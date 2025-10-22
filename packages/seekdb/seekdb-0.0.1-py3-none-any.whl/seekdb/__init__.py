"""
OceanBase SeekDB Python Embed

This module provides Python bindings for OceanBase SeekDB database.
The actual C++ extension (oblite.so) is downloaded on first import to keep
the package size small.
"""

import os
import sys
import platform
import hashlib
import urllib.request
import urllib.error
import gzip
import shutil
from pathlib import Path
from typing import Optional
import traceback

__version__ = "0.0.1"
__author__ = "OceanBase"

# Base URL for downloading binaries - can be overridden via OBLITE_IMAGE_BASEURL
_DEFAULT_BASE_URL = "https://github.com/oceanbase/oceanbase-seekdb/releases/download/"
_BASE_URL = os.environ.get("OBLITE_IMAGE_BASEURL", _DEFAULT_BASE_URL)

_LIB_FILE_NAME = "oblite"

# Configuration for downloading the .so file
_SO_DOWNLOAD_CONFIG = {
    "base_url": _BASE_URL,
    "version": f"v{__version__}",  # Tag/version in release assets
    "filename": f"{_LIB_FILE_NAME}.so",
    "compressed_filename": f"{_LIB_FILE_NAME}.so.gz",  # Compressed version
    "checksum": None,  # Will be set after first successful download
}

def _initialize_module():
    try:
        seekdb_module = _load_oblite_module()
        attributes = []
        for attr_name in dir(seekdb_module):
            if not attr_name.startswith('_'):
                setattr(sys.modules[__name__], attr_name, getattr(seekdb_module, attr_name))
                attributes.append(attr_name)
    except Exception as e:
        print(f"Warning: Failed to import seekdb module: {e}")
        attributes = []
    return attributes

def _get_platform_info():
    """Get platform information for downloading the correct .so file"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        if machine in ["x86_64", "amd64"]:
            return "linux-x86_64"
        elif machine in ["aarch64", "arm64"]:
            return "linux-aarch64"

    raise RuntimeError(f"Unsupported platform: {system}-{machine}")

def _get_python_version() -> str:
    return f'py{sys.version_info.major}.{sys.version_info.minor}'

def _get_cache_dir() -> Path:
    """Get the cache directory path organized by version/revision/platform"""
    platform_info = _get_platform_info()
    cache_dir = (
        Path.home()
        / ".seekdb"
        / "cache"
        / __version__
        / _SO_DOWNLOAD_CONFIG["revision"]
        / platform_info
        / _get_python_version()
    )
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def _get_so_path() -> Path:
    """Get the path where the .so file should be stored in user cache directory"""
    return _get_cache_dir() / f"{_LIB_FILE_NAME}.so"

def config_info() -> dict:
    """Get current configuration information"""
    return {
        "version": __version__,
        "revision": _SO_DOWNLOAD_CONFIG["revision"],
        "base_url": _SO_DOWNLOAD_CONFIG["base_url"],
        "platform": _get_platform_info(),
        "python_version": _get_python_version(),
        "cache_dir": str(_get_cache_dir()),
    }

def _download_so_file(force_download: bool = False) -> bool:
    """
    Download the oblite.so file if it doesn't exist or if force_download is True

    Args:
        force_download: If True, download even if file exists

    Returns:
        True if download was successful, False otherwise
    """
    so_path = _get_so_path()

    # Check if file already exists and we're not forcing download
    if so_path.exists() and not force_download:
        print(f"{_LIB_FILE_NAME}.so already exists at {so_path}")
        return True

    try:
        platform_info = _get_platform_info()
        # Filenames include platform and revision so multiple revisions can coexist
        asset_prefix = f"{_LIB_FILE_NAME}-{platform_info}-{_SO_DOWNLOAD_CONFIG['revision']}-{_get_python_version()}"
        # Try compressed version first
        compressed_url = f"{_SO_DOWNLOAD_CONFIG['base_url']}{_SO_DOWNLOAD_CONFIG['version']}/{asset_prefix}.so.gz"
        uncompressed_url = f"{_SO_DOWNLOAD_CONFIG['base_url']}{_SO_DOWNLOAD_CONFIG['version']}/{asset_prefix}.so"

        # Create temporary files
        temp_compressed = so_path.with_suffix('.so.gz.tmp')
        temp_uncompressed = so_path.with_suffix('.so.tmp')

        def show_progress(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, (block_num * block_size * 100) // total_size)
                sys.stdout.write(f"\rDownloading: {percent}%")
                sys.stdout.flush()

        # Try to download compressed version first
        try:
            print(f"Downloading compressed {_LIB_FILE_NAME}.so from {compressed_url}...")
            urllib.request.urlretrieve(compressed_url, temp_compressed, reporthook=show_progress)
            print()  # New line after progress

            # Verify compressed file size (should be much smaller)
            if temp_compressed.stat().st_size < 10 * 1024 * 1024:  # Less than 10MB is suspicious for compressed
                temp_compressed.unlink()
                raise RuntimeError("Compressed file seems too small")

            # Decompress the file
            print("Decompressing file...")
            with gzip.open(temp_compressed, 'rb') as f_in:
                with open(temp_uncompressed, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Clean up compressed file
            temp_compressed.unlink()

        except (urllib.error.URLError, RuntimeError) as e:
            print(f"Failed to download compressed version: {e}")
            print("Trying uncompressed version...")

            # Clean up any partial files
            if temp_compressed.exists():
                temp_compressed.unlink()

            # Try uncompressed version
            print(f"Downloading uncompressed {_LIB_FILE_NAME}.so from {uncompressed_url}...")
            urllib.request.urlretrieve(uncompressed_url, temp_uncompressed, reporthook=show_progress)
            print()  # New line after progress

        # Verify the final file size
        if temp_uncompressed.stat().st_size < 100 * 1024 * 1024:  # Less than 100MB is suspicious
            temp_uncompressed.unlink()
            raise RuntimeError("Downloaded file seems too small, download may have failed")

        # Move to final location
        temp_uncompressed.rename(so_path)
        print(f"Successfully downloaded and decompressed {_LIB_FILE_NAME}.so to {so_path}")
        return True

    except urllib.error.URLError as e:
        print(f"Failed to download {_LIB_FILE_NAME}.so: {e}")
        print("Please check your internet connection and try again.")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"Error downloading {_LIB_FILE_NAME}.so: {e}")
        traceback.print_exc()
        return False

def _load_oblite_module():
    """Load the oblite module, downloading the .so file if necessary"""
    so_path = _get_so_path()

    # Try to download if file doesn't exist
    if not so_path.exists():
        print(f"{_LIB_FILE_NAME}.so not found in cache directory: {so_path.parent}")
        print("Attempting to download...")
        if not _download_so_file():
            raise ImportError(
                "Failed to download {_LIB_FILE_NAME}.so. Please check your internet connection "
                f"or manually place {_LIB_FILE_NAME}.so in the cache directory: {so_path.parent}"
            )

    # Add the cache directory to sys.path so we can import the .so file
    cache_dir = str(so_path.parent)
    if cache_dir not in sys.path:
        sys.path.insert(0, cache_dir)

    try:
        # Import the module
        import oblite
        return oblite
    except ImportError as e:
        raise ImportError(f"Failed to import {_LIB_FILE_NAME} module from {cache_dir}: {e}")

__all__ = ['__version__', 'config_info']
__all__.extend(_initialize_module())