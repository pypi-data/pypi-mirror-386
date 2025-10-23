from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import fields
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from flask import abort
from flask import current_app
from flask import Flask
from flask import request
from protein_turnover.background import SimpleQueueClient
from protein_turnover.jobs import remap_job as turnover_remap_job
from protein_turnover.jobs import TurnoverJob
from protein_turnover.utils import PeptideSettings

from .explorer.explorer import find_mountpoint_for
from .explorer.explorer import get_mountpoints
from .explorer.explorer import logger
from .explorer.explorer import safe_repr
from .flask_utils import oktokill
from .jobsmanager import JobsManager
from .jobsmanager import ViewJobsManager


def oktokill_abort() -> None:
    if not oktokill():  # pragma: no cover
        abort(404)


def sanitize(job: TurnoverJob) -> tuple[TurnoverJob, bool]:
    mountpoints = get_mountpoints()
    have_locations = True

    def rep(p: str) -> str:
        nonlocal have_locations
        mp, fname, located = safe_repr(Path(p), mountpoints)
        if not located:  # pragma: no cover
            have_locations = False
            return f'<b class="unknown-mountpoint">{mp.label}</b>:{fname}'
        return f"<b>{mp.label}</b>:{fname}"

    return (
        replace(
            job,
            pepxml=[rep(f) for f in job.pepxml],
            protxml=rep(job.protxml),
            mzmlfiles=[rep(f) for f in job.mzmlfiles],
        ),
        have_locations,
    )


def verify_files(job: TurnoverJob) -> tuple[TurnoverJob, list[str]]:
    missing = []

    def rep(files: list[str]) -> list[str]:
        ret = []
        for f in files:
            p = Path(f)
            if not p.exists():  # pragma: no cover
                missing.append(p.name)
                continue
            ret.append(f)
        return ret

    def prep(xml: str) -> str:
        if not xml:  # pragma: no cover
            return ""
        p = Path(xml)
        if not p.exists():  # pragma: no cover
            missing.append(p.name)
            return ""
        return xml

    job = replace(
        job,
        pepxml=rep(job.pepxml),
        mzmlfiles=rep(job.mzmlfiles),
        protxml=prep(job.protxml),
    )
    return job, missing


def remap_job(job: TurnoverJob) -> TurnoverJob:
    M = current_app.config.get("REMAP_MOUNTPOINTS")
    if not M:
        return job
    return turnover_remap_job(job, M)


@dataclass
class File:
    # what was loaded into hidden value object in jobs.ts
    mountpoint: str
    parent: str
    files: list[str]

    @classmethod
    def from_files(cls, files: list[str]) -> File:
        if len(files) == 0:
            return File("", "", [])

        mountpoints = get_mountpoints()
        paths = [Path(f).expanduser() for f in files]
        paths = [p.absolute() for p in paths]
        mp = find_mountpoint_for(paths[0], mountpoints)
        if mp is None:  # pragma: no cover
            return File("", "", [])
        parent = paths[0].parent.relative_to(mp.mountpoint)
        return File(mp.label, str(parent), [p.name for p in paths])

    def todict(self) -> dict[str, str | list[str]]:
        if len(self.files) == 0:
            return {}
        return asdict(self)

    def to_realfiles(self) -> list[Path]:  # pragma: no cover
        if len(self.files) == 0:
            abort(404)
        if Path(self.parent).is_absolute():  # expecting only relative paths
            abort(404)
        if any(Path(f).is_absolute() for f in self.files):
            abort(404)
        mountpoints = get_mountpoints()
        m = mountpoints.get(self.mountpoint)
        if m is None:  # unknown mountpoint
            abort(404)
        assert m is not None
        return [m.mountpoint.joinpath(self.parent, f) for f in self.files]


def input2files(key: str) -> list[Path]:
    return File(**json.loads(request.form[key])).to_realfiles()


