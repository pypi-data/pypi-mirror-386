from __future__ import annotations

import re
import sys
from pathlib import Path

import click

__all__ = ["release"]

from ._utils import (
    bootstrap_dev,
    get_project_metadata,
    gh_available,
    gh_release_create,
    gh_release_edit,
    gh_release_exists,
    git_branch,
    git_create_annotated_tag,
    git_delete_tag,
    git_push,
    git_tag_exists,
    read_version_from_pyproject,
    run,
)


PROJECT = get_project_metadata()


def release(*, remote: str = "origin") -> None:
    version = read_version_from_pyproject(Path("pyproject.toml"))
    if not version or not _looks_like_semver(version):
        raise SystemExit("[release] Could not read version X.Y.Z from pyproject.toml")
    click.echo(f"[release] Target version {version}")
    click.echo("[release] project diagnostics: " + ", ".join(PROJECT.diagnostic_lines()))

    # Verify clean working tree
    _ensure_clean()

    # Ensure dev tools for build/test flows (optional)
    bootstrap_dev()

    # Run local checks
    click.echo("[release] Running validation suite (python -m scripts.test)")
    run(["python", "-m", "scripts.test"], capture=False)

    # Remove stray 'v' tag (local and remote)
    git_delete_tag("v", remote=remote)

    # Push branch
    branch = git_branch()
    click.echo(f"[release] Pushing branch {branch} to {remote}")
    git_push(remote, branch)

    # Tag and push
    tag = f"v{version}"
    if git_tag_exists(tag):
        click.echo(f"[release] Tag {tag} already exists locally")
    else:
        git_create_annotated_tag(tag, f"Release {tag}")
    click.echo(f"[release] Pushing tag {tag}")
    git_push(remote, tag)

    # Create or edit GitHub release
    if gh_available():
        if gh_release_exists(tag):
            gh_release_edit(tag, tag, f"Release {tag}")
        else:
            click.echo(f"[release] Creating GitHub release {tag}")
            gh_release_create(tag, tag, f"Release {tag}")
    else:
        click.echo("[release] gh CLI not found; skipping GitHub release creation")

    click.echo(f"[release] Done: {tag} tagged and pushed.")


def _ensure_clean() -> None:
    if run(["bash", "-lc", "! git diff --quiet || ! git diff --cached --quiet"], check=False).code == 0:
        raise SystemExit("[release] Working tree not clean. Commit or stash changes first.")


def _looks_like_semver(v: str) -> bool:
    return bool(re.match(r"^[0-9]+\.[0-9]+\.[0-9]+$", v))


if __name__ == "__main__":  # pragma: no cover
    from .cli import main as cli_main

    cli_main(["release", *sys.argv[1:]])
