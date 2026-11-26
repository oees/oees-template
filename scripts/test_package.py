"""Tests for scripts/package.py, the clean zip sent to the OEES tech team."""

import importlib.util
import sys
import zipfile
from pathlib import Path
from types import ModuleType

import pytest


def _load_package_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "package", Path(__file__).with_name("package.py")
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["package"] = module  # dataclasses resolve annotations through it
    spec.loader.exec_module(module)
    return module


package = _load_package_module()

# Built at runtime so this file does not itself look like it holds a secret.
FAKE_DO_TOKEN = "dop_v1_" + "a" * 64
FAKE_REMOTE_URL = "postgresql://app:" + "s3cret" + "@db-cluster.example.com:25060/app"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    return root


@pytest.fixture
def out(tmp_path: Path) -> Path:
    folder = tmp_path / "out"
    folder.mkdir()
    return folder


def make_project(root: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def zipped_names(out: Path, prefix: str) -> set[str]:
    [archive_path] = list(out.glob(f"{prefix}-*.zip"))
    with zipfile.ZipFile(archive_path) as archive:
        return set(archive.namelist())


def test_clean_project_is_zipped_without_dependencies_or_build_output(
    project: Path, out: Path
) -> None:
    make_project(
        project,
        {
            "pyproject.toml": '[project]\nname = "campaign-site"\n',
            "manage.py": "print('ok')\n",
            ".env.example": "DATABASE_URL=postgres://postgres:postgres@db:5432/app\n",
            ".venv/lib/site.py": "x = 1\n",
            "staticfiles/app.css": "body {}\n",
            "apps/__pycache__/x.pyc": "x",
        },
    )

    assert package.main(["--out", str(out)], root=project) == 0
    assert zipped_names(out, "campaign-site") == {
        "campaign-site/pyproject.toml",
        "campaign-site/manage.py",
        "campaign-site/.env.example",
    }


def test_env_and_key_files_are_never_zipped(project: Path, out: Path) -> None:
    make_project(
        project,
        {
            "pyproject.toml": '[project]\nname = "site"\n',
            ".env": "DJANGO_SECRET_KEY=x\n",
            ".env.production": "X=y\n",
            "certs/server.key": "k",
        },
    )

    assert package.main(["--out", str(out)], root=project) == 0
    assert zipped_names(out, "site") == {"site/pyproject.toml"}


def test_token_in_source_blocks_packaging(project: Path, out: Path) -> None:
    make_project(project, {"apps/api.py": f'TOKEN = "{FAKE_DO_TOKEN}"\n'})

    problems = package.scan(project).problems

    assert len(problems) == 1
    assert "apps/api.py:1" in problems[0]
    assert FAKE_DO_TOKEN not in problems[0]
    assert package.main(["--out", str(out)], root=project) == 1
    assert list(out.iterdir()) == []


def test_remote_connection_string_blocks_but_local_one_does_not() -> None:
    local = "DATABASE_URL=postgres://postgres:postgres@localhost:5432/app\n"

    assert package.find_secrets(local) == []
    assert package.find_secrets(f"DATABASE_URL={FAKE_REMOTE_URL}\n") == [
        (1, "a connection string with a password")
    ]


def test_secrets_inside_excluded_folders_are_ignored(project: Path) -> None:
    make_project(project, {"manage.py": "ok", ".venv/pkg/key.txt": FAKE_DO_TOKEN})

    assert package.scan(project).problems == []


def test_oversized_file_blocks_packaging(project: Path) -> None:
    make_project(project, {"manage.py": "ok"})
    with (project / "video.mp4").open("wb") as handle:
        handle.truncate(package.MAX_FILE_BYTES + 1)

    problems = package.scan(project).problems

    assert len(problems) == 1
    assert "video.mp4" in problems[0]


def test_zip_name_comes_from_the_project_table_of_pyproject(project: Path) -> None:
    make_project(
        project,
        {
            "pyproject.toml": (
                '[tool.example]\nname = "not-this"\n\n'
                '[project]\nversion = "0.1.0"\nname = "campaign-2027"\n'
            )
        },
    )

    assert package.project_name(project) == "campaign-2027"
