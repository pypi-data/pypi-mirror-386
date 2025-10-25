"""
Pytest configuration file for arcgis-overture tests.

It is used to set up fixtures and configurations for running tests, 
especially when tests are spread acrsoss multiple files.
"""
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="function")
def tmp_dir() -> Path:
    """Create a temporary directory for testing purposes. When the test is done, the directory and its contents are deleted."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture(scope="function")
def tmp_gdb(tmp_dir: Path) -> Path:
    """Create a temporary file geodatabase for testing purposes. When the test is done, the geodatabase and its contents are deleted."""
    import arcpy

    gdb_pth: str = arcpy.management.CreateFileGDB(str(tmp_dir), "test.gdb")[0]
    yield Path(gdb_pth)
    arcpy.Delete_management(gdb_pth)


@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Set up any necessary environment variables or configurations before tests run."""
    # Example: Set an environment variable
    import os

    os.environ["TEST_ENV"] = "true"
    yield
    # Teardown code can go here if needed
    del os.environ["TEST_ENV"]
