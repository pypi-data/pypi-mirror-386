# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from pathlib import Path
from typing import List

import pandas as pd

from polaris.runs.results.h5_results import H5_Results
from polaris.utils.database.db_utils import read_sql


class TransitDemandMetrics:
    """Loads all data required for the computation of demand metrics and
    creates permanent tables with statistics in the demand database.

    The behavior of time filtering consists of setting to instant zero
    whenever *from_time* is not provided and the end of simulation when
    *to_time* is not provided"""

    def __init__(self, supply_file: Path, result_h5: Path):
        """
        :param supply_file: Path to the supply file corresponding to the demand file we will compute metrics for
        :param h5_file: Path to the H5 result file we want to compute metrics for
        """

        self.__base_table = None
        self.__trip_load = None
        self.__zone_data = None
        self.__result_h5 = result_h5
        self.__supply_file = supply_file

        self.tables: List[str] = []
        self.__stop_data = pd.DataFrame([])
        self.__boardings = pd.DataFrame([])
        self.__alightings = pd.DataFrame([])

        self.__list_tables()

    @staticmethod
    def list_stop_metrics() -> list:
        """Returns list of metrics available for stops"""
        return [
            "alightings",
            "pax_hour_for_alighted",
            "pax_km_for_alighted",
            "boardings",
            "pax_hour_for_boarded",
            "pax_km_for_boarded",
        ]

    @staticmethod
    def list_pattern_metrics() -> list:
        """Returns list of metrics available for patterns"""
        return ["total_boardings", "maximum_load", "most_boardings_trip", "most_crowded_trip"]

    @staticmethod
    def list_route_metrics() -> list:
        """Returns list of metrics available for routes"""
        return ["total_boardings", "maximum_load", "most_boardings_trip", "most_crowded_trip"]

    @staticmethod
    def list_zone_metrics() -> list:
        """Returns list of metrics available for traffic analysis zones"""
        return [
            "alightings",
            "boardings",
            "alightings_per_1000_pop",
            "boardings_per_1000_pop",
            "alightings_per_1000_jobs",
            "boardings_per_1000_jobs",
            "pax_hour_for_alighted",
            "pax_km_for_alighted",
            "pax_hour_for_boarded",
            "pax_km_for_boarded",
        ]

    def stop_metrics(
        self, from_minute=None, to_minute=None, agency_id=None, stops=None, patterns=None, routes=None
    ) -> pd.DataFrame:
        """
        Computes boardings and alightings at each stop. Allows constraining to a given time interval,
            set of routes, set of patterns and/or Transit Agency.

            All parameters are optional.

        :param from_minute: Start of the interval for computation. Zero if not provided
        :param to_minute: End of the interval for computation. Maximum time from the dataset if not provided
        :param agency_id: The ID of the agency we want to filter for
        :param stops: List of stops we want to compute data for
        :param patterns: List of pattern_id to consider in the computation
        :param routes: List of route_id to consider in the computation
        :return: Statistics DataFrame
        """

        return self.__stop_zone_metric_generation(
            from_minute=from_minute,
            to_minute=to_minute,
            agency_id=agency_id,
            stops=stops,
            patterns=patterns,
            routes=routes,
            aggregation="stop_id",
        )

    def zone_metrics(
        self, from_minute=None, to_minute=None, agency_id=None, stops=None, patterns=None, routes=None
    ) -> pd.DataFrame:
        """
        Computes boardings and alightings for all stop within each zone. Allows constraining to a given
        time interval, set of routes, set of patterns and/or Transit Agency.

            All parameters are optional.

        :param from_minute: Start of the interval for computation. Zero if not provided
        :param to_minute: End of the interval for computation. Maximum time from the dataset if not provided
        :param agency_id: The ID of the agency we want to filter for
        :param stops: List of stops we want to compute data for
        :param patterns: List of pattern_id to consider in the computation
        :param routes: List of route_id to consider in the computation
        :return: Statistics DataFrame
        """
        self.__get_zonal_data()
        df = self.__stop_zone_metric_generation(
            from_minute=from_minute,
            to_minute=to_minute,
            agency_id=agency_id,
            stops=stops,
            patterns=patterns,
            routes=routes,
            aggregation="zone",
        )
        df.set_index(["zone"], inplace=True)
        df = df.join(self.__zone_data, how="left")
        df = df.assign(
            alightings_per_1000_pop=1000 * df.alightings / df.popu,
            alightings_per_1000_jobs=1000 * df.alightings / df.empl,
            boardings_per_1000_pop=1000 * df.alightings / df.popu,
            boardings_per_1000_jobs=1000 * df.alightings / df.empl,
        )
        return df.drop(columns=["popu", "empl"])

    def __get_table_if_exists(self, tbl_name, overwrite):
        if not overwrite:
            if tbl_name in H5_Results(self.__result_h5).list_groups():
                return pd.read_hdf(self.__result_h5, f"/{tbl_name}")
        return pd.DataFrame([])

    def compute_stop_to_stop_matrix(self, overwrite=False):
        """Builds tables on demand database with the summary statistics for boardings and alightings.
        If table exists, loads the data into a DataFrame

        :param overwrite: `Optional`. Overwrites cached summary tables if they exist. Defaults to **False**"""

        tbl_name = "qgs_stop_to_stop_matrix"
        df = self.__get_table_if_exists(tbl_name, overwrite)
        if not df.empty:
            self.__stop_data = df
            return

        transit_stops = read_sql("select stop_id, zone from Transit_Stops", self.__supply_file)

        self.__get_base_table()
        gpb = self.__base_table.groupby("object_id")
        frt = gpb.first()[["from_node", "from_time", "agency_id", "pattern_id", "route_id"]]
        frt.columns = ["from_stop", "from_minute", "from_agency_id", "from_pattern_id", "from_route_id"]

        lst = gpb.last()[["to_node", "to_time", "agency_id", "pattern_id", "route_id"]]
        lst.columns = ["to_stop", "to_minute", "to_agency_id", "to_pattern_id", "to_route_id"]

        sm = gpb.sum()[["vadt", "distance"]]
        sm.columns = ["pax_hour", "pax_km"]
        sm.loc[:, "pax_hour"] /= 3600
        sm.loc[:, "pax_km"] /= 1000

        stop_data = frt.join(lst).join(sm)
        transit_stops.columns = ["from_stop", "from_zone"]
        stop_data = stop_data.merge(transit_stops, on="from_stop")

        transit_stops.columns = ["to_stop", "to_zone"]
        self.__stop_data = stop_data.merge(transit_stops, on="to_stop")

        self.__stop_data.to_hdf(self.__result_h5, key=f"/{tbl_name}", index=False, format="table")

        self.__list_tables()

    def route_metrics(
        self, from_minute=None, to_minute=None, agency_id=None, patterns=None, routes=None
    ) -> pd.DataFrame:
        """Computes several metrics for transit routes, indexed by route_id. Allows constraining
            the analysis to a given time interval, set of routes, set of patterns and/or Transit Agency.
            *It does NOT allow for filtering by stops*

        :param from_minute: Start of the interval for computation. Zero if not provided
        :param to_minute: End of the interval for computation. Maximum time from the dataset if not provided
        :param agency_id: The ID of the agency we want to filter for
        :param patterns: List of pattern_id to consider in the computation
        :param routes: List of route_id to consider in the computation
        :return: Statistics DataFrame
        """
        return self.__line_metrics("route_id", from_minute, to_minute, agency_id, patterns, routes)

    def pattern_metrics(
        self, from_minute=None, to_minute=None, agency_id=None, patterns=None, routes=None
    ) -> pd.DataFrame:
        """Computes several metrics for transit patterns, indexed by pattern_id. Allows constraining
            the analysis to a given time interval, set of routes, set of patterns and/or Transit Agency.
            *It does NOT allow for filtering by stops*

        :param from_minute: Start of the interval for computation. Zero if not provided
        :param to_minute: End of the interval for computation. Maximum time from the dataset if not provided
        :param agency_id: The ID of the agency we want to filter for
        :param patterns: List of pattern_id to consider in the computation
        :param routes: List of route_id to consider in the computation
        :return: Statistics DataFrame
        """
        return self.__line_metrics("pattern_id", from_minute, to_minute, agency_id, patterns, routes)

    def compute_line_loads(self, overwrite=False):
        """Builds tables on demand database with the summary statistics for line loads.
        If table exists, loads the data into a DataFrame.

        :param overwrite: `Optional`. Overwrites cached summary table if it exists. Defaults to **False**
        """

        tbl_name = "qgs_journeys_on_transit"
        df = self.__get_table_if_exists(tbl_name, overwrite)
        if not df.empty:
            self.__trip_load = df
            return

        self.__get_base_table()
        gpb = self.__base_table.groupby(["object_id", "trip_id"])

        self.__trip_load = gpb.agg(
            {
                "pattern_id": "first",
                "route_id": "first",
                "agency_id": "first",
                "from_time": "first",
                "to_time": "last",
            }
        ).reset_index()
        self.__trip_load.to_hdf(self.__result_h5, key=f"/{tbl_name}", index=False)

        self.__list_tables()

    def __line_metrics(self, metric, from_minute, to_minute, agency_id, patterns, routes):
        self.compute_line_loads()
        base_data = self.__trip_load
        if not all([from_minute is None, to_minute is None]):
            fm = 0 if from_minute is None else from_minute
            tm = base_data.to_time.max() if to_minute is None else to_minute
            base_data = base_data.loc[~(tm < base_data.from_time), :]
            base_data = base_data.loc[~(fm > base_data.to_time), :]

        if agency_id is not None:
            base_data = base_data[base_data.agency_id == agency_id]

        if patterns is not None:
            base_data = base_data[base_data.pattern_id.isin(patterns) | base_data.pattern_id.astype(str).isin(patterns)]

        if routes is not None:
            base_data = base_data[base_data.route_id.isin(routes) | base_data.route_id.astype(str).isin(routes)]

        boards = base_data[["agency_id", "route_id", "pattern_id", "trip_id", "from_time"]].assign(action=1)
        boards.rename(columns={"from_time": "instant"}, inplace=True)
        alights = base_data[["agency_id", "route_id", "pattern_id", "trip_id", "to_time"]].assign(action=-1)
        alights.rename(columns={"to_time": "instant"}, inplace=True)
        loads = pd.concat([boards, alights])

        route_loads = loads[[metric, "instant", "action"]].sort_values(by=[metric, "instant"])
        route_loads = route_loads.assign(load=route_loads.groupby(metric)["action"].cumsum())
        route_loads = route_loads.groupby([metric, "instant"]).max()[["load"]].reset_index()
        route_loads.drop(columns=["instant"], inplace=True)
        route_loads = route_loads.groupby(metric).max()
        route_loads.columns = ["maximum_load"]

        busiest_trip = loads[[metric, "trip_id", "instant", "action"]].sort_values(by=["trip_id", "instant"])
        busiest_trip = busiest_trip.assign(most_crowded_trip=busiest_trip.groupby("trip_id")["action"].cumsum())
        busiest_trip = busiest_trip.groupby([metric]).max()[["most_crowded_trip"]]

        most_boardings = (
            base_data[["trip_id", "pattern_id", "route_id", "from_time"]].groupby(["trip_id", metric]).count()
        )
        most_boardings = most_boardings.reset_index().groupby(metric).max()[["from_time"]]
        most_boardings.columns = ["most_boardings_trip"]

        boards = base_data[["route_id", "pattern_id"]].groupby(metric).count()
        boards.columns = ["total_boardings"]

        return route_loads.join(boards).join(busiest_trip).join(most_boardings).reset_index()

    def __stop_zone_metric_generation(
        self,
        from_minute=None,
        to_minute=None,
        agency_id=None,
        aggregation="stop_id",
        stops=None,
        patterns=None,
        routes=None,
    ):
        self.compute_stop_to_stop_matrix()
        base_data = self.__stop_data.assign(pax_count=1)
        if self.__boardings.empty:
            gpb = base_data.groupby(
                ["from_stop", "from_minute", "from_agency_id", "from_zone", "from_pattern_id", "from_route_id"]
            )
            self.__boardings = gpb.sum()[["pax_hour", "pax_km", "pax_count"]].reset_index()
            self.__boardings.rename(
                columns={
                    "from_agency_id": "agency_id",
                    "from_stop": "stop_id",
                    "from_minute": "boarding_minute",
                    "from_zone": "zone",
                    "from_pattern_id": "pattern_id",
                    "from_route_id": "route_id",
                },
                inplace=True,
            )

            gpb = base_data.groupby(["to_stop", "to_minute", "to_agency_id", "to_zone", "to_pattern_id", "to_route_id"])
            self.__alightings = gpb.sum()[["pax_hour", "pax_km", "pax_count"]].reset_index()
            self.__alightings.rename(
                columns={
                    "to_agency_id": "agency_id",
                    "to_stop": "stop_id",
                    "to_minute": "alighting_minute",
                    "to_zone": "zone",
                    "to_pattern_id": "pattern_id",
                    "to_route_id": "route_id",
                },
                inplace=True,
            )

        board = self.__boardings
        alight = self.__alightings
        if not all([from_minute is None, to_minute is None]):
            fm = 0 if from_minute is None else from_minute
            tm = max(alight.alighting_minute.max(), board.boarding_minute.max()) if to_minute is None else to_minute
            board = board.loc[(board.boarding_minute > fm) & (board.boarding_minute < tm)]
            alight = alight.loc[(alight.alighting_minute > fm) & (alight.alighting_minute < tm)]

        if stops is not None:
            board = board.loc[board.stop_id.isin(stops)]
            alight = alight.loc[alight.stop_id.isin(stops)]

        if patterns is not None:
            board = board.loc[board.pattern_id.isin(patterns)]
            alight = alight.loc[alight.pattern_id.isin(patterns)]

        if routes is not None:
            board = board.loc[board.route_id.isin(routes)]
            alight = alight.loc[alight.route_id.isin(routes)]

        if agency_id is not None:
            board = board.loc[board.agency_id == agency_id]
            alight = alight.loc[alight.agency_id == agency_id]

        alight = alight.groupby(aggregation).sum()[["pax_count", "pax_hour", "pax_km"]]
        board = board.groupby(aggregation).sum()[["pax_count", "pax_hour", "pax_km"]]

        alight.columns = ["alightings", "pax_hour_for_alighted", "pax_km_for_alighted"]
        board.columns = ["boardings", "pax_hour_for_boarded", "pax_km_for_boarded"]
        return alight.join(board).fillna(0).reset_index()

    def __get_zonal_data(self):
        if self.__zone_data is not None:
            return
        self.__zone_data = read_sql(
            "Select zone, pop_persons popu, employment_total empl from Zone", self.__supply_file, index_col="zone"
        )

    def __get_base_table(self):
        if self.__base_table is not None:
            return

        qry = """SELECT tl.transit_link, tl.from_node, tl.to_node, "index" "order",  tl.pattern_id, tp.route_id,
                        tr.agency_id, tl.length distance
                            FROM Transit_Links tl
                            INNER JOIN transit_patterns tp ON tl.pattern_id=tp.pattern_id
                            INNER JOIN transit_pattern_links tpl ON tl.transit_link=tpl.transit_link
                            INNER JOIN transit_Routes tr ON tp.route_id=tr.route_id"""

        trans_links = read_sql(qry, self.__supply_file)

        h5_res = H5_Results(self.__result_h5)

        df = pd.concat([h5_res.get_path_mm_links_for_timestep(ts) for ts in h5_res.timesteps])
        df = df.rename(
            columns={
                "path_id": "object_id",
                "transit_vehicle_trip_id": "trip_id",
                "link_id": "transit_link",
                "act_arrival_time": "vaat",
                "act_travel_time": "vadt",
            }
        ).query("trip_id >= 0")

        df = df[["object_id", "trip_id", "transit_link", "vaat", "vadt"]]

        df = df.assign(from_time=(df.vaat / 60).astype(int), to_time=((0.5 + df.vaat + df.vadt) / 60).astype(int))

        self.__base_table = df.merge(trans_links, on="transit_link")
        self.__base_table.sort_values(by=["object_id", "vaat"], inplace=True)

    def __list_tables(self):
        if self.__result_h5 is None:
            return

        h5_res = H5_Results(self.__result_h5)
        self.tables = h5_res.list_groups()
