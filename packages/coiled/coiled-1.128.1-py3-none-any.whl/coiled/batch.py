from __future__ import annotations

import shlex
import time

from aiohttp import ServerDisconnectedError

import coiled
from coiled.cli.curl import sync_request
from coiled.utils import dict_to_key_val_list, error_info_for_tracking


def run(
    command: list[str] | str,
    *,
    name: str | None = None,
    workspace: str | None = None,
    software: str | None = None,
    container: str | None = None,
    run_on_host: bool | None = None,
    cluster_kwargs: dict | None = None,
    env: list | dict | None = None,
    secret_env: list | dict | None = None,
    tag: list | dict | None = None,
    vm_type: list | None = None,
    scheduler_vm_type: list | None = None,
    arm: bool | None = False,
    cpu: int | str | None = None,
    memory: str | None = None,
    gpu: bool | None = False,
    region: str | None = None,
    spot_policy: str | None = None,
    allow_cross_zone: bool | None = None,
    disk_size: str | None = None,
    allow_ssh_from: str | None = None,
    ntasks: int | None = None,
    task_on_scheduler: bool | None = None,
    array: str | None = None,
    scheduler_task_array: str | None = None,
    map_over_values: list[str] | None = None,
    map_over_file: str | None = None,
    map_over_input_var: str | None = None,
    map_over_task_var_dicts: list[dict[str, str]] | None = None,
    map_over_delimiter: str | None = None,
    max_workers: int | None = None,
    wait_for_ready_cluster: bool | None = None,
    forward_aws_credentials: bool | None = None,
    package_sync_strict: bool = False,
    package_sync_conda_extras: list | None = None,
    package_sync_ignore: list[str] | None = None,
    local_upload_path: str | None = None,
    buffers_to_upload: list[dict] | None = None,
    host_setup_script: str | None = None,
    host_setup_script_content: str | None = None,
    command_as_script: bool | None = None,
    ignore_container_entrypoint: bool | None = None,
    job_timeout: str | None = None,
    logger=None,
) -> dict:
    """Submit a batch job to run on Coiled.

    See ``coiled batch run --help`` for documentation.

    Additional Parameters
    ---------------------
    map_over_task_var_dicts
        takes a list of dictionaries, so you can specify multiple environment variables for each task.
        For example, ``[{"FOO": 1, "BAR": 2}, {"FOO": 3, "BAR": 4}]`` will pass ``FOO=1 BAR=2`` to one task and
        ``FOO=3 BAR=4`` to another.
    buffers_to_upload
        takes a list of dictionaries, each should have path where file should be written on VM(s)
        relative to working directory, and ``io.BytesIO`` which provides content of file,
        for example ``[{"relative_path": "hello.txt", "buffer": io.BytesIO(b"hello")}]``.
    """
    if isinstance(command, str) and not command.startswith("#!") and not command_as_script:
        command = shlex.split(command)

    env = dict_to_key_val_list(env)
    secret_env = dict_to_key_val_list(secret_env)
    tag = dict_to_key_val_list(tag)
    vm_type = [vm_type] if isinstance(vm_type, str) else vm_type

    kwargs = dict(
        name=name,
        command=command,
        workspace=workspace,
        software=software,
        container=container,
        run_on_host=run_on_host,
        cluster_kwargs=cluster_kwargs,
        env=env,
        secret_env=secret_env,
        tag=tag,
        vm_type=vm_type,
        scheduler_vm_type=scheduler_vm_type,
        arm=arm,
        cpu=cpu,
        memory=memory,
        gpu=gpu,
        region=region,
        spot_policy=spot_policy,
        allow_cross_zone=allow_cross_zone,
        disk_size=disk_size,
        allow_ssh_from=allow_ssh_from,
        ntasks=ntasks,
        task_on_scheduler=task_on_scheduler,
        array=array,
        scheduler_task_array=scheduler_task_array,
        # for CLI, map_over_values is a single string that needs to be split
        map_over_split_values=map_over_values,
        map_over_file=map_over_file,
        map_over_input_var=map_over_input_var,
        map_over_delimiter=map_over_delimiter,
        map_over_task_var_dicts=map_over_task_var_dicts,  # not exposed in CLI
        max_workers=max_workers,
        wait_for_ready_cluster=wait_for_ready_cluster,
        forward_aws_credentials=forward_aws_credentials,
        package_sync_strict=package_sync_strict,
        package_sync_conda_extras=package_sync_conda_extras,
        package_sync_ignore=package_sync_ignore,
        local_upload_path=local_upload_path,
        buffers_to_upload=buffers_to_upload,
        host_setup_script=host_setup_script,
        host_setup_script_content=host_setup_script_content,
        command_as_script=command_as_script,
        ignore_container_entrypoint=ignore_container_entrypoint,
        job_timeout=job_timeout,
        logger=logger,
    )

    # avoid circular imports
    from coiled.cli.batch.run import _batch_run, batch_run_cli

    # {kwarg: default value} dict, taken from defaults on the CLI
    cli_defaults = {param.name: param.default for param in batch_run_cli.params}

    # this function uses `None` as the default
    # we want to both (1) track which kwargs are the default and (2) replace with default from CLI
    default_kwargs = {key: cli_defaults[key] for key, val in kwargs.items() if val is None and key in cli_defaults}
    kwargs = {
        **kwargs,
        **default_kwargs,
    }

    success = True
    exception = None
    try:
        return _batch_run(default_kwargs, **kwargs)
    except Exception as e:
        success = False
        exception = e
        raise
    finally:
        coiled.add_interaction(
            "coiled-batch-python",
            success=success,
            **error_info_for_tracking(exception),
        )


def wait_for_job_done(job_id: int, timeout: int | None = None) -> str | None:
    timeout_at = time.monotonic() + timeout if timeout is not None else None
    with coiled.Cloud() as cloud:
        url = f"{cloud.server}/api/v2/jobs/{job_id}"
        while timeout_at is None or time.monotonic() < timeout_at:
            try:
                response = sync_request(cloud, url, "get", data=None, json_output=True)
            except ServerDisconnectedError:
                continue
            state = response.get("state")
            if state and "done" in state:
                return state
            time.sleep(5)
    # if we timed out waiting for job to finish
    return None


def status(
    cluster: str | int = "",
    workspace: str | None = None,
) -> list[dict]:
    """Check the status of a Coiled Batch job.

    See ``coiled batch status --help`` for documentation.
    """
    # avoid circular imports
    from coiled.cli.batch.status import get_job_status

    return get_job_status(cluster=cluster, workspace=workspace)[0]


def list_jobs(
    workspace: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """List Coiled Batch jobs in a workspace.

    See ``coiled batch list --help`` for documentation.
    """
    # avoid circular imports
    from coiled.cli.batch.list import get_job_list

    return get_job_list(workspace=workspace, limit=limit)
