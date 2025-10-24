"""
SPDX-License-Identifier: Apache-2.0
Copyright Contributors to the ODPi Egeria project.



pyegeria md_commands available also from python.
"""
from .cat.dr_egeria_md import process_markdown_file
from .cat.list_deployed_catalogs import list_deployed_catalogs
from .cat.list_deployed_database_schemas import list_deployed_database_schemas
from .cat.list_deployed_databases import list_deployed_databases
from .cat.list_glossaries import display_glossaries
from .cat.list_terms import display_glossary_terms
from .ops.list_catalog_targets import display_catalog_targets
from .ops.monitor_engine_activity_c import display_engine_activity_c
from .ops.monitor_gov_eng_status import display_gov_eng_status
from .ops.monitor_integ_daemon_status import display_integration_daemon_status
from .ops.table_integ_daemon_status import (
    display_integration_daemon_status as table_integ_daemon_status,
)
from .tech.list_elements_by_property_value import EGERIA_WIDTH


def list_integration_daemon_status(
    search_list: str, width: int = EGERIA_WIDTH, sort: bool = True
):
    table_integ_daemon_status(
        search_list=search_list, paging=True, width=width, sort=sort
    )
