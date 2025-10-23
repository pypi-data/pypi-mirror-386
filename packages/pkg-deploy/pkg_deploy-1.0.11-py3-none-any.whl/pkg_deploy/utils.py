import os
import re
import sys
import shutil
import tomlkit
import logging
import getpass
import argparse
import subprocess
import configparser
from pathlib import Path
from typing import Optional, Tuple
from tomlkit.toml_document import TOMLDocument


logger = logging.getLogger(__name__)


def is_uv_venv() -> bool:
    """Detect if the current virtual environment was created by uv (supports versioned marker)."""
    if not hasattr(sys, 'prefix') or not sys.prefix:
        return False
    pyvenv_cfg = Path(sys.prefix) / "pyvenv.cfg"
    if not pyvenv_cfg.exists():
        return False
    try:
        with open(pyvenv_cfg, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.lower().startswith("uv ="):
                    logger.info("Detected uv-managed Python.")
                    return True
    except Exception:
        pass
    return False

def setup_uv_compatibility():
    if is_uv_venv():
        logger.info("Setting PIP_USE_VIRTUALENV=1 for build compatibility.")
        os.environ["PIP_USE_VIRTUALENV"] = "1"
        return True
    else:
        return False


def get_credentials(username: Optional[str] = None,
                    password: Optional[str] = None,
                    url: str = "",
                    is_pypi: bool = False
                    ) -> Tuple[Optional[str], Optional[str]]:
    is_pypi = "upload.pypi.org" in url or is_pypi
    if not username:
        if is_pypi:
            logger.info("For PyPI API tokens, use '__token__' as username")
            username = "__token__"
        else:
            username = input(f"Please enter username for {url}:").strip()

    if not username:
        raise ValueError("Username cannot be empty")

    logger.info(f"Using username: {username}")

    if not password:
        if is_pypi:
            password = getpass.getpass("PyPI API token: ")
        else:
            password = getpass.getpass(f"Please enter password for {url}:")

    if not password:
        raise ValueError("Password/Token cannot be empty")

    return username, password


def parse_prerelease(version: str):
    # Match the pattern: numbers.numbers.numbers + optional prerelease type + optional version
    pattern = r'^(\d+)\.(\d+)\.(\d+)([abc]|rc)?(\d*)$'
    match = re.match(pattern, version)

    if match:
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        prerelease_type = match.group(4)  # None if no prerelease

        if prerelease_type and match.group(5):
            prerelease_version = int(match.group(5))
        elif prerelease_type:
            prerelease_version = 1
        else:
            prerelease_version = None

        return {
            'major': major,
            'minor': minor,
            'patch': patch,
            'prerelease_type': prerelease_type,
            'prerelease_version': prerelease_version,
            'has_prerelease': prerelease_type is not None
        }
    else:
        raise ValueError(f"Invalid version format: {version}")


def get_pypirc_info():
    """
    Read and parse .pypirc file from user's home directory.
    Returns a dictionary with repository configurations.
    """
    # Get the path to .pypirc file
    home_dir = Path.home()
    pypirc_path = home_dir / '.pypirc'

    if not pypirc_path.exists():
        raise FileNotFoundError(f"No .pypirc file found at {pypirc_path}")

    # Parse the configuration file
    config = configparser.ConfigParser()

    try:
        config.read(pypirc_path)

        # Extract information
        pypirc_info = {}

        # Get index servers if available
        if config.has_section('distutils') and config.has_option('distutils', 'index-servers'):
            index_servers = config.get('distutils', 'index-servers').split()
            pypirc_info['index_servers'] = index_servers

        # Get repository configurations
        repositories = {}
        for section_name in config.sections():
            if section_name != 'distutils':
                repo_config = {}
                for option in config.options(section_name):
                    repo_config[option] = config.get(section_name, option)
                repositories[section_name] = repo_config
        if not repositories:
            raise ValueError(f"No repositories configuration found in {pypirc_path}")

        pypirc_info['repositories'] = repositories
        return pypirc_info
    except Exception as e:
        logger.error(f"Error reading .pypirc file: {e}")
        return None

def ensure_uv_installed():
    """Check if 'uv' is available, and install it if not."""
    if shutil.which("uv"):
        logger.info("uv is already installed and available in PATH.")
        return

    try:
        result = subprocess.run(
            [sys.executable, "-m", "uv", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"uv is installed as a module: {result.stdout.strip()}")
        return
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass  # uv not available as module either

    logger.info("uv not found. Installing uv via pip...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "uv"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("uv installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error("Failed to install uv:", e.stderr)
        raise RuntimeError(
            "Failed to install uv automatically. Please install it manually:\n"
            "  pip install uv\n"
            "Or download from: https://github.com/astral-sh/uv/releases"
        ) from e

    try:
        result = subprocess.run(
            [sys.executable, "-m", "uv", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"uv version: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError("uv installed but failed to run.") from e


def load_config(pyproject_path: Path) -> TOMLDocument:
    """load pyproject.toml"""
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    with open(pyproject_path, "r", encoding="utf-8") as f:
        content = f.read()
    config = tomlkit.parse(content)
    return config


def save_config(config, pyproject_path: Path):
    with open(pyproject_path, 'w', encoding='utf-8') as f:
        f.write(tomlkit.dumps(config))


def validate_version_arg(value: str) -> str:
    """
    Custom argparse validator that checks if a version string conforms to SemVer.
    Returns the value if valid, raises an error otherwise.
    """
    version_pattern = re.compile(r"^\d+\.\d+\.\d+(a\d+|b\d+|rc\d+)?$")

    if not version_pattern.match(value):
        raise argparse.ArgumentTypeError(
            f"Invalid version format: '{value}'. Valid examples:\n"
            "  Final release: 1.2.0\n"
            "  Alpha release: 1.2.0a1\n"
            "  Beta release: 1.2.0b1\n"
            "  Release candidate: 1.2.0rc1"
        )
    return value
