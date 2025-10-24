from __future__ import annotations

import asyncio
import functools
import json
import os
import platform
import re
import shutil
import subprocess
import warnings
from base64 import b64decode
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from logging import getLogger
from pathlib import Path
from sys import executable
from threading import Lock
from typing import Dict, List, TextIO, Tuple, Union, cast
from urllib.parse import unquote, urlparse

import dask.config
import toml
from dask.utils import parse_timedelta
from filelock import BaseFileLock, FileLock
from packaging.utils import parse_wheel_filename
from rich.progress import Progress
from typing_extensions import Literal
from urllib3.util import Url, parse_url

from coiled.context import track_context
from coiled.types import PackageInfo, PackageLevelEnum, ResolvedPackageInfo
from coiled.utils import (
    TemporaryDirectory,
    get_encoding,
    get_temp_dir,
    partition,
    recurse_importable_python_files,
    safe_path_resolve,
    validate_wheel,
)
from coiled.v2.widgets.util import simple_progress

try:
    import keyring  # type: ignore[reportMissingImports]

    HAVE_KEYRING = True
except Exception:
    HAVE_KEYRING = False


logger = getLogger("coiled.software_utils")
subdir_datas = {}

ANY_AVAILABLE = "ANY-AVAILABLE"
AUTH_BEARER_USERNAME = "AUTH_BEARER_TOKEN"
CONDA_TOKEN_USERNAME = "CONDA_TOKEN"
COILED_LOCAL_PACKAGE_PREFIX = "coiled_local_"
DEFAULT_JSON_PYPI_URL = "https://pypi.org/pypi"
DEFAULT_PYPI_URL = "https://pypi.org/simple"
LOCK_PATH = Path(os.path.expanduser("~")) / ".coiled" / "locks"
PYTHON_VERSION = platform.python_version_tuple()


