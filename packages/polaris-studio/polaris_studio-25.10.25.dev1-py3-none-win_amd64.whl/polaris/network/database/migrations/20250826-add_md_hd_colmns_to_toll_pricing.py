# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from polaris.network.create.triggers import recreate_network_triggers
from polaris.utils.database.db_utils import add_column_unless_exists


def migrate(conn):
    add_column_unless_exists(conn, "Toll_Pricing", "md_price", "INTEGER")
    add_column_unless_exists(conn, "Toll_Pricing", "hd_price", "INTEGER")

    recreate_network_triggers(conn)
