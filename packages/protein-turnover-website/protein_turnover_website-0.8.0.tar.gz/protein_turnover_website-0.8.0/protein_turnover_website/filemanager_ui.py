from __future__ import annotations

import hashlib
import os
import tomllib
from datetime import datetime
from pathlib import Path
from shutil import copy
from typing import Any
from typing import Sequence

import click


def hash256(filename: Path, bufsize: int = 4096 * 8, algo: str = "sha256") -> bytes:
    sha256_hash = hashlib.new(algo, usedforsecurity=False)
    with filename.open("rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(bufsize), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.digest()


def issame(f1: Path, f2: Path) -> bool:
    """Check if two files are the same by comparing size"""
    s1 = f1.stat()
    s2 = f2.stat()
    return s1.st_size == s2.st_size


def isidentical(f1: Path, f2: Path) -> bool:
    """Check if two files are the same by comparing hash"""
    if not issame(f1, f2):
        return False
    return hash256(f1) == hash256(f2)


def restore(path: Path) -> dict[str, Any]:
    with path.open("rb") as f:
        return tomllib.load(f)


def link_all_jobs(
    archives: Sequence[Path],
    linkto: Path,
    *,
    date: datetime | None = None,
    verbose: bool = False,
):
    if not linkto.exists():
        linkto.mkdir(parents=True)
    for root in archives:

        ts = date.timestamp() if date else None
        for d, _, files in root.walk():
            if any(f.endswith(".toml") for f in files):
                r = d.relative_to(root)
                to = linkto / r
                if files:
                    to.mkdir(parents=True, exist_ok=True)

                for f in files:
                    orig = d / f
                    dst = to / f

                    if dst.exists():
                        if isidentical(orig, dst):
                            if verbose:
                                click.secho(f"Skipping identical: {dst}", fg="green")
                        else:
                            click.secho(
                                f"Skipping existing (but different!): {dst}",
                                fg="yellow",
                                bold=True,
                            )
                        continue
                    if not f.endswith(".toml"):
                        dst.symlink_to(orig)
                        # os.symlink(orig, dst)
                    else:
                        copy(orig, dst)
                        if ts is not None:
                            os.utime(dst, (ts, ts))
                        else:
                            mtime = orig.stat().st_mtime
                            os.utime(dst, (mtime, mtime))
                        if verbose:
                            click.secho(f"Copied: {orig}", fg="blue")


def archive_all_jobs(
    root_list: Sequence[Path],
    archive: Path,
    *,
    verbose: bool = False,
) -> int:
    if not archive.exists():
        archive.mkdir(parents=True)
    n = 0
    for root in root_list:
        for d, _, files in root.walk():
            if any(f.endswith(".toml") for f in files):
                r = d.relative_to(root)
                to = archive / r
                to.mkdir(parents=True, exist_ok=True)

                for f in files:
                    orig = d / f
                    dst = to / f

                    if orig.is_symlink():
                        # skip symlinks
                        continue

                    if dst.exists():
                        if isidentical(orig, dst):
                            if verbose:
                                click.secho(f"Skipping identical: {dst}", fg="green")
                        else:
                            click.secho(
                                f"Skipping existing (but different!): {dst}",
                                fg="yellow",
                                bold=True,
                            )
                        continue

                    copy(orig, dst)
                    if orig.suffix == ".toml":
                        n += 1
                    mtime = orig.stat().st_mtime
                    os.utime(dst, (mtime, mtime))
                    if verbose:
                        click.secho(f"Copied: {orig}", fg="blue")
    return n


def remove_failed_jobs(
    archives: Sequence[Path],
    *,
    verbose: bool = False,
    dryrun: bool = False,
) -> int:
    n = 0
    for archive in archives:
        if not archive.exists():
            continue

        for d, _, files in archive.walk():
            for f in files:
                if not f.endswith(".toml"):
                    continue
                orig = d / f
                jobid = orig.stem
                try:
                    job = restore(orig)
                    if "status" in job:
                        status = job["status"]
                    else:
                        status = None

                    if not dryrun and "finished_time" in job and status == "finished":
                        try:
                            t: float = job["finished_time"].timestamp()
                            os.utime(orig, (t, t))
                        except ValueError:
                            pass

                except Exception as e:
                    if verbose:
                        click.secho(f"Could not restore job from {orig}: {e}", fg="red")
                    status = "failed"

                if status != "finished":
                    n += 1
                    if verbose and not dryrun:
                        click.secho(f"Removing job: {orig} [{status}]", fg="red")
                    for ext in [".log", ".sqlite", ".sqlite.gz", ".toml"]:
                        ff = d / (jobid + ext)
                        if dryrun:
                            if ff.exists():
                                click.secho(f"Would remove: {ff}", fg="yellow")
                        else:
                            ff.unlink(missing_ok=True)
    return n


def verbose_option(f):
    return click.option("-v", "--verbose", is_flag=True, help="be verbose")(f)


@click.group()
@click.version_option()
def cli():
    pass


@cli.command()
@verbose_option
@click.option(
    "-d",
    "--date",
    help='set time of copied TOML files as iso format "YYYY-MM-DD HH:MM:SS"'
    " (to ensure these file appear last for instance)",
)
@click.argument("dst", type=click.Path(dir_okay=True, file_okay=False))
@click.argument(
    "archives",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    nargs=-1,
    required=True,
)
def mirror(
    archives: tuple[str, ...],
    dst: str,
    date: str | None,
    verbose: bool,
) -> None:
    """Create a shadow directory tree with copied .toml files and links to everthing else.

    The archive directories are scanned for jobs (directories with .toml files).
    Only .toml files are copied, everything else is linked.
    """
    if date is not None:
        d = datetime.fromisoformat(date)
    else:
        d = None
    link_all_jobs(
        [Path(s).expanduser() for s in archives],
        Path(dst).expanduser(),
        date=d,
        verbose=verbose,
    )


@cli.command()
@verbose_option
@click.argument("archive", type=click.Path(dir_okay=True, file_okay=False))
@click.argument(
    "sources",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    nargs=-1,
    required=True,
)
def archive(sources: tuple[str, ...], archive: str, verbose: bool) -> None:
    """Create an archive copy of all jobs.

    Take source directories and copy all files to the archive directory.
    Only copy files that do not exist in the archive (see mirror to reconstitue this archive).
    """
    n = archive_all_jobs(
        [Path(s).expanduser() for s in sources],
        Path(archive).expanduser(),
        verbose=verbose,
    )

    click.secho(f"Archived {n} job(s) to {archive}", fg="green")


@cli.command()
@verbose_option
@click.option("-f", "--no-dryrun", is_flag=True, help="actual run (files are removed)")
@click.argument(
    "archives",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    nargs=-1,
    required=True,
)
def remove_failed(archives: tuple[str, ...], verbose: bool, no_dryrun: bool) -> None:
    """Remove failed jobs from the given archives"""

    dryrun = not no_dryrun
    n = remove_failed_jobs(
        [Path(s).expanduser() for s in archives],
        verbose=verbose,
        dryrun=dryrun,
    )

    verb = "Would remove" if dryrun else "Removed"
    click.secho(f"{verb} {n} job(s)", fg="green")


if __name__ == "__main__":
    cli()
