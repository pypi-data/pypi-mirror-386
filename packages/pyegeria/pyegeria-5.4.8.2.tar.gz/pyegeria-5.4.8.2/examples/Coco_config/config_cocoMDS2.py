"""
SPDX-License-Identifier: Apache-2.0
Copyright Contributors to the ODPi Egeria project.



Egeria Coco Pharmaceutical demonstration labs.

This script creates and configures the cocoMDS2 - Governance metadata server


"""

import json

from globals import (
    cocoCohort,
    cocoMDS2Name,
    corePlatformURL,
    devCohort,
    iotCohort,
    max_paging_size,
)

from pyegeria import CoreServerConfig, Platform, print_exception_response

disable_ssl_warnings = True

mdr_server = cocoMDS2Name
platform_url = corePlatformURL
admin_user = "garygeeke"
mdr_server_user_id = "cocoMDS2npa"
mdr_server_password = "cocoMDS2passw0rd"
metadataCollectionId = f"{mdr_server}-e915f2fa-aa3g-4396-8bde-bcd65e642b1d"
metadataCollectionName = "Governance Catalog"

print("Configuring " + mdr_server + "...")

try:
    o_client = CoreServerConfig(mdr_server, platform_url, admin_user)

    o_client.set_basic_server_properties(
        "Governance Server",
        "Coco Pharmaceuticals",
        platform_url,
        mdr_server_user_id,
        mdr_server_password,
        max_paging_size,
    )

    #   Inherit event bus config

    event_bus_config = {
        "producer": {"bootstrap.servers": "{{kafkaEndpoint}}"},
        "consumer": {"bootstrap.servers": "{{kafkaEndpoint}}"},
    }

    o_client.set_event_bus(event_bus_config)

    security_connection_body = {
        "class": "Connection",
        "connectorType": {
            "class": "ConnectorType",
            "connectorProviderClassName": "org.odpi.openmetadata.metadatasecurity.samples.CocoPharmaServerSecurityProvider",
        },
    }

    o_client.set_server_security_connection(security_connection_body)
    o_client.add_default_log_destinations()

    # o_client.set_in_mem_local_repository()
    # o_client.set_xtdb_local_kv_repository()
    body = {
        "xtdbConfigEDN": """{:xtdb/index-store {:kv-store {:xtdb/module xtdb.rocksdb/->kv-store :db-dir "data/servers/xtdb/rdb-index"}}
                                                :xtdb.lucene/lucene-store {:db-dir "data/servers/xtdb/lucene"
                                                                             :indexer {:xtdb/module xtdb.lucene.egeria/->egeria-indexer}
                                                                             :analyzer {:xtdb/module xtdb.lucene.egeria/->ci-analyzer}}
                                                  :xtdb.jdbc/connection-pool {:dialect {:xtdb/module xtdb.jdbc.psql/->dialect}
                                                                              :db-spec {:jdbcUrl "jdbc:postgresql://host.docker.internal:5442/xtdb?user=postgres&password=egeria"}}
                                                  :xtdb/tx-log {:xtdb/module xtdb.jdbc/->tx-log
                                                                :connection-pool :xtdb.jdbc/connection-pool
                                                                :poll-sleep-duration "PT1S"}
                                                  :xtdb/document-store {:xtdb/module xtdb.jdbc/->document-store
                                                                        :connection-pool :xtdb.jdbc/connection-pool}}""",
        "syncIndex": True,
    }
    o_client.add_startup_open_metadata_archive_file(
        "content-packs/CoreContentPack.omarchive"
    )
    o_client.set_xtdb_local_repository(body)
    o_client.set_local_metadata_collection_id(metadataCollectionId)
    o_client.set_local_metadata_collection_name(metadataCollectionName)

    o_client.add_cohort_registration(cocoCohort)
    o_client.add_cohort_registration(devCohort)
    o_client.add_cohort_registration(iotCohort)

    print(f"Configuring {mdr_server}  Access Services (OMAS)....")

    # o_client.configure_access_service("asset-catalog", {})
    o_client.configure_access_service("asset-consumer", {})

    o_client.configure_access_service("asset-owner", {})
    o_client.configure_access_service("community-profile", {"KarmaPointPlateau": "500"})
    # o_client.configure_access_service("glossary-view", {})
    # o_client.configure_access_service("subject-area", {})
    o_client.configure_access_service("governance-engine", {})
    o_client.configure_access_service("governance-server", {})
    o_client.configure_access_service("governance-program", {})
    # o_client.configure_access_service("data-privacy", {})
    o_client.configure_access_service("digital-architecture", {})
    # o_client.configure_access_service("security-manager", {})
    # o_client.configure_access_service("asset-lineage", {})
    # o_client.configure_access_service("it-infrastructure", {})
    # o_client.configure_access_service("project-management", {})

    p_client = Platform(mdr_server, platform_url, admin_user)
    p_client.activate_server_stored_config()

    print(f"\n\n\tConfiguration of {mdr_server} is complete.")

    config = o_client.get_stored_configuration()
    print(f"The server stored configuration is \n{json.dumps(config, indent=4)}")

except Exception as e:
    print_exception_response(e)
