from __future__ import annotations

import os
import random
import shutil
import signal
import string
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterator
from typing import NamedTuple
from typing import Sequence
from typing import TypedDict

from flask import abort
from flask import current_app
from flask import has_app_context
from protein_turnover.exts import RESULT_EXT
from protein_turnover.jobs import slugify
from protein_turnover.jobs import TurnoverJob
from protein_turnover.resourcefiles import hash256
from protein_turnover.utils import decompressto
from typing_extensions import override


# IS_WIN = sys.platform == "win32"

if sys.platform == "win32":
    KILLSIG = signal.CTRL_C_EVENT
else:
    KILLSIG = signal.SIGINT


# CFG = ".turnover-layout.cfg"

# this has to form both a filename (on case preserving filesystems)
# *and* a url
ALPHABET = string.ascii_lowercase + string.digits


def create_short_jobid(n: int = 7) -> str:
    return "".join(random.choices(ALPHABET, k=n))


def chop(prefix: str, max_length: int) -> str:
    # take letters from front and back of string
    # to a maximum of max_length
    if len(prefix) > max_length:
        s = prefix[: (max_length * 2) // 3]
        e = max_length - len(s)
        prefix = s + prefix[-e:]
    return prefix


# def url_to_path(dataid: str) -> str:  # pragma: no cover
#     # if IS_WIN:
#     #     return dataid.replace("/", "\\")
#     return dataid


# def path_to_url(path: str) -> str:  # pragma: no cover
#     if IS_WIN:
#         return path.replace("\\", "/")
#     return path


class JobDir(NamedTuple):
    jobsdir: Path
    dir_index: int
    stat_files: bool


class Locator:
    """Given a dataid and a root jobsdir locate all files for this dataid"""

    def __init__(self, jobid: str, manager: JobsManager, dir_index: int):
        self.jobid = jobid
        self.manager = manager
        self.dir_index = dir_index

    def stem(self) -> str:
        return self.manager.stem(self.jobid)

    def locate_data_file(self) -> Path:
        # *** important function! ***
        # given a dataid find the sqlite file
        return self.locate_directory().joinpath(f"{self.stem()}{RESULT_EXT}")

    def locate_log_file(self) -> Path:
        return self.locate_directory().joinpath(f"{self.stem()}.log")

    def locate_config_file(self) -> Path:
        return self.locate_directory().joinpath(f"{self.stem()}.toml")

    def locate_pid_file(self) -> Path:
        return self.locate_directory().joinpath(f"{self.stem()}.toml.pid")

    def locate_all_files(self) -> list[Path]:
        return [
            self.locate_pid_file(),
            self.locate_config_file(),
            self.locate_data_file(),
            self.locate_log_file(),
        ]

    def locate_directory(self) -> Path:
        return self.manager.locate_directory(self.jobid, self.dir_index)

    def is_in_use(self) -> bool:
        return self.locate_directory().exists()

    def kill_pid(self) -> str | None:
        pidfile = self.locate_pid_file()
        if not pidfile.exists():
            return f"job {self.jobid} not running"

        try:  # pragma: no cover
            with pidfile.open() as fp:
                pid = int(fp.read())
            os.kill(pid, KILLSIG)
        except (
            TypeError,
            OSError,
            PermissionError,
            ProcessLookupError,
        ):  # pragma: no cover
            return f"no such job: {self.jobid}"
        return None  # pragma: no cover

    def remove(self) -> bool:
        directory = self.locate_directory()
        if not directory.exists():
            return False
        shutil.rmtree(directory)
        return True

    def remove_all_files(self) -> None:  # pragma: no cover
        for f in self.locate_all_files():
            try:
                f.unlink(missing_ok=True)
            except OSError:
                pass


def check_path(dataid: str, root: Path) -> tuple[Path, bool]:
    """dataid is from the web, root is from us (so trusted)"""

    dataid = dataid + ".toml"
    if ".." in dataid:
        return Path(dataid), False
    jobfile = Path(dataid)
    if jobfile.is_absolute():
        return jobfile, False

    jobfile = root / jobfile
    # if jobfile is a symlink then resolve could jump any where
    jobfile = jobfile.absolute()
    if not jobfile.relative_to(root):
        return jobfile, False

    return jobfile, True


class ViewLocator(Locator):
    def __init__(self, jobid: str, manager: JobsManager, dir_index: int):
        """dataid is an encoded file path from the web (so untrustworthy!)"""

        # dataid = url_to_path(dataid)
        jobfile, ok = check_path(
            jobid,
            manager.jobsdir_list[dir_index].jobsdir,
        )
        if not ok:  # pragma: no cover
            self.bad_file(jobfile)
        if jobfile.exists():
            job = TurnoverJob.restore(jobfile)
            jobid = job.jobid

        super().__init__(jobid, manager, dir_index)
        self.jobfile = jobfile

    def bad_file(self, jobfile: Path) -> None:
        current_app.logger.error("bad dataid: %s", jobfile)
        abort(404)

    @override
    def locate_directory(self) -> Path:
        return self.jobfile.parent

    @override
    def locate_config_file(self) -> Path:
        return self.jobfile

    @override
    def is_in_use(self) -> bool:
        return self.jobfile.exists()

    @override
    def remove(self) -> bool:
        self.remove_all_files()
        return True


class TurnoverJobFiles(NamedTuple):
    # found a job file i.e. a recognised
    # .toml file with a dataid .etc
    # NB: note that dataid is used to by the website to
    # map data to files using => dataid  =>  dataid[:2]/dataid/ datadir
    # see Locator
    job: TurnoverJob
    directory: Path
    name: str  # filename of jobfile
    # full_path: str
    mtime: datetime
    size: int | None = None
    is_running: bool = False
    has_result: bool = False
    dir_index: int = 0

    @property
    def status(self) -> str:
        if self.is_running:
            return "running"
        return self.job.status or "stopped"

    @property
    def dataid(self) -> str:
        return jobid_to_data_url(self.job.jobid, self.dir_index)


# class PersonalJobFiles(TurnoverJobFiles):
#     @property
#     @override
#     def dataid(self) -> str:
#         """Use full path as dataid"""
#         path = path_to_url(self.full_path)
#         return jobid_to_data_url(path, self.dir_index)


class Jobs(TypedDict):
    running: list[TurnoverJobFiles]
    queued: list[TurnoverJobFiles]
    finished: list[TurnoverJobFiles]


class Decompressor:
    def __init__(self, gzfile: Path, cache_dir: Path):
        self.cache_dir = cache_dir.absolute()
        self.gzfile = gzfile
        self.decompressed_link = gzfile.with_suffix("")
        self._is_symlink = self.decompressed_link.is_symlink()

        self._target: Path | None = None

    def hash(self) -> str:
        return hash256(self.gzfile)

    @property
    def target(self) -> Path:
        if self._target is None:
            if self._is_symlink:
                self._target = self.decompressed_link.resolve()
            else:
                self._target = self.cache_dir / (self.hash() + RESULT_EXT)
        return self._target

    def maybe_decompress(self) -> Path:
        tgt = self.target
        if not tgt.exists():
            if has_app_context():
                current_app.logger.debug("decompressing: %s", self.gzfile)
            # try and stop race conditions
            # tgt.touch()
            decompressto(self.gzfile, tgt)
            if not self._is_symlink:
                try:
                    # possible race condition here
                    self.decompressed_link.symlink_to(tgt)
                    self._is_symlink = True
                except OSError:  # pragma: no cover
                    pass
        return tgt

    def remove_decompressed(self) -> None:
        # remove underlying file
        self.target.unlink(missing_ok=True)


class Finder:
    TurnoverJobFilesClass: type[TurnoverJobFiles] = TurnoverJobFiles

    def _data_from_jobfile(
        self,
        jobfile: Path,
        dinfo: JobDir,
        *,
        use_jobid: bool = True,
        compressed: bool = True,
    ) -> TurnoverJobFiles | None:
        # needs to be quick
        try:
            job = TurnoverJob.restore(jobfile)
        except (TypeError, UnicodeDecodeError, ValueError) as e:  # pragma: no cover
            current_app.logger.error("can't open: %s, reason: %s", jobfile, e)
            return None
        # TODO: tomlfile -> sqlite... convention
        directory = jobfile.parent
        stem = job.jobid if use_jobid else jobfile.stem
        data = directory.joinpath(stem + RESULT_EXT)
        if compressed:
            data = data.with_suffix(data.suffix + ".gz")

        if dinfo.stat_files:
            # has_result = data.exists()
            # if not has_result and compressed:
            #     # try compressed version
            #     data = data.with_suffix(data.suffix + ".gz")
            has_result = data.exists()
            st = data.stat() if has_result else jobfile.stat()
            is_running = directory.joinpath(jobfile.name + ".pid").exists()
        else:  # pragma: no cover
            # we probably have the sqlite files on a slow network file system so
            # stating etc. will be slow (see ./bin/mkmirror.py)
            has_result = True  # we assume!
            st = jobfile.stat()  # jobfile is local
            is_running = False

        # def full_path() -> str:
        #     return str(directory.relative_to(dinfo.jobsdir) / jobfile.stem)

        return self.TurnoverJobFilesClass(
            job=job,
            directory=directory,
            name=jobfile.name,
            mtime=datetime.fromtimestamp(st.st_mtime),
            size=st.st_size if dinfo.stat_files else 0,
            is_running=is_running,
            has_result=has_result,
            # full_path=full_path(),
            dir_index=dinfo.dir_index,
        )

    def _find_all_jobs(self, dinfo: JobDir) -> Iterator[TurnoverJobFiles]:
        from .inspect import is_compressed

        compressed = is_compressed()
        for d, _, files in dinfo.jobsdir.walk():
            for f in files:
                if f.endswith(".toml"):
                    ret = self._data_from_jobfile(
                        d.joinpath(f),
                        dinfo,
                        compressed=compressed,
                    )
                    if ret is None:  # pragma: no cover
                        continue
                    yield ret

    def find_job_files(self, jobsdir_list: Sequence[JobDir]) -> Jobs:
        # Maybe turn this into a database?

        running: list[TurnoverJobFiles] = []
        finished: list[TurnoverJobFiles] = []
        queued: list[TurnoverJobFiles] = []
        for dinfo in jobsdir_list:
            for r in self._find_all_jobs(dinfo):
                if r.status == "running":
                    target = running
                elif r.status == "pending":
                    target = queued
                else:  # stopped or failed
                    target = finished
                target.append(r)

        def bymtime(t: TurnoverJobFiles) -> datetime:
            return t.mtime

        return Jobs(
            running=sorted(running, key=bymtime, reverse=False),
            queued=sorted(queued, key=bymtime, reverse=False),  # oldest first
            finished=sorted(finished, key=bymtime, reverse=True),  # newest first
        )


# class ViewFinder(Finder):
#     TurnoverJobFilesClass = PersonalJobFiles
#     """use full_path as dataid"""


def data_url_to_jobid(data_url: str) -> tuple[int, str] | None:
    if "---" not in data_url:
        return 0, data_url
    n, jobid = data_url.split("---", maxsplit=1)
    if not n.isdigit():
        return None
    return int(n), jobid


def jobid_to_data_url(dataid: str | Path, dir_index: int = 0) -> str:
    if dir_index == 0:
        return str(dataid)
    return f"{dir_index}---{dataid}"


class JobsManager:
    LocatorClass: type[Locator] = Locator
    FinderClass: type[Finder] = Finder

    def __init__(
        self,
        jobsdir_list: Sequence[Path],
        *,
        check_dir: bool = True,
        sub_directories: int = 2,
        max_length: int = 20,
        stat_files: int = -1,
    ):
        self.check_dir = check_dir
        self.sub_directories = sub_directories
        self.max_length = max_length
        # self.stat_files = stat_files
        s = stat_files < 0
        self.jobsdir_list: list[JobDir] = [
            JobDir(job, idx, s or idx <= stat_files)
            for idx, job in enumerate(jobsdir_list)
        ]

    def find_all_jobs(self) -> Jobs:
        return self.FinderClass().find_job_files(self.jobsdir_list)

    def find_current_jobs(self) -> Jobs:
        return self.FinderClass().find_job_files(self.jobsdir_list[:1])

    def find_archive_jobs(self) -> Jobs:
        return self.FinderClass().find_job_files(self.jobsdir_list[1:])

    def locate_from_url(self, data_url: str) -> Locator:
        res = data_url_to_jobid(data_url)
        if res is None:  # pragma: no cover
            abort(404)
        dir_index, jobid = res

        return self.LocatorClass(
            jobid,
            self,
            dir_index,
        )

    def locate_from_new(self, jobid: str) -> Locator:
        return self.LocatorClass(
            jobid,
            self,
            0,
        )

    def stem(self, jobid: str) -> str:  # pragma: no cover
        return jobid

    def locate_directory(self, jobid: str, dir_index: int) -> Path:
        jobsdir = self.jobsdir_list[dir_index].jobsdir
        if self.sub_directories <= 0:  # pragma: no cover
            return jobsdir.joinpath(jobid)
        return jobsdir.joinpath(jobid[: self.sub_directories], jobid)

    def jobid_from_jobname(self, jobname: str, ext: int = 7) -> str:
        jobname = chop(slugify(jobname), self.max_length)
        # pad out with random string
        # ext = self.max_length - len(prefix) + ext
        jobid = jobname + "-" + self._create_short_jobid(ext)
        if self.check_dir:
            locate = self.locate_from_new(jobid)
            while locate.is_in_use():  # pragma: no cover
                jobid = jobname + "-" + self._create_short_jobid(ext)
                locate = self.locate_from_new(jobid)
        return jobid

    @classmethod
    def _create_short_jobid(cls, n: int = 7) -> str:
        return create_short_jobid(n)

    # @classmethod
    # def read_cfg(cls, cfg: Path) -> tuple[int, int] | None:
    #     try:
    #         with cfg.open(encoding="utf8") as fp:
    #             method, sub_directories = map(int, fp.read().strip().split(","))
    #             return method, sub_directories
    #     except Exception:  # pragma: no cover
    #         return None

    # def write_config(self) -> None:
    #     jobsdir = self.jobsdir_list[0][0]
    #     cfg = jobsdir / CFG
    #     with cfg.open("wt", encoding="utf8") as fp:
    #         fp.write(f"0,{self.sub_directories}")

    # def check_config(self) -> bool:
    #     """Returns False is there is a prexisting layout"""
    #     jobsdir = self.jobsdir_list[0][0]
    #     cfg = jobsdir / CFG
    #     if cfg.exists():
    #         ret = self.read_cfg(cfg)
    #         if ret is not None:
    #             self.sub_directories = ret[1]
    #         return False

    #     return True


class ViewJobsManager(JobsManager):
    LocatorClass: type[Locator] = ViewLocator
    # FinderClass: type[Finder] = ViewFinder
