from pathlib import Path

# This assumes your asset management code is saved in 'asset_manager.py'
import simplipy as sp
import pytest

# --- Test Constants ---
# These tests use real, known assets from the psaegert/simplipy-assets-test manifest.
# An active internet connection is required to run them.
VALID_ENGINE = "dev_7-3"
VALID_TEST_DATA = "expressions_10k"
INVALID_ASSET = "this-asset-does-not-exist"

HF_MANIFEST_REPO = "psaegert/simplipy-assets-test"
HF_MANIFEST_FILENAME = "manifest.json"


def test_install_and_remove_asset(tmp_path: Path):
    """
    Tests the full lifecycle: installing a valid asset and then removing it.
    """
    # --- 1. Installation ---
    # Arrange: Use tmp_path as our isolated local directory.
    # Act: Install a known valid engine.
    install_success = sp.install(
        asset=VALID_ENGINE,
        local_dir=tmp_path,
        repo_id=HF_MANIFEST_REPO,
        manifest_filename=HF_MANIFEST_FILENAME
    )

    # Assert: Check that the installation was successful and files exist.
    assert install_success is True
    expected_dir = tmp_path / "engines" / VALID_ENGINE
    assert expected_dir.is_dir()
    # Based on the manifest for 'dev_7-3', these files should exist.
    assert (expected_dir / "config.yaml").is_file()
    assert (expected_dir / "rules.json").is_file()

    # --- 2. Removal ---
    # Arrange: The asset is now installed.
    # Act: Remove the same asset.
    remove_success = sp.uninstall(
        asset=VALID_ENGINE,
        local_dir=tmp_path,
        repo_id=HF_MANIFEST_REPO,
        manifest_filename=HF_MANIFEST_FILENAME
    )

    # Assert: The removal should be successful and the directory should be gone.
    assert remove_success is True
    assert not expected_dir.exists()


def test_install_non_existent_asset(tmp_path: Path):
    """
    Tests that attempting to install a non-existent asset fails gracefully.
    """
    # Arrange: An invalid asset name.
    # Act: Attempt to install the non-existent asset.
    success = sp.install(
        asset=INVALID_ASSET,
        local_dir=tmp_path,
        repo_id=HF_MANIFEST_REPO,
        manifest_filename=HF_MANIFEST_FILENAME
    )

    # Assert: The function should return False and not create any directories.
    assert success is False
    assert not (tmp_path / "engines" / INVALID_ASSET).exists()


def test_get_asset_path_auto_install(tmp_path: Path):
    """
    Tests get_asset_path's ability to automatically download and return the path
    for an asset that is not yet installed.
    """
    # Arrange: The asset is not installed since tmp_path is empty.
    # Act: Get the path with auto_install=True (the default).
    path_str = sp.get_path(
        asset=VALID_ENGINE,
        local_dir=tmp_path,
        install=True,
        repo_id=HF_MANIFEST_REPO,
        manifest_filename=HF_MANIFEST_FILENAME
    )

    # Assert: A valid path string is returned and the asset is now installed.
    assert path_str is not None
    # The manifest for 'dev_7-3' has entrypoint 'engines/dev_7-3/config.yaml'.
    expected_path = tmp_path / "engines" / VALID_ENGINE / "config.yaml"
    assert path_str == str(expected_path)
    assert expected_path.is_file()


def test_get_asset_path_no_install(tmp_path: Path):
    """
    Tests that get_asset_path raises FileNotFoundError if an asset is not installed
    and install is explicitly set to False.
    """
    # Arrange: The asset is not installed.
    # Act & Assert: Get the path with install=False should raise FileNotFoundError.

    with pytest.raises(FileNotFoundError):
        sp.get_path(
            asset=VALID_ENGINE,
            local_dir=tmp_path,
            install=False,
            repo_id=HF_MANIFEST_REPO,
            manifest_filename=HF_MANIFEST_FILENAME
        )

    # Assert: The asset should not be installed.
    assert not (tmp_path / "engines" / VALID_ENGINE).exists()