async def create_subprocess_exec(
    program: str,
    *args: str,
    stdout: Union[TextIO, int, None] = None,
    stderr: Union[TextIO, int, None] = None,
    extra_env: Dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    # create_subprocess_exec is broken with IPython on Windows,
    # because it uses the wrong event loop
    loop = asyncio.get_running_loop()
    env = {**os.environ, **(extra_env or {})}
    result = loop.run_in_executor(
        None, lambda: subprocess.run([program, *args], stdout=stdout, stderr=stderr, close_fds=True, env=env)
    )
    return await result


def partition_ignored_packages(
    packages: List[PackageInfo], priorities: Dict[Tuple[str, Literal["conda", "pip"]], PackageLevelEnum]
) -> Tuple[List[PackageInfo], List[PackageInfo]]:
    return partition(
        packages,
        lambda pkg: priorities.get((pkg["name"], pkg["source"])) == PackageLevelEnum.IGNORE,
    )


def partition_local_python_code_packages(packages: List[PackageInfo]) -> Tuple[List[PackageInfo], List[PackageInfo]]:
    return partition(
        packages,
        lambda pkg: (
            pkg["name"].startswith(COILED_LOCAL_PACKAGE_PREFIX) and not cast(str, pkg["wheel_target"]).endswith(".whl")
        ),
    )


def partition_local_packages(packages: List[PackageInfo]) -> Tuple[List[PackageInfo], List[PackageInfo]]:
    return partition(
        packages,
        lambda pkg: bool(pkg["wheel_target"]),
    )


WHEEL_BUILD_LOCKS: Dict[str, Tuple[BaseFileLock, Lock, TemporaryDirectory]] = {}


# filelock is thread local
# so we have to ensure the lock is acquired/released
# on the same thread
FILE_LOCK_POOL = ThreadPoolExecutor(max_workers=1)
THREAD_LOCK_POOL = ThreadPoolExecutor(max_workers=1)


@asynccontextmanager
async def async_lock(file_lock: BaseFileLock, thread_lock: Lock):
    # Beware, there are some complicated details to this locking implementation!
    # We're trying to manage the weirdness of the file lock mostly.
    loop = asyncio.get_running_loop()
    # first acquire a thread lock
    await loop.run_in_executor(THREAD_LOCK_POOL, thread_lock.acquire)
    # acquire the file lock, we should be the only thread trying to get it
    # the threadpool is required to release it, so another thread
    # attempting to get the lock will deadlock things by preventing the
    # release!
    await loop.run_in_executor(FILE_LOCK_POOL, file_lock.acquire)
    yield
    # release the file lock first
    await loop.run_in_executor(FILE_LOCK_POOL, file_lock.release)
    # now release the thread lock, allowing another thread to proceed
    # and get the file lock
    thread_lock.release()


@track_context
async def create_wheel(pkg_name: str, version: str, src: str) -> ResolvedPackageInfo:
    # These locks are set up such that
    # Threads: Block on each other and check if another thread already built the wheel
    # Processes: Block on each other, but will not reuse a wheel created by another
    # `pip wheel` is never run on the same package at the same time
    LOCK_PATH.mkdir(parents=True, exist_ok=True)  # ensure lockfile directory exists
    package_lock, thread_lock, tmpdir = WHEEL_BUILD_LOCKS.setdefault(
        pkg_name,
        (
            FileLock(LOCK_PATH / ("." + pkg_name + version + ".build-lock")),
            Lock(),
            get_temp_dir(ignore_cleanup_errors=True),
        ),
    )
    async with async_lock(package_lock, thread_lock):
        outdir = Path(tmpdir.name) / Path(pkg_name)
        if outdir.exists():
            logger.debug(f"Checking for existing wheel for {pkg_name} @ {outdir}")
            wheel_fn = next((file for file in outdir.iterdir() if file.suffix == ".whl"), None)
        else:
            wheel_fn = None
        if not wheel_fn:
            logger.debug(f"No existing wheel, creating a wheel for {pkg_name} @ {src}")
            # must use executable to avoid using some other random python
            proc = await create_subprocess_exec(
                executable,
                "-m",
                "pip",
                "wheel",
                "--wheel-dir",
                str(outdir),
                "--no-deps",
                "--use-pep517",
                "--no-cache-dir",
                src,
                stderr=subprocess.STDOUT,
                stdout=subprocess.PIPE,
                extra_env={"PIP_REQUIRE_VIRTUALENV": "false"},
            )
            if proc.returncode:
                print(f"---Wheel Build Log for {pkg_name}---\n" + proc.stdout.decode(encoding=get_encoding()))
                return {
                    "name": pkg_name,
                    "source": "pip",
                    "channel": None,
                    "conda_name": None,
                    "client_version": version,
                    "specifier": "",
                    "include": False,
                    "error": (
                        "Failed to build a wheel for the"
                        " package, will not be included in environment, check stdout for the build log"
                    ),
                    "note": None,
                    "sdist": None,
                    "md5": None,
                }
            wheel_fn = next(file for file in outdir.iterdir() if file.suffix == ".whl")
        logger.debug(f"Using wheel @ {wheel_fn}")
        _, build_version, _, _ = parse_wheel_filename(str(wheel_fn.name))
        has_python, md5, missing_py_files = await validate_wheel(wheel_fn, src)
    return {
        "name": pkg_name,
        "source": "pip",
        "channel": None,
        "conda_name": None,
        "client_version": str(build_version),
        "specifier": "",
        "include": True,
        "error": None if has_python else "Built wheel contains no python files!",
        "note": (
            f"Wheel built from {src}"
            + (f" is missing {', '.join(sorted(missing_py_files)[:10])}" if missing_py_files else "")
        ),
        "sdist": wheel_fn.open("rb"),
        "md5": md5,
    }


@track_context
async def create_wheel_from_egg(pkg_name: str, version: str, src: str) -> ResolvedPackageInfo:
    warnings.warn(
        "Converting eggs to wheels is deprecated, please use wheel-based packages instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    tmpdir = get_temp_dir(ignore_cleanup_errors=True)
    outdir = Path(tmpdir.name) / Path(pkg_name)
    outdir.mkdir(parents=True)
    logger.debug(f"Attempting to create a wheel for {pkg_name} in directory {src}")
    # must use executable to avoid using some other random python
    proc = await create_subprocess_exec(
        executable,
        "-m",
        "wheel",
        "convert",
        "--dest-dir",
        str(outdir),
        src,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        extra_env={"PIP_REQUIRE_VIRTUALENV": "false"},
    )
    if proc.returncode:
        print(f"---Egg to wheel conversion Log for {pkg_name}---\n" + proc.stdout.decode(encoding=get_encoding()))
        return {
            "name": pkg_name,
            "source": "pip",
            "channel": None,
            "conda_name": None,
            "client_version": version,
            "specifier": "",
            "include": False,
            "error": (
                "Failed to convert the package egg to a wheel"
                ", will not be included in environment, check stdout for egg conversion log"
            ),
            "note": None,
            "sdist": None,
            "md5": None,
        }
    wheel_fn = next(file for file in outdir.iterdir() if file.suffix == ".whl")
    has_python, md5, missing_py_files = await validate_wheel(Path(wheel_fn), tmpdir.name)
    return {
        "name": pkg_name,
        "source": "pip",
        "channel": None,
        "conda_name": None,
        "client_version": version,
        "specifier": "",
        "include": True,
        "error": None if has_python else "Built wheel has no python files!",
        "note": (
            "Wheel built from local egg"
            + (f" is missing {', '.join(sorted(missing_py_files)[:10])}" if missing_py_files else "")
        ),
        "sdist": wheel_fn.open("rb"),
        "md5": md5,
    }


@track_context
async def create_wheel_from_src_dir(pkg_name: str, version: str, src: str) -> ResolvedPackageInfo:
    # These locks are set up such that
    # Threads: Block on each other and check if another thread already built the tarball
    # Processes: Block on each other, but will not reuse a tarball created by another
    md5 = None
    LOCK_PATH.mkdir(parents=True, exist_ok=True)  # ensure lockfile directory exists
    package_lock, thread_lock, tmpdir = WHEEL_BUILD_LOCKS.setdefault(
        pkg_name,
        (
            FileLock(LOCK_PATH / (f".{pkg_name}{version}.build-lock")),
            Lock(),
            get_temp_dir(ignore_cleanup_errors=True),
        ),
    )
    async with async_lock(package_lock, thread_lock):
        outdir = Path(tmpdir.name) / Path(pkg_name)
        if outdir.exists():
            logger.debug(f"Checking for existing source archive for {pkg_name} @ {outdir}")
            wheel_fn = next((file for file in outdir.iterdir() if file.suffix == ".whl"), None)
        else:
            wheel_fn = None
        if not wheel_fn:
            logger.debug(f"No existing source archive, creating an archive for {pkg_name} @ {src}")
            try:
                unpacked_dir = outdir / f"{pkg_name}-{version}"
                # Create fake metadata to make wheel work
                dist_info_dir = unpacked_dir / f"{unpacked_dir.name}.dist-info"
                dist_info_dir.mkdir(parents=True)
                with open(dist_info_dir / "METADATA", "w") as f:
                    f.write(f"Metadata-Version: 2.1\nName: {pkg_name}\nVersion: {version}\n")
                with open(dist_info_dir / "WHEEL", "w") as f:
                    f.write("Wheel-Version: 1.0\nGenerator: coiled\nRoot-Is-Purelib: true\nTag: py3-none-any\n")
                src_path = Path(src)
                for file in recurse_importable_python_files(src_path):
                    if str(file) in ("__init__.py", "__main__.py"):
                        continue
                    dest = unpacked_dir / file
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(src_path / file, dest)
                proc = await create_subprocess_exec(
                    executable,
                    "-m",
                    "wheel",
                    "pack",
                    "--dest-dir",
                    str(outdir),
                    str(unpacked_dir),
                    stderr=subprocess.STDOUT,
                    stdout=subprocess.PIPE,
                    extra_env={"PIP_REQUIRE_VIRTUALENV": "false"},
                )
                if proc.returncode:
                    print(f"---wheel packing log for {src}---\n" + proc.stdout.decode(encoding=get_encoding()))
                    return {
                        "name": pkg_name,
                        "source": "pip",
                        "channel": None,
                        "conda_name": None,
                        "client_version": version,
                        "specifier": "",
                        "include": False,
                        "error": (
                            "Failed to build a package of your local python files. Please check stdout for details"
                        ),
                        "note": None,
                        "sdist": None,
                        "md5": None,
                    }
            except IOError as e:
                return {
                    "name": pkg_name,
                    "source": "pip",
                    "channel": None,
                    "conda_name": None,
                    "client_version": version,
                    "specifier": "",
                    "include": False,
                    "error": f"Failed to build a package of your local python files. Exception: {e}",
                    "note": None,
                    "sdist": None,
                    "md5": None,
                }
            wheel_fn = next(file for file in outdir.iterdir() if file.suffix == ".whl")
        logger.debug(f"Using wheel @ {wheel_fn}")
        _, build_version, _, _ = parse_wheel_filename(str(wheel_fn.name))
        has_python, md5, missing_py_files = await validate_wheel(wheel_fn, src)
    return {
        "name": pkg_name,
        "source": "pip",
        "channel": None,
        "conda_name": None,
        "client_version": str(build_version),
        "specifier": "",
        "include": True,
        "error": None if has_python else "Built wheel does not contain all python files!",
        "note": (
            f"Source wheel built from {src}"
            + (f" is missing {', '.join(sorted(missing_py_files)[:10])}" if missing_py_files else "")
        ),
        "sdist": wheel_fn.open("rb"),
        "md5": md5,
    }


async def create_wheels_for_local_python(packages: List[PackageInfo], progress: Progress | None = None):
    finalized_packages: list[ResolvedPackageInfo] = []
    home_dir = str(Path.home())
    for pkg in packages:
        if pkg["wheel_target"]:
            with simple_progress(
                f"Creating wheel for {pkg['wheel_target'].replace(home_dir, '~', 1)}", progress=progress
            ):
                fut = create_wheel_from_src_dir(
                    pkg_name=pkg["name"],
                    version=pkg["version"],
                    src=pkg["wheel_target"],
                )
                wheel_timeout = parse_timedelta(dask.config.get("coiled.wheel-creation-timeout", "1m"))
                try:
                    result = await asyncio.wait_for(fut, timeout=wheel_timeout)
                except TimeoutError:
                    raise TimeoutError(
                        f"Creating wheel for '{pkg['name']}' package timed out after {wheel_timeout} seconds.\n"
                        "Please retry (this often works), or if you want to increase timeout you can run:\n"
                        "  coiled config set coiled.wheel-creation-timeout 2m\n"
                        "(or another timeout value)."
                    ) from None
                finalized_packages.append(result)
    return finalized_packages


async def create_wheels_for_packages(
    packages: List[PackageInfo],
    progress: Progress | None = None,
):
    finalized_packages: list[ResolvedPackageInfo] = []
    for pkg in packages:
        if pkg["wheel_target"]:
            # TODO: Remove this once we stop supporting eggs entirely
            if pkg["wheel_target"].endswith(".egg"):
                with simple_progress(f"Creating wheel from egg for {pkg['name']}", progress=progress):
                    finalized_packages.append(
                        await create_wheel_from_egg(
                            pkg_name=pkg["name"],
                            version=pkg["version"],
                            src=pkg["wheel_target"],
                        )
                    )
            else:
                with simple_progress(f"Creating wheel for {pkg['name']}", progress=progress):
                    fut = create_wheel(
                        pkg_name=pkg["name"],
                        version=pkg["version"],
                        src=pkg["wheel_target"],
                    )
                    wheel_timeout = parse_timedelta(dask.config.get("coiled.wheel-creation-timeout", "1m"))
                    try:
                        result = await asyncio.wait_for(fut, timeout=wheel_timeout)
                    except TimeoutError:
                        raise TimeoutError(
                            f"Creating wheel for '{pkg['name']}' package timed out after {wheel_timeout} seconds.\n"
                            "Please retry (this often works), or if you want to increase timeout you can run:\n"
                            "  coiled config set coiled.wheel-creation-timeout 2m\n"
                            "(or another timeout value)."
                        ) from None
                    finalized_packages.append(result)
    return finalized_packages


pip_bad_req_regex = (
    r"(?P<package>.+) (?P<version>.+) has requirement "
    r"(?P<requirement>.+), but you have (?P<requirement2>.+) (?P<reqversion>.+)\."
)


@track_context
async def check_pip_happy(progress: Progress | None = None) -> Dict[str, List[str]]:
    with simple_progress("Running pip check", progress=progress):
        proc = await create_subprocess_exec(
            executable,
            "-m",
            "pip",
            "check",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            extra_env={"PIP_REQUIRE_VIRTUALENV": "false"},
        )
        faulty_packages = defaultdict(list)
        if proc.returncode:
            output = proc.stdout.decode(encoding=get_encoding())
            bad_reqs = re.finditer(pip_bad_req_regex, output)
            for bad_req in bad_reqs:
                groups = bad_req.groupdict()
                span = bad_req.span()
                warning = output[span[0] : span[1]]
                faulty_packages[groups["package"]].append(warning)
        return faulty_packages


def _load_toml(path: Union[Path, str]) -> Dict:
    path = Path(path)
    filename = path.name
    dir_path = safe_path_resolve(path.parent)
    toml_dict = {}
    # Walk up the directory tree to find the first toml file (up to 10 levels above)
    for _ in range(10):
        path = dir_path / filename
        if not path.exists():
            if dir_path == dir_path.parent:
                break
            dir_path = dir_path.parent
            continue
        try:
            with path.open() as f:
                toml_dict = toml.load(f)
        except (toml.TomlDecodeError, FileNotFoundError, IndexError) as e:
            logger.debug(f"Failed to load {path}: {e}", exc_info=True)
        break
    return toml_dict


def _get_pip_index_urls() -> List[str]:
    """Returns the index URLs from `pip config list` as a list of strings."""
    encoding = get_encoding()

    index_url = DEFAULT_PYPI_URL
    extra_index_urls = []

    # Check pip config first
    try:
        config_output = subprocess.check_output(
            [
                executable,
                "-m",
                "pip",
                "--no-input",
                "config",
                "list",
            ],
            encoding=encoding,
            env={**os.environ, "PIP_REQUIRE_VIRTUALENV": "false"},
        )
        for line in config_output.splitlines():
            if ".index-url" in line:
                index_url = line.split("=", 1)[1].strip("' \n\"")
            if ".extra-index-url" in line:
                extra_index_urls.append(line.split("=", 1)[1].strip("' \n\""))

    except Exception:
        pass

    # Load pyproject.toml to check other tool configs
    pyproject = _load_toml("pyproject.toml")
    tool_dict = pyproject.get("tool", {})

    # poetry
    poetry_sources = tool_dict.get("poetry", {}).get("source", [])
    for source in poetry_sources:
        if source_url := source.get("url"):
            extra_index_urls.append(source_url)
    # uv
    uv_conf = {**tool_dict.get("uv", {}), **_load_toml("uv.toml")}.get("pip", {})
    index_url = uv_conf.get("index-url") or index_url

    uv_raw_extras = uv_conf.get("extra-index-url")
    uv_extra_index_urls = (uv_raw_extras.split() if isinstance(uv_raw_extras, str) else uv_raw_extras) or []
    extra_index_urls.extend(uv_extra_index_urls)

    # pixi
    pixi_conf = {**tool_dict.get("pixi", {}), **_load_toml("pixi.toml")}.get("pypi-options", {})
    index_url = pixi_conf.get("index-url") or index_url
    extra_index_urls.extend(pixi_conf.get("extra-index-urls", []))

    # Environment variables take precedence over config files
    # See https://pip.pypa.io/en/stable/topics/configuration/#precedence-override-order
    extra_index_urls.extend(os.environ.get("PIP_EXTRA_INDEX_URL", "").split())
    extra_index_urls.extend(os.environ.get("UV_EXTRA_INDEX_URL", "").split())
    index_url = os.environ.get("PIP_INDEX_URL", os.environ.get("PIP_PYPI_URL", index_url))
    index_url = os.environ.get("UV_INDEX_URL", index_url)

    extra_index_urls = sorted(set(extra_index_urls) - {index_url})

    return [url.strip() for url in [index_url, *extra_index_urls]]


@functools.lru_cache
def get_mamba_auth_dict(home_dir: Path | None = None) -> dict[str, tuple[str, str]]:
    if home_dir is None:
        home_dir = Path.home()
    auth_file = home_dir / ".mamba" / "auth" / "authentication.json"
    domain_auth = {}
    if auth_file.exists():
        with auth_file.open("r") as f:
            auth_data = json.load(f)
            for domain, auth in auth_data.items():
                auth_type = auth.get("type")
                if auth_type == "CondaToken":
                    domain_auth[domain] = (CONDA_TOKEN_USERNAME, auth["token"])
                elif auth_type == "BearerToken":
                    domain_auth[domain] = (AUTH_BEARER_USERNAME, auth["token"])
                elif auth_type == "BasicHTTPAuthentication":
                    domain_auth[domain] = (
                        auth.get("user") or "",
                        # Mamba stores passwords as base64 encoded strings
                        b64decode(auth.get("password") or "").decode("utf-8"),
                    )
                else:
                    logger.debug(f"Encountered unknown mamba auth type {auth_type} for domain {domain}")
    return domain_auth


def get_mamba_auth(netloc: str) -> tuple[str, str] | None:
    """Returns the Requests tuple auth for a given domain from the mamba auth file."""
    # mamba uses the domain as the key
    return get_mamba_auth_dict().get(netloc, None)


def _parse_rattler_auth_data(auth_data: dict) -> tuple[str, str] | None:
    """Parse rattler authentication data into username/password tuple.

    Handles rattler Authentication variants:
    - {"BearerToken": "token"}
    - {"CondaToken": "token"}
    - {"BasicHTTP": {"username": "user", "password": "pass"}}

    Returns:
        Tuple of (username, password) or None if unknown auth type
    """
    if "BearerToken" in auth_data:
        return (AUTH_BEARER_USERNAME, auth_data["BearerToken"])
    elif "CondaToken" in auth_data:
        return (CONDA_TOKEN_USERNAME, auth_data["CondaToken"])
    elif "BasicHTTP" in auth_data:
        basic_auth = auth_data["BasicHTTP"]
        return (
            basic_auth.get("username", ""),
            basic_auth.get("password", ""),
        )
    else:
        return None


@functools.lru_cache
def get_rattler_auth_dict(home_dir: Path | None = None) -> dict[str, tuple[str, str]]:
    # RATTLER_AUTH_FILE is an env var that can override the default location
    env_auth_file = os.environ.get("RATTLER_AUTH_FILE")
    if env_auth_file:
        auth_file = Path(env_auth_file)
    else:
        if home_dir is None:
            home_dir = Path.home()
        auth_file = home_dir / ".rattler" / "credentials.json"
    domain_auth = {}
    if auth_file.exists():
        with auth_file.open("r") as f:
            auth_data = json.load(f)
            for domain, auth in auth_data.items():
                parsed_auth = _parse_rattler_auth_data(auth)
                if parsed_auth:
                    domain_auth[domain] = parsed_auth
                else:
                    logger.debug(f"Encountered unknown rattler auth type {list(auth.keys())} for domain {domain}")
    return domain_auth


def get_rattler_keyring_auth(netloc: str) -> tuple[str, str] | None:
    """Returns the Requests tuple auth for a given domain from rattler keyring storage."""
    if not HAVE_KEYRING:
        logger.debug("keyring not available, skipping rattler keyring auth")
        return None

    def try_keyring_auth(host: str) -> tuple[str, str] | None:
        """Try to get auth from keyring for a specific host using rattler's storage format."""
        try:
            # Use the existing get_keyring_auth function with "rattler" as the URL
            # and the host as the username to get rattler-stored credentials
            auth_parts = get_keyring_auth("rattler", host)
            if auth_parts:
                username, password = auth_parts
                if password:
                    try:
                        auth_data = json.loads(password)
                        parsed_auth = _parse_rattler_auth_data(auth_data)
                        if parsed_auth:
                            return parsed_auth
                    except json.JSONDecodeError:
                        # If it's not JSON, treat it as a simple username/password
                        return (username or host, password)

        except Exception as e:
            logger.debug(f"Error getting rattler keyring auth for {host}: {e}")
            return None

        return None

    # Try exact match first
    auth_parts = try_keyring_auth(netloc)
    if auth_parts:
        logger.debug(f"Found rattler keyring auth for {netloc}")
        return auth_parts

    # Try parent domain matches if exact match failed
    # If looking for foo.example.com, try example.com (but not com)
    parts = netloc.split(".")
    for i in range(1, len(parts) - 1):  # Stop before single TLD
        parent_domain = ".".join(parts[i:])

        auth_parts = try_keyring_auth(parent_domain)
        if auth_parts:
            logger.debug(f"Found rattler keyring auth for {parent_domain} (matching {netloc})")
            return auth_parts

    logger.debug(f"No rattler keyring auth found for {netloc}")
    return None


def get_rattler_auth(netloc: str) -> tuple[str, str] | None:
    """Returns the Requests tuple auth for a given domain from rattler keyring or auth file."""
    # Try keyring first (primary storage method for rattler/pixi)
    auth_parts = get_rattler_keyring_auth(netloc)
    if auth_parts:
        return auth_parts

    # Fall back to file-based storage
    # rattler allows wildcards, so we have to check for exact matches first
    auth_parts = get_rattler_auth_dict().get(netloc, None)
    if auth_parts:
        return auth_parts

    # then check for wildcard matches in file storage
    for domain, auth in get_rattler_auth_dict().items():
        if domain.startswith("*.") and netloc.endswith(domain[1:]):
            return auth

    return None


@functools.lru_cache
def get_conda_config() -> dict:
    """Returns the current conda config as dictionary"""
    encoding = get_encoding()
    conda_config = {}
    try:
        config_output = subprocess.check_output(
            [
                "conda",
                "config",
                "--show",
                "--json",
            ],
            encoding=encoding,
        )
        conda_config = json.loads(config_output)
    except Exception:
        logger.debug("Encountered error when loading conda config", exc_info=True)

    return conda_config


def get_conda_python_path() -> Path | None:
    """Returns the path the conda base environment python executable"""
    # Try using config first, since that's probably the most cross-platform way
    conda_config = get_conda_config()
    root_prefix = conda_config.get("root_prefix")
    if root_prefix:
        conda_python = Path(root_prefix) / "bin" / "python"
        if conda_python.exists():
            return conda_python
    # Fallback to the conda executable
    conda_executable = shutil.which("conda")
    if conda_executable:
        conda_executable = Path(conda_executable)
        conda_python = conda_executable.parent / "python"
        if conda_python.exists():
            return conda_python
    return None


def get_conda_auth(no_auth_url: str) -> tuple[str, str] | None:
    """Returns the Requests tuple auth for a given domain from its conda-auth values."""
    conda_config = get_conda_config()
    channel_settings = conda_config.get("channel_settings", [])
    auth_type = None
    username = None
    password = None
    for channel in channel_settings:
        if channel.get("channel") != no_auth_url:
            continue
        auth_type = channel.get("auth")
        if not auth_type:
            continue
        if auth_type == "http-basic":
            username = channel.get("username")
            password = channel.get("password")
        elif auth_type == "token":
            username = "token"
            password = channel.get("token")

    if not auth_type or not username:
        return None
    if not password:
        # Use base environment python to get the keyring,
        # so we don't prompt for a password and know keyring is available
        conda_python = get_conda_python_path()
        if conda_python:
            # This is kind of a hack, but using multiprocessing with a
            # different python executable lends itself to pickling issues
            python_code = f"""
import json
import sys
try:
    import keyring
except Exception as e:
    sys.exit(0)

username = {username!r}
url = "conda-auth::{auth_type}::{no_auth_url}"
auth_parts = None

if hasattr(keyring, "get_credential"):
    cred = keyring.get_credential(url, username)
    if cred is not None:
        auth_parts = cred.username, cred.password

if username is not None:
    password = keyring.get_password(url, username)
    if password:
        auth_parts = username, password

print(json.dumps(auth_parts))
"""
            try:
                auth_parts_str = subprocess.check_output(
                    [str(conda_python), "-c", python_code],
                    encoding=get_encoding(),
                    timeout=5,
                ).strip()
                if auth_parts_str and auth_parts_str != "null":
                    auth_parts = json.loads(auth_parts_str)
                    if auth_parts:
                        username, password = auth_parts
                else:
                    logger.debug(f"Keyring returned no credentials for conda-auth::{auth_type}::{no_auth_url}")
            except subprocess.TimeoutExpired:
                logger.warning("Timed out getting conda-auth keyring creds")
                return None
            except Exception as e:
                logger.warning(f"Unexpected error getting keyring auth: {e}", exc_info=True)
                return None

    if auth_type == "token":
        username = CONDA_TOKEN_USERNAME

    if not username and not password:
        return None

    return (username or "", password or "")


@functools.lru_cache
def set_auth_for_url(url: Url | str) -> str:
    """Returns a url string with the user and password set from netrc, keyring, mamba, or the URL itself."""
    if isinstance(url, str):
        try:
            parsed_url = parse_url(url)
        except Exception:
            # If the URL is not valid, we just return it as is
            logger.warning(f"Failed to parse URL: {url}")
            return url
    else:
        parsed_url = url
    username = None
    password = None
    if parsed_url.auth:
        # parse_url quotes the auth part, so we need to unquote it
        auth_parts = unquote(parsed_url.auth).split(":", 1)
        if len(auth_parts) < 2:
            auth_parts += [None]
        username, password = auth_parts

    path = parsed_url.path or ""
    netloc = parsed_url.netloc or ""

    if not password:
        use_netrc = dask.config.get("coiled.package_sync.conda.cred_sources.netrc", True)
        use_keyring = dask.config.get("coiled.package_sync.conda.cred_sources.keyring", True)
        use_conda_auth = dask.config.get("coiled.package_sync.conda.cred_sources.conda", True)
        use_mamba_auth = dask.config.get("coiled.package_sync.conda.cred_sources.mamba", True)
        use_rattler_auth = dask.config.get("coiled.package_sync.conda.cred_sources.rattler", True)

        no_auth_url = parsed_url._replace(auth=None).url
        auth_parts = (
            # get_netrc_auth takes a URL, but only uses the netloc part
            (get_netrc_auth(no_auth_url) if use_netrc else None)
            # keyring could have URL stored by full URL or netloc
            or (
                (get_keyring_auth(no_auth_url, username) or get_keyring_auth(netloc, username)) if use_keyring else None
            )
            # conda-auth stores things in keyring in its own format
            or (get_conda_auth(no_auth_url) if use_conda_auth else None)
            # mamba could have URL stored by netloc/path or netloc
            or ((get_mamba_auth(f"{netloc}{path}") or get_mamba_auth(netloc)) if use_mamba_auth else None)
            # rattler/pixi stores URL stored by netloc in keyring or a fallback file
            or (get_rattler_auth(netloc) if use_rattler_auth else None)
        )
        if auth_parts is not None:
            username, password = auth_parts
        if username == CONDA_TOKEN_USERNAME:
            # If the username indicates this is a token (which only happens for mamba auth)
            # the token should be embedded directly in the URL and not in the auth portion

            if not password:
                logger.warning(f"No token found for {parsed_url.url}")
            # If the path has `/t//`, it's missing the token, so add it
            elif path.startswith("/t//"):
                parsed_url = parsed_url._replace(path=f"/t/{password}{path[3:]}")
            # If the path doesn't have `/t/` at all, add it
            elif not path.startswith("/t/"):
                parsed_url = parsed_url._replace(path=f"/t/{password}{path}")
            parsed_url = parsed_url._replace(auth=None)
        elif username or password:
            parsed_url = parsed_url._replace(auth=f"{username or ''}:{password or ''}")

        if username and username != CONDA_TOKEN_USERNAME and not password:
            if username == AUTH_BEARER_USERNAME:
                logger.warning(f"No bearer token found for {parsed_url.url}")
            else:
                logger.info(f"No password found for {parsed_url.url}")
        elif not username:
            logger.info(f"No username or password found for {parsed_url.url}")

    return parsed_url.url


### Code below here was copied from requests.utils to avoid a dependency on requests
NETRC_FILES = (".netrc", "_netrc")


def get_netrc_auth(url: str, raise_errors=False) -> tuple[str | None, str | None] | None:
    """Returns the Requests tuple auth for a given url from netrc."""

    # If dask config is set, then the default netrc locations won't be used at all, but env var
    # takes precedence over dask config if both are set.
    netrc_file = os.environ.get("NETRC") or dask.config.get("coiled.package_sync.conda.netrc_path", None)
    if netrc_file is not None:
        netrc_locations = (netrc_file,)
    else:
        netrc_locations = (f"~/{f}" for f in NETRC_FILES)

    try:
        from netrc import NetrcParseError, netrc

        netrc_path = None

        for f in netrc_locations:
            try:
                loc = os.path.expanduser(f)
            except KeyError:
                # os.path.expanduser can fail when $HOME is undefined and
                # getpwuid fails. See https://bugs.python.org/issue20164 &
                # https://github.com/psf/requests/issues/1846
                return

            if os.path.exists(loc):
                netrc_path = loc
                break

        # Abort early if there isn't one.
        if netrc_path is None:
            return

        ri = urlparse(url)

        host = ri.netloc.split(":")[0]

        try:
            _netrc = netrc(netrc_path).authenticators(host)
            if _netrc:
                # Return with login / password
                login_i = 0 if _netrc[0] else 1
                return (_netrc[login_i], _netrc[2])
        except (NetrcParseError, OSError):
            # If there was a parsing error or a permissions issue reading the file,
            # we'll just skip netrc auth unless explicitly asked to raise errors.
            if raise_errors:
                raise

    # App Engine hackiness.
    except (ImportError, AttributeError):
        pass


def get_keyring_auth(url: str, username: str | None) -> tuple[str | None, str | None] | None:
    """Returns the Requests tuple auth for a given url from keyring."""

    if not HAVE_KEYRING:
        return None

    if hasattr(keyring, "get_credential"):  # type: ignore[reportPossiblyUnboundVariable]
        logger.debug(f"Getting credentials from keyring for {url}")
        cred = keyring.get_credential(url, username)  # type: ignore[reportPossiblyUnboundVariable]
        if cred is not None:
            return cred.username, cred.password
        return None

    if username is not None:
        logger.debug(f"Getting password from keyring for {url}")
        password = keyring.get_password(url, username)  # type: ignore[reportPossiblyUnboundVariable]
        if password:
            return username, password
    return None


def get_index_urls():
    index_urls = [(DEFAULT_PYPI_URL if url == DEFAULT_JSON_PYPI_URL else url) for url in _get_pip_index_urls()]

    # Include netrc auth in URLs if available
    authed_index_urls = []
    for index_url in index_urls:
        try:
            parsed_url = parse_url(index_url)
        except Exception:
            logger.warning(f"Failed to parse PyPI index URL {index_url}. Skipping URL")
            continue

        # If the URL is not http(s), skip it
        if parsed_url.scheme not in ("http", "https"):
            logger.debug(f"Skipping PyPI index URL with unexpected scheme {index_url}")
            continue

        host = parsed_url.host or ""
        # If the host is a local domain, skip it
        if host.endswith(".local") or host.startswith("localhost"):
            logger.debug(f"Skipping local PyPI index URL {index_url}")
            continue

        # Do not bother checking for passwords to pypi.org
        if index_url != DEFAULT_PYPI_URL:
            index_url = set_auth_for_url(parsed_url)

        authed_index_urls.append(index_url)

    # If no index URLs were found, use the default PyPI URL
    if not authed_index_urls:
        authed_index_urls = [DEFAULT_PYPI_URL]

    return authed_index_urls


def make_coiled_local_name(dirname: str):
    cleaned_name = re.sub(r"[^\w\d.]+", "_", dirname, flags=re.UNICODE)
    cleaned_name = re.sub(r"_+", "_", cleaned_name)
    cleaned_name = cleaned_name.strip("_")
    # This will happen if dirname is /
    if not cleaned_name:
        cleaned_name = "rootdir"
    return COILED_LOCAL_PACKAGE_PREFIX + cleaned_name