def job_from_form(jobid: str) -> TurnoverJob:
    if (
        not request.form.get("pepxmlfiles")
        or not request.form.get("mzmlfiles")
        or not request.form.get("protxmlfile")
    ):  # pragma: no cover
        abort(400)

    CVT = dict(
        float=float,
        str=str,
        int=int,
        bool=lambda v: v.lower() in {"yes", "y", "1", "true"},
    )
    res = {}
    for field in fields(PeptideSettings):
        if field.name in request.form:
            # only true if ``from __future__ import annotations``
            assert isinstance(field.type, str)
            typ = field.type
            t = "str" if "Literal" in typ else typ
            if t in CVT:
                val = CVT[t](request.form[field.name])  # type: ignore
            else:
                val = request.form[field.name]
            res[field.name] = val

    settings = PeptideSettings(**res)
    if "mzTolerance" in res:
        settings = replace(settings, mzTolerance=settings.mzTolerance / 1e6)

    try:
        pepxmlfiles = input2files("pepxmlfiles")
        protxmlfile = input2files("protxmlfile")
        mzmlfiles = input2files("mzmlfiles")
    except (TypeError, UnicodeDecodeError):  # pragma: no cover
        abort(400)

    if (
        not pepxmlfiles
        or not protxmlfile
        or not mzmlfiles
        or not all(f.exists() for f in protxmlfile)
        or not all(f.exists() for f in mzmlfiles)
        or not all(f.exists() for f in pepxmlfiles)
    ):  # pragma: no cover
        logger.error(
            'job_from_form: no files found: pepxml="%s" protxml="%s" mzml="%s"',
            pepxmlfiles,
            protxmlfile,
            mzmlfiles,
        )
        abort(400)

    match_runNames = request.form.get("match_runNames", "no") == "yes"

    cachedir: str | None = current_app.config.get("CACHEDIR")
    email = request.form.get("email", None)
    if email == "":  # pragma: no cover
        email = None
    jobby = TurnoverJob(
        job_name=request.form.get("job_name", jobid),
        pepxml=[str(s) for s in pepxmlfiles],
        protxml=str(protxmlfile[0]),
        mzmlfiles=[str(s) for s in mzmlfiles],
        settings=settings,
        jobid=jobid,
        cache_dir=str(cachedir) if cachedir else None,
        email=email,
        match_runNames=match_runNames,
    )
    return jobby


def get_bg_client() -> SimpleQueueClient:
    return current_app.extensions["bgclient"]


def get_jobs_manager() -> JobsManager:
    return current_app.extensions["jobsmanager"]


def create_jobs_manager(
    app: Flask,
    jobsdir_list: Sequence[Path],
) -> JobsManager:
    stat_files = app.config.get("STAT_FILES", -1)

    jobsdir_list = [j.absolute() for j in jobsdir_list]
    manager = JobsManager(
        jobsdir_list,
        stat_files=stat_files,
    )
    jobsdir = jobsdir_list[0]
    if not jobsdir.exists():  # pragma: no cover
        jobsdir.mkdir(parents=True, exist_ok=True)

    return manager


def ensure_cachedir(app: Flask) -> Path:
    cachedir = app.config.get("CACHEDIR")
    if not cachedir:  # pragma: no cover
        raise RuntimeError("need config.CACHEDIR directory")

    path = Path(cachedir).expanduser()

    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    app.config["CACHEDIR"] = path
    return path


def get_jobsdir_list(app: Flask) -> list[Path]:
    if "_JOBSDIR_LIST" in app.config:
        return app.config["_JOBSDIR_LIST"]
    jobsdir = app.config.get("JOBSDIR")
    if not jobsdir:
        app.logger.error("need config.JOBSDIR directory")
        raise RuntimeError("need config.JOBSDIR directory")
    if not isinstance(jobsdir, list):
        jobsdir_list = [jobsdir]
    else:
        jobsdir_list = jobsdir

    jobsdir_list = [Path(j).expanduser() for j in jobsdir_list]
    app.config["_JOBSDIR_LIST"] = jobsdir_list

    return jobsdir_list


def ensure_jobsdir(app: Flask) -> None:
    jobsdir_list = get_jobsdir_list(app)
    app.extensions["bgclient"] = SimpleQueueClient(jobsdir_list[0])
    app.extensions["jobsmanager"] = create_jobs_manager(
        app,
        jobsdir_list,
    )
    app.jinja_env.globals["has_archive"] = len(jobsdir_list) > 1


def view_jobsdir(app: Flask) -> None:
    jobsdir_list = get_jobsdir_list(app)
    app.extensions["bgclient"] = SimpleQueueClient(jobsdir_list[0])
    app.extensions["jobsmanager"] = ViewJobsManager(
        jobsdir_list,
        sub_directories=0,
    )
    app.jinja_env.globals["has_archive"] = False
