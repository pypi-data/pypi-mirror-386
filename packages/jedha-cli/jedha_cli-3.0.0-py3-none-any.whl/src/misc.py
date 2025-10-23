import platform
import subprocess
import sys
from typing import List, Optional

import requests
import typer
from rich import print
from yaml import load

try:
    # Python 3.9+
    from importlib.resources import files
except ImportError:
    # Python 3.8 fallback
    from importlib_resources import files

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


PACKAGE_NAME = "jedha-cli"


def get_latest_version() -> Optional[str]:
    """
    Get the latest version of a package from PyPI.
    """
    url = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data["info"]["version"]
        else:
            print("Warning: Unable to connect to PyPI")
    except requests.Timeout:
        print("Warning: Timeout when trying to connect to get last version from PyPI")
    except Exception as e:
        print(f"Error: {e}")
    return None


def current_installed_version() -> str:
    """
    Get the current installed version of the package from pyproject.toml.
    """
    try:
        from importlib.metadata import version
    except ImportError:
        print("Warning: importlib-metadata not found. Please upgrade to Python 3.8+")
    try:
        return version(PACKAGE_NAME)
    except Exception as e:
        print(
            f"Error retrieving version for package {PACKAGE_NAME}: {e}", file=sys.stderr
        )
        raise SystemExit(1)


def check_for_updates() -> None:
    """
    Check for updates to the package.
    """
    latest_version = get_latest_version()
    if latest_version is not None:
        if latest_version != current_installed_version():
            print(
                f"Warning! New version of {PACKAGE_NAME} available: {latest_version}. You are using {current_installed_version()}. Please upgrade."
            )
    else:
        print("Unable to check for updates.")


def get_lab_config_file(labname: str) -> str:
    """
    Get the content of the lab's Docker Compose configuration file.
    Args:
        labname (str): The name of the lab.
    Returns:
        str: The content of the lab's Docker Compose configuration file.
    """
    if labname is None:
        return None
    return str(files("src") / "labs" / labname / "docker-compose.prod.yaml")


def run_command(command: List[str]) -> bool:
    """
    Utility function to run a command and return True if it succeeds.

    Args:
        command (List[str]): The command to run as a list of strings.
    Returns:
        bool: True if the command succeeds, False otherwise.
    """
    try:
        subprocess.run(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def docker_is_installed() -> bool:
    """
    Check if Docker is installed on the machine.

    Returns:
        bool: True if Docker is installed, False otherwise.
    """
    return run_command(["docker", "--version"])


def docker_compose_v2_is_installed() -> bool:
    """
    Check if Docker Compose V2 is installed on the machine.

    Returns:
        bool: True if Docker Compose is installed, False otherwise.
    """
    return run_command(["docker", "compose", "version"])


def docker_compose_v1_is_installed() -> bool:
    """
    Check if Docker Compose V1 is installed on the machine.

    Returns:
        bool: True if Docker Compose is installed, False otherwise.
    """
    return run_command(["docker-compose", "--version"])


def docker_requires_sudo() -> bool:
    """
    Check if Docker requires sudo.

    Returns:
        bool: True if Docker requires sudo, False otherwise.
    """
    return not run_command(["docker", "ps"])


def get_docker_compose_command(args: List[str]) -> List[str]:
    """
    Manage the Docker command depending on the OS.

    Args:
        args (List[str]): The arguments to pass to the Docker compose command.
    """
    if not docker_is_installed():
        print("Docker not found. Please install it.")
        raise typer.Exit(code=1)
    if docker_compose_v2_is_installed():
        args.insert(0, "docker")
        args.insert(1, "compose")
    elif docker_compose_v1_is_installed():
        args.insert(0, "docker-compose")
    else:
        print(
            "Docker Compose (either V1 or V2) not found. Please install Docker Desktop or docker-compose."
        )
        raise typer.Exit(code=1)
    if platform.system() != "Darwin" or docker_requires_sudo():
        args.insert(0, "sudo")
    return args


def is_docker_running() -> bool:
    """
    Check if Docker is running.

    Returns:
        bool: True if Docker is running, False otherwise.
    """
    command = get_docker_compose_command(["ls"])
    return run_command(command)


def get_yaml_labs() -> list[dict]:
    labs_yaml_content = (files("src") / "labs.yaml").read_text()
    filename_array = load(labs_yaml_content, Loader=Loader)
    return filename_array

def get_lab_folder_name(labname: str) -> str:
    """
    Get the name of the lab.
    """
    yaml_labs = get_yaml_labs()
    for lab in yaml_labs:
        if lab["name"] == labname:
            if "folder" in lab:
                return lab["folder"]
            else:
                return lab["name"]
    return None


def get_running_labs() -> set[str]:
    """
    Get the list of running labs.

    Returns:
        set[str]: The list of running labs.
    """
    try:
        command = get_docker_compose_command(["ls"])
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        lines = result.stdout.splitlines()
        running_labs = set(line.split()[0] for line in lines[1:])
        yaml_labs = get_yaml_labs()
        all_labs_names = [lab["name"] for lab in yaml_labs]
        all_labs = set(all_labs_names)

        return running_labs & all_labs
    except Exception as e:
        print("We failed to check on Docker Compose. Is Docker running?")
        raise typer.Exit(1)


def is_lab_already_running(verbose: bool = True) -> bool:
    """
    Check if one lab is already running.

    Args:
        verbose (bool, optional): Whether to print a message if a lab is already running. Defaults to True.
    Returns:
        bool: True if one lab at least is already running, False otherwise.
    """
    running_labs = get_running_labs()
    if running_labs:
        if verbose:
            print(
                f"🫣 You already have the following running labs: [b]{', '.join(running_labs)}[/b]. Please stop them before starting a new one."
            )
        return True
    return False


def clean_docker_network() -> None:
    """
    Clean Docker Network using `prune` to avoid conflicting IP range issues.
    """
    try:
        command = (
            ["sudo", "docker", "network", "prune", "-f"]
            if docker_requires_sudo()
            else ["docker", "network", "prune", "-f"]
        )
        subprocess.run(command, check=True)
        print("🧹 Docker network")
    except Exception as e:
        print(f"❌ Error while network pruning: {e}")


def cleanup_lab(labname: str, lab_config_file: str) -> None:
    """
    Cleanup the lab by removing the containers and networks.

    Args:
        labname (str): The name of the lab.
        lab_config_file (str): The path to the lab's Docker Compose configuration.
    """
    try:
        print("🏋️ Cleaning up the lab before starting it.")
        clean_docker_network()
        command = get_docker_compose_command(
            [
                "-p",
                labname,
                "--file",
                lab_config_file,
                "down",
                "--remove-orphans",
                "--volumes",
            ],
        )
        subprocess.run(
            command,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to clean lab {labname}.")
