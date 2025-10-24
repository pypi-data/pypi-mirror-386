"""
SPDX-License-Identifier: Apache-2.0
Copyright Contributors to the ODPi Egeria project.



This module is for testing the core Project Manager class and methods
The routines assume that pytest is being used as the test tool and framework.

A running Egeria environment is needed to run these tests.

"""

import json
import time
from pydantic import ValidationError
from pyegeria.project_manager import ProjectManager
from pyegeria.glossary_manager import GlossaryManager
from pyegeria._exceptions_new import PyegeriaException, print_basic_exception, print_exception_table, \
    print_validation_error, PyegeriaAPIException

from pyegeria import (
    InvalidParameterException,
    PropertyServerException,
    UserNotAuthorizedException,
    print_exception_response,
)

# from pyegeria.admin_services import FullServerConfig

disable_ssl_warnings = True


class TestProjectManager:
    good_platform1_url = "https://127.0.0.1:9443"
    good_platform2_url = "https://oak.local:9443"
    bad_platform1_url = "https://localhost:9443"

    # good_platform1_url = "https://127.0.0.1:30080"
    # good_platform2_url = "https://127.0.0.1:30081"
    # bad_platform1_url = "https://localhost:9443"

    good_user_1 = "garygeeke"
    good_user_2 = "erinoverview"
    good_user_3 = "peterprofile"
    bad_user_1 = "eviledna"
    bad_user_2 = ""
    good_integ_1 = "fluffy_integration"
    good_server_1 = "qs-metadata-store"
    good_server_2 = "laz_kv"
    good_server_3 = "active-metadata-store"
    good_server_4 = "integration-daemon"
    good_server_5 = "fluffy_kv"
    good_server_6 = "cocoVIew1"
    good_engine_host_1 = "governDL01"
    good_view_server_1 = "view-server"
    good_view_server_2 = "qs-view-server"
    bad_server_1 = "coco"
    bad_server_2 = ""

    def test_get_linked_projects(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_2,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )
            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            # parent_guid = "5d4a0b11-5552-4fe8-85e0-75d53e947cb7" # management
            # parent_guid = "994283c2-deaf-42dc-adf9-ce87cdee0d1f"
            # parent_guid = '4fe24e34-490a-43f0-a0d4-fe45ac45c663' # it setup
            parent_guid = '2d86e375-c31b-494d-9e73-a03af1370d81' # trial
            # parent_guid = "25452b45-942d-47af-90b6-3fa9df4a5df7"  # proj template
            response = p_client.get_linked_projects(parent_guid)
            duration = time.perf_counter() - start_time

            print(f"\n\tDuration was {duration} seconds")
            if type(response) is list:
                print("\n\n" + json.dumps(response, indent=4))
            elif type(response) is tuple:
                print(f"Type is {type(response)}")
                print("\n\n" + json.dumps(response, indent=4))
            elif type(response) is str:
                print("\n\nGUID is: " + response)
            assert True

        except (
            InvalidParameterException,
            PropertyServerException,
            UserNotAuthorizedException,
        ) as e:
            print_exception_response(e)
            assert False, "Invalid request"

        finally:
            p_client.close_session()

    def test_get_classified_projects(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_1,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )
            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            # parent_guid = "0fa16a37-5c61-44c1-85a0-e415c3cecb82"
            # classification = "RootCollection"
            classification = "GovernanceProject"
            response = p_client.get_classified_projects(classification)
            duration = time.perf_counter() - start_time

            print(f"\n\tDuration was {duration} seconds")
            print(f"response type is: {type(response)}")
            if type(response) is tuple:
                t = response[0]
                count = len(t)
                print(f"Found {count} projects {type(t)}\n\n")
                print(json.dumps(response, indent=4))
            elif type(response) is list:
                count = len(response)
                print(f"Found {count} projects\n\n")
                print(json.dumps(response, indent=4))
            elif type(response) is str:
                print("\n\n" + response)
            assert True

        except (
            InvalidParameterException,
            PropertyServerException,
            UserNotAuthorizedException,
        ) as e:
            print_exception_response(e)
            assert False, "Invalid request"

        finally:
            p_client.close_session()

    def test_find_projects(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_2,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )
            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            search_string = "*"

            response = p_client.find_projects(
                search_string, output_format="DICT", report_spec="Project"
            )
            duration = time.perf_counter() - start_time

            print(f"\n\tDuration was {duration} seconds")
            if type(response) is list:
                print(f"Found {len(response)} projects {type(response)}\n\n")
                print("\n\n" + json.dumps(response, indent=4))
            elif type(response) is str:
                print("\n\nGUID is: " + response)
            assert True

        except (
            PyegeriaException
        ) as e:
            print_basic_exception()
            assert False, "Invalid request"
        except ValidationError as e:
            print_validation_error(e)
        finally:
            p_client.close_session()

    def test_get_projects_by_name(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_2,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )
            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            # project_name = "Teddy Bear Drop Foot Clinical Trial IT Setup"
            project_name = "Second Task"
            response = p_client.get_projects_by_name(project_name)
            duration = time.perf_counter() - start_time

            print(f"\n\tDuration was {duration} seconds")
            if type(response) is list:
                print("\n\n" + json.dumps(response, indent=4))
            elif type(response) is tuple:
                print(f"Type is {type(response)}")
                print("\n\n" + json.dumps(response, indent=4))
            elif type(response) is str:
                print("\n\nResponse is: " + response)
            assert True

        except (
            InvalidParameterException,
            PropertyServerException,
            UserNotAuthorizedException,
        ) as e:
            print_exception_response(e)
            assert False, "Invalid request"

        finally:
            p_client.close_session()

    def test_get_classified_projects(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_2,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )
            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            project_classification = "Campaign"

            response = p_client.get_classified_projects(project_classification)
            duration = time.perf_counter() - start_time

            print(f"\n\tDuration was {duration} seconds")
            if type(response) is list:
                print(f"Type was list - found {len(response)} elements\n")
                print(json.dumps(response, indent=4))
            elif type(response) is tuple:
                print(f"Type is {type(response)}")
                print("\n\n" + json.dumps(response, indent=4))
            elif type(response) is str:
                print("\n\nGUID is: " + response)
            assert True

        except (
            PyegeriaException
        ) as e:
            print_basic_exception( e)
            assert False, "Invalid request"
        except ValidationError as e:
            print_validation_error(e)
        finally:
            p_client.close_session()

    def test_get_project_by_guid(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_2,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )
            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            project_guid = "79ec7de5-7367-4bde-a3c8-b8d8c582b521"

            response = p_client.get_project_by_guid(project_guid, output_format="DICT", report_spec="Projects")
            duration = time.perf_counter() - start_time

            print(f"\n\tDuration was {duration} seconds")
            print(f"Type of response is {type(response)}")

            if isinstance(response, list| dict):
                print("dict:\n\n")
                print(json.dumps(response, indent=4))
            elif type(response) is tuple:
                print(f"Type is {type(response)}\n\n")
                print(json.dumps(response, indent=4))
            elif type(response) is str:
                print("\n\nGUID is: " + response)
            assert True

        except (
            PyegeriaException, PyegeriaAPIException,
        ) as e:
            print_basic_exception(e)
            assert False, "Invalid request"

        finally:
            p_client.close_session()

    def test_get_project_graph(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_2,
                self.good_platform1_url,
                user_id=self.good_user_2,
                )
            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()

            project_guid = "79ec7de5-7367-4bde-a3c8-b8d8c582b521"

            response = p_client.get_project_graph(project_guid, output_format='DICT', report_spec='Project')
            duration = time.perf_counter() - start_time

            print(f"\n\tDuration was {duration} seconds")
            print(f"Type of response is {type(response)}")

            if type(response) is dict:
                print("dict:\n\n")
                print(json.dumps(response, indent=4))
            elif type(response) is list:
                print(f"Type is {type(response)}\n\n")
                print(json.dumps(response, indent=4))
            elif type(response) is str:
                print("\n\nGUID is: " + response)
            assert True

        except (
                InvalidParameterException,
                PropertyServerException,
                UserNotAuthorizedException,
                ) as e:
            print_exception_response(e)
            assert False, "Invalid request"

        finally:
            p_client.close_session()

    def test_create_project(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_2,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )

            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            classification_name = "PersonalProject"
            body = {
                "class": "NewElementRequestBody",
                "parentGUID": "79ec7de5-7367-4bde-a3c8-b8d8c582b521",
                "parentRelationshipTypeName": "ProjectHierarchy",
                "properties":{
                    "class": "ProjectProperties",
                    "name": "My Study Project",
                    "qualifiedName": f"{classification_name}-MyPersonalProject",
                    "description": "my first personal project",
                    "projectStatus": "DEFINED",
                    "startDate": "2021-01-01",
                    "plannedEndDate": "2028-01-01",
                    "initialClassifications" : {
                        "PersonalProject" : {
                          "class": "PersonalProjectProperties"
                        }
                    },
                },
            }
            response = p_client.create_project(body)
            duration = time.perf_counter() - start_time
            # resp_str = json.loads(response)
            print(f"\n\tDuration was {duration} seconds\n")
            if type(response) is dict:
                print(json.dumps(response, indent=4))
            elif type(response) is str:
                print("\n\nGUID is: " + response)
            assert True

        except (
            PyegeriaException,
        ) as e:
            print_basic_exception(e)
            assert False, "Invalid request"
        except ValidationError as e:
            print_validation_error(e)
        finally:
            p_client.close_session()

    def test_create_project_from_template(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_1,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )

            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            anchor_guid = None
            parent_guid = "97bbfe07-6696-4550-bf8b-6b577d25bef0"
            parent_relationship_type_name = "CollectionMembership"
            parent_at_end1 = True
            display_name = "Meow"
            description = "Meow"
            project_type = "Meow"
            is_own_anchor = False
            project_ordering = "NAME"
            order_property_name = None
            body = {
                "class": "TemplateRequestBody",
                "parentGUID": parent_guid,
                "parentRelationshipTypeName": parent_relationship_type_name,
                "parentAtEnd1": True,
                "templateGUID": "c7368217-d013-43cb-9af1-b58e3a491e77",
                "replacementProperties": {
                    "class": "ElementProperties",
                    "propertyValueMap": {
                        "qualifiedName": {
                            "class": "PrimitiveTypePropertyValue",
                            "typeName": "string",
                            "primitiveTypeCategory": "OM_PRIMITIVE_TYPE_STRING",
                            "primitiveValue": f"templated-{display_name}-{time.asctime()}",
                        },
                        "name": {
                            "class": "PrimitiveTypePropertyValue",
                            "typeName": "string",
                            "primitiveTypeCategory": "OM_PRIMITIVE_TYPE_STRING",
                            "primitiveValue": display_name,
                        },
                        "description": {
                            "class": "PrimitiveTypePropertyValue",
                            "typeName": "string",
                            "primitiveTypeCategory": "OM_PRIMITIVE_TYPE_STRING",
                            "primitiveValue": description,
                        },
                    },
                },
            }

            response = p_client.create_project_from_template(body)
            duration = time.perf_counter() - start_time
            # resp_str = json.loads(response)
            print(f"\n\tDuration was {duration} seconds\n")
            if type(response) is dict:
                print(json.dumps(response, indent=4))
            elif type(response) is str:
                print("\n\nGUID is: " + response)
            assert True

        except (
            InvalidParameterException,
            PropertyServerException,
            UserNotAuthorizedException,
        ) as e:
            print_exception_response(e)
            assert False, "Invalid request"
        finally:
            p_client.close_session()

    def test_update_project(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_1,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )

            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            project_guid = "7ab4f441-83e2-4e3f-8b63-2ed3946a5dd7"
            qualified_name = (
                "PersonalProject-First Child Project-Mon Apr 22 07:53:13 2024"
            )
            response = p_client.update_project(project_guid, project_status="Active")
            duration = time.perf_counter() - start_time
            # resp_str = json.loads(response)
            print(f"\n\tDuration was {duration} seconds\n")
            if type(response) is dict:
                print(json.dumps(response, indent=4))
            elif type(response) is str:
                print("\n\nGUID is: " + response)
            assert True

        except (
            InvalidParameterException,
            PropertyServerException,
            UserNotAuthorizedException,
        ) as e:
            print_exception_response(e)
            assert False, "Invalid request"
        finally:
            p_client.close_session()

    def test_delete_project(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_2,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )

            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            project_guid = "90213557-be19-421c-990d-78a76c30e0f5"

            response = p_client.delete_project(project_guid)
            duration = time.perf_counter() - start_time
            # resp_str = json.loads(response)
            print(f"\n\tDuration was {duration} seconds\n")
            print(f"Project GUID: {project_guid} was deleted")
            assert True

        except (
            PyegeriaException
        ) as e:
            print_basic_exception(e)
            assert False, "Invalid request"
        finally:
            p_client.close_session()

    def test_get_project_team(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_1,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )

            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            project_guid = "456cacde-a891-4e5a-bd3f-9fa0eeaa792c"

            response = p_client.get_project_team(project_guid)
            duration = time.perf_counter() - start_time
            # resp_str = json.loads(response)
            print(f"\n\tDuration was {duration} seconds\n")
            print(f"Result type is: {type(response)}")
            if type(response) is list:
                print(json.dumps(response, indent=4))
            elif type(response) is tuple:
                print(json.dumps(response, indent=4))
            elif type(response) is str:
                print("\n\nGUID is: " + response)
            assert True

        except (
            InvalidParameterException,
            PropertyServerException,
            UserNotAuthorizedException,
        ) as e:
            print_exception_response(e)
            assert False, "Invalid request"
        finally:
            p_client.close_session()

    def test_add_to_project_team(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_1,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )

            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            project_guid = "456cacde-a891-4e5a-bd3f-9fa0eeaa792c"
            actor_guid = "a588fb08-ae09-4415-bd5d-991882ceacba"

            p_client.add_to_project_team(project_guid, actor_guid)
            duration = time.perf_counter() - start_time
            # resp_str = json.loads(response)
            print(f"\n\tDuration was {duration} seconds\n")
            print("Added project member ")
            assert True

        except (
            InvalidParameterException,
            PropertyServerException,
            UserNotAuthorizedException,
        ) as e:
            print_exception_response(e)
            assert False, "Invalid request"
        finally:
            p_client.close_session()

    def test_remove_from_project_team(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_1,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )

            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            project_guid = "b9580bfb-c3dd-4c74-ae3d-3c4c4bf0b3ab"
            actor_guid = "a588fb08-ae09-4415-bd5d-991882ceacba"

            response = p_client.remove_from_project_team(project_guid, actor_guid)
            duration = time.perf_counter() - start_time
            # resp_str = json.loads(response)
            print(f"\n\tDuration was {duration} seconds\n")
            print(f"Removed project member {actor_guid}")
            assert True

        except (
            InvalidParameterException,
            PropertyServerException,
            UserNotAuthorizedException,
        ) as e:
            print_exception_response(e)
            assert False, "Invalid request"
        finally:
            p_client.close_session()

    def test_setup_proj_mgmt_role(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_1,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )

            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            project_guid = "be04abf9-9bd9-411a-b4a4-bbad682c5c35"
            prj_guid = "522f1b0a-9d44-43f5-a0ab-fc2e7487cfb7"

            response = p_client.setup_project_management_role(project_guid, prj_guid)
            duration = time.perf_counter() - start_time
            # resp_str = json.loads(response)
            print(f"\n\tDuration was {duration} seconds\n")
            print(f"Project manager role is  {prj_guid}")
            assert True

        except (
            InvalidParameterException,
            PropertyServerException,
            UserNotAuthorizedException,
        ) as e:
            print_exception_response(e)
            assert False, "Invalid request"
        finally:
            p_client.close_session()

    def test_clear_proj_mgmt_role(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_1,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )

            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            project_guid = "b9580bfb-c3dd-4c74-ae3d-3c4c4bf0b3ab"
            prj_guid = "522f1b0a-9d44-43f5-a0ab-fc2e7487cfb7"

            response = p_client.clear_project_management_role(project_guid, prj_guid)
            duration = time.perf_counter() - start_time
            # resp_str = json.loads(response)
            print(f"\n\tDuration was {duration} seconds\n")
            print(f"Project manager role  {prj_guid} was cleared.")
            assert True

        except (
            InvalidParameterException,
            PropertyServerException,
            UserNotAuthorizedException,
        ) as e:
            print_exception_response(e)
            assert False, "Invalid request"
        finally:
            p_client.close_session()

    def test_sustainability_sample_setup(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_1,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )

            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()

            # Create a Sustainability Campaign
            anchor_guid = None
            parent_guid = None
            parent_relationship_type_name = None
            parent_at_end1 = False
            display_name = "Sustainability Campaign"
            description = "This is the overall sustainability project"
            classification_name = "Campaign"
            identifier = "Sustainability-Master"
            is_own_anchor = True
            phase = "Define"
            status = "New"
            health = "Not Started"
            start_date = "2024-05-01"
            planned_end_date = "2025-04-01"

            response = p_client.create_project(
                anchor_guid,
                parent_guid,
                parent_relationship_type_name,
                parent_at_end1,
                display_name,
                description,
                classification_name,
                identifier,
                is_own_anchor,
                status,
                phase,
                health,
                start_date,
                planned_end_date,
            )
            campaign_guid = response

            # Now lets create some tasks
            # First a planning task
            parent_guid = campaign_guid
            display_name = "Plan Project"
            description = "Do the initial planning for the project"
            identifier = "Sustainability-Planning"
            phase = "Define"
            status = "New"
            health = "Not Started"
            start_date = "2024-05-01"
            planned_end_date = "2025-04-01"

            plan_task_guid = p_client.create_project_task(
                parent_guid,
                display_name,
                identifier,
                description,
                status,
                phase,
                health,
                start_date,
                planned_end_date,
            )
            print(f"\n\n created a task with guid {plan_task_guid}")

            # Now a task to set up a communications plan
            parent_guid = campaign_guid
            display_name = "Communications Plan"
            description = "Plan the project communications"
            identifier = "Sustainability-Planning"
            phase = "Define"
            status = "New"
            health = "Not Started"
            start_date = "2024-05-01"
            planned_end_date = "2025-04-01"

            comm_task_guid = p_client.create_project_task(
                parent_guid,
                display_name,
                identifier,
                description,
                status,
                phase,
                health,
                start_date,
                planned_end_date,
            )
            print(f"\n\n created a task with guid {comm_task_guid}")

            # Now a task to set up glossary to facilitate communications and understanding
            parent_guid = campaign_guid
            display_name = "Setup Glossary"
            description = "Setup a Sustainability Glossary"
            identifier = "Sustainability-Planning"
            phase = "Define"
            status = "New"
            health = "Not Started"
            start_date = "2024-05-01"
            planned_end_date = "2025-04-01"

            gloss_task_guid = p_client.create_project_task(
                parent_guid,
                display_name,
                identifier,
                description,
                status,
                phase,
                health,
                start_date,
                planned_end_date,
            )
            print(f"\n\n created a task with guid {gloss_task_guid}")

            assert True

        except (
            InvalidParameterException,
            PropertyServerException,
            UserNotAuthorizedException,
        ) as e:
            print_exception_response(e)
            assert False, "Invalid request"
        finally:
            p_client.close_session()

    def test_set_project_hierarchy(self):
        try:
            p_client = ProjectManager(
                self.good_view_server_2,
                self.good_platform1_url,
                user_id=self.good_user_2,
            )

            token = p_client.create_egeria_bearer_token(self.good_user_2, "secret")
            start_time = time.perf_counter()
            project_guid = "94b883bb-f3f7-49b4-ab0e-2a381fff5243"
            parent_project_guid = "8293b438-e43b-4bbb-a358-4683a3085b2d"
            body = {
                  "class" : "NewRelationshipRequestBody",
                  "properties": {
                        "class" : "ProjectDependencyProperties",
                        "description": "a desciption",

                        "label": "hierarchy label"
                        }
                }


            p_client.set_project_hierarchy(project_guid, parent_project_guid, body)
            duration = time.perf_counter() - start_time
            # resp_str = json.loads(response)
            print(f"\n\tDuration was {duration} seconds\n")
            print("Added project link ")
            assert True

        except (
            PyegeriaException
        ) as e:
            print_basic_exception(e)
            assert False, "Invalid request"
        finally:
            p_client.close_session()


