from pathlib import Path

import pytest

from app.errors import AppError
from app.filesystem import FileSystemService


def test_resolves_root_relative_path(test_env: Path):
    service = FileSystemService(root=test_env, app_data_dir=test_env.parent / "app-data")
    assert service.resolve("/") == test_env.resolve()
    assert service.resolve("/nested", must_exist=False).parent == test_env.resolve()


def test_blocks_parent_traversal(test_env: Path):
    service = FileSystemService(root=test_env, app_data_dir=test_env.parent / "app-data")
    with pytest.raises(AppError) as exc:
        service.resolve("/../secret")
    assert exc.value.code == "path_outside_root"


def test_blocks_missing_absolute_path_outside_root(test_env: Path):
    service = FileSystemService(root=test_env, app_data_dir=test_env.parent / "app-data")
    with pytest.raises(AppError) as exc:
        service.resolve("/etc/passwd")
    assert exc.value.code == "path_not_found"


def test_blocks_symlink_escape(test_env: Path, tmp_path: Path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret", encoding="utf-8")
    link = test_env / "link"
    link.symlink_to(outside, target_is_directory=True)
    service = FileSystemService(root=test_env, app_data_dir=test_env.parent / "app-data")
    with pytest.raises(AppError) as exc:
        service.resolve("/link/secret.txt")
    assert exc.value.code == "path_outside_root"


def test_rejects_invalid_new_name(test_env: Path):
    service = FileSystemService(root=test_env, app_data_dir=test_env.parent / "app-data")
    with pytest.raises(AppError) as exc:
        service.validate_name("../bad")
    assert exc.value.code == "invalid_name"
