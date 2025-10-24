#!/usr/bin/env python3
"""
SPDX-License-Identifier: Apache-2.0
Copyright Contributors to the ODPi Egeria project.

Display the status of cataloged platforms and servers.
"""

import argparse
import os
import sys
import time

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.table import Table

from pyegeria import RuntimeManager
from pyegeria._exceptions import (
    InvalidParameterException,
    PropertyServerException,
    UserNotAuthorizedException,
    print_exception_response,
)

EGERIA_METADATA_STORE = os.environ.get("EGERIA_METADATA_STORE", "active-metadata-store")
EGERIA_KAFKA_ENDPOINT = os.environ.get("KAFKA_ENDPOINT", "localhost:9092")
EGERIA_PLATFORM_URL = os.environ.get("EGERIA_PLATFORM_URL", "https://localhost:9443")
EGERIA_VIEW_SERVER = os.environ.get("EGERIA_VIEW_SERVER", "view-server")
EGERIA_VIEW_SERVER_URL = os.environ.get(
    "EGERIA_VIEW_SERVER_URL", "https://localhost:9443"
)
EGERIA_INTEGRATION_DAEMON = os.environ.get("EGERIA_INTEGRATION_DAEMON", "integration-daemon")
EGERIA_INTEGRATION_DAEMON_URL = os.environ.get(
    "EGERIA_INTEGRATION_DAEMON_URL", "https://localhost:9443"
)
EGERIA_ADMIN_USER = os.environ.get("ADMIN_USER", "garygeeke")
EGERIA_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "secret")
EGERIA_USER = os.environ.get("EGERIA_USER", "erinoverview")
EGERIA_USER_PASSWORD = os.environ.get("EGERIA_USER_PASSWORD", "secret")
EGERIA_JUPYTER = bool(os.environ.get("EGERIA_JUPYTER", "False"))
EGERIA_WIDTH = int(os.environ.get("EGERIA_WIDTH", "200"))

disable_ssl_warnings = True
console = Console(width=EGERIA_WIDTH)


def display_status(
    view_server: str = EGERIA_VIEW_SERVER,
    view_url: str = EGERIA_VIEW_SERVER_URL,
    user: str = EGERIA_USER,
    user_pass: str = EGERIA_USER_PASSWORD,
    jupyter: bool = EGERIA_JUPYTER,
    width: int = EGERIA_WIDTH,
):
    r_client = RuntimeManager(view_server, view_url, user)
    token = r_client.create_egeria_bearer_token(user, user_pass)

    def generate_table() -> Table:
        """Make a new table."""
        table = Table(
            title=f"Server Status for Platform - {time.asctime()}",
            # style="bold white on black",
            row_styles=["bold white on black"],
            header_style="white on dark_blue",
            title_style="bold white on black",
            caption_style="white on black",
            caption=f"Status of Platforms - '{view_url}'",
            show_lines=True,
            # expand=True
        )
        table.add_column("Platform Name & GUID")
        # table.add_column("Platform GUID")
        table.add_column("Platform URL")
        table.add_column("Platform Origin")
        table.add_column("Description")
        table.add_column("Platform Started")
        table.add_column("Servers")

        server_types = {
            "Metadata Access Store": "Store",
            "View Server": "View",
            "Engine Host Server": "EngineHost",
            "Integration Daemon": "Integration",
        }
        try:
            platform_list = r_client.get_platforms_by_type()
            if type(platform_list) is str:
                print("No OMAG Server Platforms found?")
                sys.exit(1)

            for platform in platform_list:
                platform_name = platform["properties"].get("displayName", "---")
                platform_guid = platform["elementHeader"]["guid"]
                platform_desc = platform["properties"].get("resourceDescription", "---")
                server_list = ""

                platform_report = r_client.get_platform_report(platform_guid)
                platform_url = platform_report.get("platformURLRoot", " ")
                platform_origin = platform_report.get("platformOrigin", " ")
                platform_build = platform_report.get("platformBuildProperties", " ")
                platform_build_md = ""
                if type(platform_build) is dict:
                    for prop in platform_build:
                        platform_build_md = (
                            f"{platform_build_md}\n* {prop}: {platform_build[prop]}"
                        )
                    platform_build_out = Markdown(platform_build_md)
                else:
                    platform_build_out = platform_origin
                platform_desc = f"{platform_desc}\n\n\t\t&\n\n{platform_build}"
                platform_started = platform_report.get("platformStartTime", " ")
                platform_id = f"{platform_name}\n\n\t\t&\n\n{platform_guid}"

                servers = platform_report.get("omagservers", None)

                if servers is not None:
                    for server in servers:
                        server_name = server.get("serverName", " ")
                        server_type = server.get("serverType", " ")
                        server_status = server.get("serverActiveStatus", "UNKNOWN")
                        if server_status in ("RUNNING", "STARTING"):
                            status_flag = "[bright green]"
                        elif server_status in ("INACTIVE", "STOPPING"):
                            status_flag = "[bright red]"
                        else:
                            server_status = "UNKNOWN"
                            status_flag = "[bright yellow]"

                        server_list += (
                            f"{status_flag}{server_types[server_type]}: {server_name}\n"
                        )

                    table.add_row(
                        platform_id,
                        platform_url,
                        platform_build_out,
                        platform_desc,
                        platform_started,
                        server_list,
                        style="bold white on black",
                    )

        except Exception as e:
            # console.print_exception(e)
            platform_url = " "
            platform_origin = " "
            platform_started = " "
        token = r_client.refresh_egeria_bearer_token()
        return table

    try:
        with Live(generate_table(), refresh_per_second=4, screen=True) as live:
            while True:
                time.sleep(2)
                live.update(generate_table())

    except (
        InvalidParameterException,
        PropertyServerException,
        UserNotAuthorizedException,
    ) as e:
        print_exception_response(e)

    except KeyboardInterrupt:
        pass
    finally:
        r_client.close_session()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", help="Name of the server to display status for")
    parser.add_argument("--url", help="URL Platform to connect to")
    parser.add_argument("--userid", help="User Id")
    parser.add_argument("--password", help="User Password")
    args = parser.parse_args()

    server = args.server if args.server is not None else EGERIA_VIEW_SERVER
    url = args.url if args.url is not None else EGERIA_PLATFORM_URL
    userid = args.userid if args.userid is not None else EGERIA_USER
    user_pass = args.password if args.password is not None else EGERIA_USER_PASSWORD

    display_status(server, url, userid, user_pass)


if __name__ == "__main__":
    main()
