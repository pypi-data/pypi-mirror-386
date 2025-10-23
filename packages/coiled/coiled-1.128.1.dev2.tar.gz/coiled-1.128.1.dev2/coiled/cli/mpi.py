import os.path
import shlex

import click
import fabric.connection

import coiled

from .. import AWSOptions
from ..v2.cluster_comms import get_cluster_connection_info, get_comm_from_connection_info
from .cluster.utils import find_cluster
from .run import KeepaliveSession, get_ssh_connection, write_via_ssh
from .utils import CONTEXT_SETTINGS


@click.command(
    context_settings=CONTEXT_SETTINGS,
)
@click.option("--worker-nodes", default=1, type=int)
@click.option(
    "--include-head/--exclude-head",
    default=True,
    type=bool,
    help="Include head (scheduler) node in placement group with EFA",
)
@click.option("--vm-type", default="g6.8xlarge", type=str)
@click.option("--head-vm-type", default=None, type=str)
@click.option("--worker-vm-type", default=None, type=str)
@click.option("--pip", multiple=True, type=str, help="Packages to install with pip")
@click.option("--apt", multiple=True, type=str, help="Packages to install with apt install")
@click.option("--setup-script", default=None, type=str, help="Path to additional host setup script")
@click.option("--cluster-timeout", default="1h", type=str, help="Maximum lifetime for cluster")
@click.option(
    "--idle-timeout",
    default="10m",
    type=str,
    help="How long to wait when nothing is running before shutting down cluster",
)
def setup(
    worker_nodes,
    include_head,
    vm_type,
    head_vm_type,
    worker_vm_type,
    pip,
    apt,
    setup_script,
    cluster_timeout,
    idle_timeout,
):
    additional_host_setup = None
    if setup_script:
        with open(setup_script) as f:
            additional_host_setup = f.read()
    setup_script = get_host_setup_script(pip_install=pip, apt_install=apt, additional_setup=additional_host_setup)

    efa_settings = (
        {"use_placement_group": True, "use_efa": True}
        if include_head
        else {"use_worker_placement_group": True, "use_worker_efa": True}
    )

    cluster = coiled.Cluster(
        n_workers=worker_nodes,
        container="daskdev/dask:latest",
        allow_ssh_from="me",
        host_setup_script=setup_script,
        backend_options=AWSOptions(**{**efa_settings, "ami_version": "DL"}),
        scheduler_vm_types=[head_vm_type or vm_type],
        worker_vm_types=[worker_vm_type or vm_type],
        worker_disk_size="100GB",
        scheduler_disk_size="100GB",
        shutdown_on_close=False,
        idle_timeout="520 weeks",  # don't use idle timeout
        cluster_timeout=cluster_timeout,
    )

    cluster.set_keepalive(keepalive=idle_timeout)

    print("Cluster created, installing software for MPI...")

    with coiled.Cloud() as cloud:
        connection = get_ssh_connection(cloud, cluster.cluster_id)

    with KeepaliveSession(cluster=cluster, prefix="mpi-ssh-setup"):
        setup_mpi_ssh(connection)

    print("MPI is ready")


@click.command(
    context_settings=CONTEXT_SETTINGS,
)
@click.option("--cluster", default=None)
@click.option("--workspace", default=None, type=str)
@click.option("--legate", is_flag=True, default=False, type=bool)
@click.option(
    "--include-head/--exclude-head",
    default=True,
    type=bool,
)
@click.argument("command", nargs=-1, required=True)
def run(cluster, workspace, legate, include_head, command):
    nodes = "$(cat workers | wc -w)"

    command = list(command)

    files = {}
    for i, c in enumerate(command):
        if os.path.exists(c):
            remote_path = f"/scratch/batch/{os.path.basename(c)}"
            command[i] = remote_path
            with open(c) as f:
                content = f.read()
            files[remote_path] = content

    if legate:
        # TODO make "--gpus 1 --sysmem 2000 --fbmem 20000" configurable
        wrapped_command = f"""
legate \
  --gpus 1 --sysmem 2000 --fbmem 20000 \
  --nodes {nodes} \
  --launcher mpirun \
  --launcher-extra ' --hostfile workers -x PATH ' \
  {shlex.join(command)}
"""
    else:
        wrapped_command = f"mpirun --hostfile workers -x PATH {shlex.join(command)}"

    with coiled.Cloud(workspace=workspace) as cloud:
        cluster_info = find_cluster(cloud, cluster)
        cluster_id = cluster_info["id"]
        connection = get_ssh_connection(cloud, cluster_id)
        address, security = get_cluster_connection_info(cluster_id, cloud)
        comms = get_comm_from_connection_info(address, security)

    setup_mpi_ssh(connection, include_scheduler=include_head)

    if files:
        worker_connections = []

        for worker in cluster_info["workers"]:
            if (
                not worker.get("instance")
                or not worker["instance"].get("current_state")
                or worker["instance"]["current_state"]["state"] != "ready"
            ):
                continue
            worker_address = worker["instance"]["private_ip_address"]

            worker_connections.append(
                fabric.connection.Connection(
                    worker_address, gateway=connection, user=connection.user, connect_kwargs=connection.connect_kwargs
                )
            )

        for path, content in files.items():
            write_via_ssh(connection, content=content, path=path)
            for conn in worker_connections:
                write_via_ssh(conn, content=content, path=path)  # , mode=0o555

    print(f"Running command:\n{wrapped_command}")

    with KeepaliveSession(cluster=None, comms=comms, prefix="mpi-ssh"):
        connection.run(wrapped_command, hide=False, pty=True, warn=True, env={"PATH": "/tmp/host-user-venv/bin:$PATH"})

    comms.close_comms()


def setup_mpi_ssh(connection, include_scheduler=True):
    add_scheduler_line = 'printf "\n127.0.0.1" >> workers' if include_scheduler else ""

    setup_mpi = f"""
/bin/coiled_agent list-worker-ips | sudo tee workers && sudo chown ubuntu workers
ssh-keyscan -f workers -t ed25519 >> ~/.ssh/known_hosts
{add_scheduler_line}

# block until host setup script has finished, at least on schedule node
until [ -f /tmp/host-setup-done ]
do
     sleep 5
done
"""

    _ = connection.run(setup_mpi, hide=True, pty=False)


def get_host_setup_script(venv_path="/tmp/host-user-venv", apt_install=None, pip_install=None, additional_setup=None):
    apt_install = list(apt_install or [])
    apt_install.extend(["openmpi-bin", "python3-pip", "python3-venv"])

    pip_install = list(pip_install or [])

    pip_install_line = f"{venv_path}/bin/python -m pip install {' '.join(pip_install)}" if pip_install else ""

    return f"""
sudo apt install {" ".join(apt_install)} -y

mkdir {venv_path}
python3 -m venv {venv_path}

{pip_install_line}
{additional_setup or ""}

echo 'done' > /tmp/host-setup-done
    """


@click.group(name="mpi", context_settings=CONTEXT_SETTINGS)
def mpi_group(): ...


mpi_group.add_command(setup)
mpi_group.add_command(run)