def test_get_asset_path_for_local_file(tmp_path: Path):
    """
    Tests that get_asset_path correctly identifies and returns a path
    that already exists on the local filesystem.
    """
    # Arrange: Create a dummy local file.
    local_file = tmp_path / "my_custom_rule.yaml"
    local_file.touch()

    # Act: Call get_asset_path with the full path to the local file.
    path_str = sp.get_path(
        asset=str(local_file),
        repo_id=HF_MANIFEST_REPO,
        manifest_filename=HF_MANIFEST_FILENAME
    )

    # Assert: The function returns the original path string without modification.
    assert path_str == str(local_file)


def test_list_assets_installed_and_available(capsys, tmp_path: Path):
    """
    Tests the list_assets function for both available and installed-only views.
    `capsys` is a pytest fixture to capture stdout.
    """
    # --- 1. List all available assets when none are installed ---
    sp.list_assets('engine', installed_only=False, local_dir=tmp_path, repo_id=HF_MANIFEST_REPO, manifest_filename=HF_MANIFEST_FILENAME)
    captured = capsys.readouterr()
    output = captured.out

    assert "--- Available Assets ---" in output
    assert VALID_ENGINE in output
    assert "[installed]" not in output  # Should not be marked as installed

    # --- 2. Install an asset and list only installed ---
    sp.install(VALID_ENGINE, local_dir=tmp_path, repo_id=HF_MANIFEST_REPO, manifest_filename=HF_MANIFEST_FILENAME)
    sp.list_assets('engine', installed_only=True, local_dir=tmp_path, repo_id=HF_MANIFEST_REPO, manifest_filename=HF_MANIFEST_FILENAME)
    captured = capsys.readouterr()
    output = captured.out

    assert "--- Installed Assets ---" in output
    assert VALID_ENGINE in output
    assert "[installed]" in output
    # A known asset that wasn't installed should not be in the output.
    assert "cis-benchmark-v1" not in output


def test_force_reinstall(tmp_path: Path):
    """
    Tests that the `force=True` flag correctly removes an existing
    asset before reinstalling it.
    """
    # Arrange: Install an asset and add a custom file to its directory.
    sp.install(VALID_ENGINE, local_dir=tmp_path, repo_id=HF_MANIFEST_REPO, manifest_filename=HF_MANIFEST_FILENAME)
    asset_dir = tmp_path / "engines" / VALID_ENGINE
    custom_file = asset_dir / "custom_file.txt"
    custom_file.touch()
    assert custom_file.exists()  # Verify setup

    # Act: Reinstall the same asset with force=True.
    success = sp.install(
        asset=VALID_ENGINE,
        force=True,
        local_dir=tmp_path
    )

    # Assert: The reinstall succeeded and the custom file is now gone.
    assert success is True
    assert not custom_file.exists()
    assert (asset_dir / "config.yaml").is_file()  # Check original files exist.


def test_install_different_asset_types(tmp_path: Path):
    """
    Tests that different asset types ('engine', 'test-data') are handled
    and stored in their respective subdirectories.
    """
    # Arrange & Act: Install one of each asset type.
    engine_success = sp.install(
        asset=VALID_ENGINE,
        local_dir=tmp_path,
        repo_id=HF_MANIFEST_REPO,
        manifest_filename=HF_MANIFEST_FILENAME
    )
    test_data_success = sp.install(
        asset=VALID_TEST_DATA,
        local_dir=tmp_path,
        repo_id=HF_MANIFEST_REPO,
        manifest_filename=HF_MANIFEST_FILENAME
    )

    # Assert: Both installations succeeded and created the correct directories.
    assert engine_success is True
    assert test_data_success is True

    expected_engine_dir = tmp_path / "engines" / VALID_ENGINE
    expected_test_data_dir = tmp_path / "test-data" / "expressions_10k.json"

    print(expected_engine_dir)
    print(expected_test_data_dir)

    assert expected_engine_dir.is_dir()
    assert expected_test_data_dir.is_file()
