"""
SPDX-License-Identifier: Apache-2.0
Copyright Contributors to the ODPi Egeria project.



This script refreshed an integration daemon.

"""

import os

import click
from loguru import logger
from pyegeria import EgeriaTech, PyegeriaAPIException
from pyegeria.config import settings
from pyegeria.logging_configuration import config_logging
from pyegeria._exceptions_new import (
PyegeriaException, print_exception_response, print_basic_exception
)

# EGERIA_METADATA_STORE = os.environ.get("EGERIA_METADATA_STORE", "active-metadata-store")
# EGERIA_KAFKA_ENDPOINT = os.environ.get("KAFKA_ENDPOINT", "localhost:9092")
# EGERIA_PLATFORM_URL = os.environ.get("EGERIA_PLATFORM_URL", "https://localhost:9443")
# EGERIA_VIEW_SERVER = os.environ.get("EGERIA_VIEW_SERVER", "view-server")
# EGERIA_VIEW_SERVER_URL = os.environ.get(
#     "EGERIA_VIEW_SERVER_URL", "https://localhost:9443"
# )
# EGERIA_INTEGRATION_DAEMON = os.environ.get("EGERIA_INTEGRATION_DAEMON", "integration-daemon")
# EGERIA_INTEGRATION_DAEMON_URL = os.environ.get(
#     "EGERIA_INTEGRATION_DAEMON_URL", "https://localhost:9443"
# )



EGERIA_USER = os.environ.get("EGERIA_USER", "erinoverview")
EGERIA_USER_PASSWORD = os.environ.get("EGERIA_USER_PASSWORD", "secret")
app_settings = settings
app_config = app_settings.Environment
config_logging()


@click.command("load-archive")
@click.option(
    "--file_name",
    default="content-packs/CocoComboArchive.omarchive",
    help="Full path on the Metadata Server to the archive file to load",
)
@click.option(
    "--server_name", default=app_config.egeria_metadata_store, help="Egeria metadata store to load"
)
@click.option(
    "--view-server", default=app_config.egeria_view_server, help="Egeria view server to connect to"
)
@click.option(
    "--url", default=app_config.egeria_platform_url, help="URL of Egeria platform to connect to"
)
@click.option("--userid", default=EGERIA_USER, help="Egeria admin user")
@click.option("--password", default=EGERIA_USER_PASSWORD, help="Egeria admin password")
@click.option("--timeout", default=120, help="Number of seconds to wait")
def load_archive(file_name, server_name, view_server, url, userid, password, timeout):
    """Load an Open Metadata Archive"""

    try:
        s_client = EgeriaTech(view_server, url, userid, password)
        token = s_client.create_egeria_bearer_token()
        server_guid = s_client.__get_guid__(display_name = server_name, property_name = "displayName", tech_type = "MetadataStore")
        file_name = file_name.strip()
        s_client.add_archive_file(file_name, server_guid, server_name, time_out=timeout)

        click.echo(f"Loaded archive: {file_name}")

    except (PyegeriaException, PyegeriaAPIException) as e:
        print(
            f"Perhaps there was a timeout? If so, the command will complete despite the exception\n"
            f"===> You can check by rerunning the command in a few minutes"
        )
        print_basic_exception(e)


if __name__ == "__main__":
    load_archive()
