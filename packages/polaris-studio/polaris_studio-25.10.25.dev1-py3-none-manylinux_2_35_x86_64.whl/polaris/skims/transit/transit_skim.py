# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from os import PathLike
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import openmatrix as omx
import pandas as pd
from polaris.skims.transit.export_transit_omx import export_transit_omx
from polaris.skims.utils.basic_skim import SkimBase

INFINITE_TRANSIT = 1.7895698e07


class TransitSkim(SkimBase):
    """Polaris Transit Skim class

    ::

        from polaris.skims import TransitSkim

        skims = TransitSkim()

        # Load skims for highway
        skims.open('path/to/pt/skims')

        # We can retrieve skims
        # The keys are not not case-sensitive
        bus_time_morning = skims.get_skims(interval=240, metric="time", mode="bus")

        # to get the metrics and modes available you can do
        skims.modes
        # or
        skims.metrics

        # We can also export it
        skims.export('path/to/omx/file.omx')
    """

    prefix = "transit"

    def __init__(self, filename: Optional[str] = None):
        SkimBase.__init__(self)
        self._infinite = INFINITE_TRANSIT
        self.modes = ["BUS", "RAIL", "PARK_AND_RIDE", "PARK_AND_RAIL", "RIDE_AND_UNPARK", "TNC_AND_RIDE"]
        self.metrics = ["time", "walk_access_time", "auto_access_time", "wait_time", "transfers", "fare"]
        self.__data: Dict[str, Dict[str, Dict[int, np.ndarray]]] = {}
        self.bus_only = False
        if filename is not None:
            self.open(Path(filename))

    def open(self, path_to_file: PathLike):
        """Loads the transit skim data

        Args:
            *path_to_file* (:obj:`str`): Full file path to the transit skim

        """
        if str(Path(path_to_file).suffix).lower() != ".omx":
            url = "https://git-out.gss.anl.gov/polaris/code/polaristools"
            raise ValueError(f"bin format is no longer supported. For conversion to OMX check  {url}")

        infile = omx.open_file(path_to_file)
        self.index = pd.DataFrame(infile.mapping("taz").items(), columns=["zones", "index"])
        intervals = set()
        for m in infile.list_matrices():
            matrix = infile[m]
            if any(attr not in matrix.attrs for attr in ["metric", "mode", "timeperiod"]):
                continue

            metr = matrix.attrs["metric"].astype(str)
            if metr not in self.__data:
                self.__data[metr] = {}
            mode = matrix.attrs["mode"].astype(str)
            if mode not in self.__data[metr]:
                self.__data[metr][mode] = {}
            inter = int(matrix.attrs["timeperiod"].astype(str))
            intervals.add(inter)
            m_ = np.array(matrix)
            m_[m_ >= INFINITE_TRANSIT] = np.inf
            self.__data[metr][mode][inter] = m_
        self.intervals = sorted(intervals)
        infile.close()

    def get_skims(self, interval=None, metric=None, mode=None):
        """Gets skim data for specified mode/interval/metric.  These filters are not, however, required.
        If one or more parameters it not provided, a dictionary (or nested dictionaries) will be returned

        Args:
            *interval* `Optional` (:obj:`int`): The time interval of interest
            *metric* `Optional` (:obj:`str`): Metric
            *mode* `Optional` (:obj:`str`): name of the transport mode

        """
        res = self.__data

        if interval:
            res = {mt: {md: res[mt][md][interval] for md in self.modes} for mt in self.metrics}
        if mode:
            res = {mt: res[mt][mode.upper()] for mt in self.metrics}

        if metric:
            res = res[metric.lower()]

        return res

    def create_empty(self, intervals: list, zones: int):
        """Creates a new skim data cube for a given set of intervals and number of zones.
           All matrices are filled with zeros

        Args:
            *intervals* (:obj:`list`): List of all intervals this skim file should have
            *zones* (:obj:`int`): Number of zones for this skim
        """

        self.index = pd.DataFrame({"zones": 1 + np.arange(zones), "index": np.arange(zones)})
        self.intervals = sorted(intervals)

        for metr in self.metrics:
            self.__data[metr] = {}
            for md in self.modes:
                self.__data[metr][md] = {}
                for interv in self.intervals:
                    self.__data[metr][md][interv] = np.zeros((zones, zones), dtype="f")

    def remove_interval(self, interval: int):
        """Removes one interval from this skim. Operation happens in memory only. It does NOT alter skim on disk

            Args:
        *interval* (:obj:`int`): Interval to remove from the skim
        """
        if interval not in self.intervals:
            raise ValueError(f"Interval {interval} does not exist")

        for metr in self.metrics:
            for md in self.modes:
                del self.__data[metr][md][interval]
        self.intervals.remove(interval)

    def add_interval(self, interval: int, copy_interval=None):
        """Adds a new interval to the skim matrix

        Args:
            *interval* (:obj:`int`): Interval to be added to the skim data cube
            *copy_interval* `Optional` (:obj:`int`): Interval to be copied into the new interval. Arrays of zeros
            are added is not provided
        """
        copy_from = copy_interval or self.intervals[0]
        if copy_from not in self.intervals:
            raise ValueError(f"Interval {copy_from} does not exist")

        if interval in self.intervals:
            raise ValueError(f"Interval {interval} already exists int the skim data cube")

        for metr in self.metrics:
            for md in self.modes:
                dct = self.__data[metr][md]
                data = np.zeros_like(dct[copy_from]) if copy_interval is None else np.array(dct[copy_from])
                dct[interval] = data

        self.intervals = sorted(self.intervals + [interval])

    def add_mode(self, mode_name: str, copy_mode: str):
        """Adds a new mode to the skim matrix

        Args:
            *mode_name* (:obj:`str`): Mode name to be added to the skim data cube
            *copy_mode* `Optional` (:obj:`str`):copy_mode to be copied into the new mode. Arrays of zeros
            are added if not provided
        """
        copy_from = copy_mode or self.modes[0]
        if copy_from not in self.modes:
            raise ValueError(f"Mode {copy_from} does not exist")

        if mode_name in self.modes:
            raise ValueError(f"Mode {mode_name} already exists int the skim data cube")

        for metr in self.metrics:
            for interv in self.intervals:
                dct = self.__data[metr]
                data = np.zeros_like(dct[copy_mode][interv]) if copy_mode is None else np.array(dct[copy_from][interv])
                if mode_name not in dct:
                    dct[mode_name] = {}
                self.__data[metr][mode_name][interv] = data

        self.modes.append(mode_name)

    def add_metric(self, metric: str, copy_metric: str):
        """Adds a new metric to the skim matrix

        Args:
            *metric* (:obj:`str`): Metric to be added to the skim data cube
            *copy_metric* `Optional` (:obj:`str`): metric to be copied into the new metric. Arrays of zeros
            are added if not provided
        """
        copy_from = copy_metric.lower() or self.metrics[0]
        if copy_from not in self.metrics:
            raise ValueError(f"Metric {copy_from} does not exist")

        new_metric = metric.lower()
        if new_metric in self.metrics:
            raise ValueError(f"Metric {metric} already exists int the skim data cube")

        self.__data[new_metric] = {}
        for md in self.modes:
            self.__data[new_metric][md] = {}
            for interv in self.intervals:
                data = np.zeros_like(self.__data[copy_metric][md][interv]) if copy_metric is None else None
                self.__data[new_metric][md][interv] = data or np.array(self.__data[copy_from][md][interv])

        self.metrics.append(new_metric)

    def write_to_file(self, path_to_file: PathLike):
        if Path(path_to_file).exists():
            raise FileExistsError("Cannot overwrite OMX file")
        export_transit_omx(self.get_skims(), path_to_file, self.modes, self.metrics, self.index, self.intervals)
