# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import logging
import os
import re
import subprocess
import sys
from math import floor
from pathlib import Path
from time import sleep
from typing import Optional

import pandas as pd
from polaris.utils.copy_utils import magic_copy


def run_tail_application(tail_app, results_dir):
    file_to_tail = results_dir / "simulation_out.log"
    if "linux" in sys.platform:
        print("Running linux tail app: %s %s" % (tail_app, file_to_tail))
        return subprocess.Popen([tail_app, str(file_to_tail)], shell=True)
    elif "windows" in sys.platform:
        print("Running windows tail app: %s %s" % (tail_app, file_to_tail))
        return subprocess.Popen([tail_app, str(file_to_tail)])

    print("Unable to start tail application: %s %s" % (tail_app, file_to_tail))
    return None


def copy_replace_file(filename, dest_dir):
    if not filename.exists():
        logging.warning(f"File {filename} does not exist. Skipping copy back")
        return
    dest_file = Path(dest_dir / Path(filename).name)
    dest_file.unlink(missing_ok=True)
    magic_copy(str(filename), str(dest_file), recursive=False)


def get_dir_size(dirpath: Path) -> int:
    size = 0
    for path, dirs, files in os.walk(dirpath):
        for f in files:
            fp = os.path.join(path, f)
            size += os.stat(fp).st_size
    return size


def is_finished_copying(dirpath: Path) -> bool:
    size_then = get_dir_size(dirpath)
    sleep(2)
    size_now = get_dir_size(dirpath)
    return size_then == size_now


def get_latest_polaris_output(data_dir, db_name):
    all_subdirs = all_subdirs_of(data_dir, db_name)
    if len(all_subdirs) == 0:
        return None
    return Path(max(all_subdirs, key=os.path.getmtime))


def all_subdirs_of(root_dir: Path, starts_with=None):
    filter = lambda x: x.stem.startswith(starts_with) if starts_with else lambda _: True
    return [p for p in root_dir.iterdir() if p.is_dir() and filter(p)]


def get_output_dirs(config):
    return all_subdirs_of(config.data_dir, config.db_name)


def get_output_dir_index(directory):
    m = re.search("([0-9]+)$", str(directory))
    return int(m[1]) if m else 0


def merge_csvs(config: "ConvergenceConfig", csv_name: Path, out_name: Optional[Path] = None, save_merged: bool = True):
    files = [d / csv_name for d in get_output_dirs(config)]
    files = sorted([f for f in files if f.exists()], key=os.path.getmtime)
    if len(files) == 0:
        msg = f"Couldn't find any {csv_name} files in sub-directories of {config.data_dir}"
        logging.error(msg)
        raise RuntimeError(msg)

    def f(csv_file):
        return pd.read_csv(csv_file).assign(directory=csv_file.parent.stem)

    df = pd.concat([f(x) for x in files])
    out_name = out_name if out_name is not None else csv_name
    if save_merged:
        df.to_csv(config.data_dir / out_name, index=False)
    return df.set_index("directory")


DURATION_PATTERN = r"duration:\s*(\d+):(\d+):(\d+)"


def parse_main_loop_duration(output_dir, log_file=None):
    log_file = log_file or Path(output_dir) / "log" / "polaris_progress.log"
    with open(log_file, "r") as f:
        lines = [re.search(DURATION_PATTERN, l.strip()) for l in f.readlines()]
    matches = [l for l in lines if l]
    if len(matches) > 1:
        logging.warning("Multiple timers found, using the last one")
    if len(matches) < 1:
        logging.warning("Couldn't find a duration timer")
        return -1
    m = matches[-1]
    return 3600 * int(m[1]) + 60 * int(m[2]) + int(m[3])


def parse_git_sha(output_dir):
    log_file = Path(output_dir) / "log" / "polaris_progress.log"
    with open(log_file, "r") as f:
        # find the start of the argument listing
        line = f.readline()
        while line is not None and "arguments" not in line:
            line = f.readline()

        # find how many args there are and read that many lines
        num_args = int(re.match(".*There are ([0-9]) arguments.*", line)[1])
        lines = [f.readline().strip() for _ in range(0, num_args)]

        # replace \ with / to allow parsing of files generated on windows in linux - this is required for tests
        exe = lines[0].split(" ")[-1]
        json = lines[1].split(" ")[-1]
        json = str(Path(json.replace("\\", os.sep)).name)

        return exe, json


def parse_exe_and_json(output_dir):
    log_file = Path(output_dir) / "log" / "polaris_progress.log"
    with open(log_file, "r") as f:
        # find the start of the argument listing
        line = f.readline()
        while line is not None and "arguments" not in line:
            line = f.readline()

        # find how many args there are and read that many lines
        num_args = int(re.match(".*There are ([0-9]) arguments.*", line)[1])
        lines = [f.readline().strip() for _ in range(0, num_args)]

        # replace \ with / to allow parsing of files generated on windows in linux - this is required for tests
        exe = lines[0].split(" ")[-1]
        json = lines[1].split(" ")[-1]
        json = str(Path(json.replace("\\", os.sep)).name)

        return exe, json


def seconds_to_str(seconds):
    d = floor(seconds / 86400)
    h = floor((seconds % 86400) / 3600)
    m = floor((seconds % 3600) / 60)
    s = round(seconds % 60)
    d = "" if d == 0 else f"{d}-"
    return f"{d}{h:>02}:{m:>02}:{s:>02}"
