"""PDX-License-Identifier: Apache-2.0
Copyright Contributors to the ODPi Egeria project.

This module provides access to the data-designer OMVS module.

[data-designer](https://egeria-project.org/services/omvs/data-designer/overview)

"""

import asyncio

from loguru import logger

from pyegeria._client_new import max_paging_size, Client2
from pyegeria.base_report_formats import select_report_spec, get_report_spec_match
from pyegeria.models import (SearchStringRequestBody, FilterRequestBody, GetRequestBody, NewElementRequestBody,
                             TemplateRequestBody,
                             UpdateElementRequestBody, NewRelationshipRequestBody,
                             DeleteElementRequestBody, DeleteRelationshipRequestBody)
from pyegeria.output_formatter import (extract_mermaid_only, extract_basic_dict, populate_columns_from_properties,
                                       get_required_relationships, populate_common_columns)
from pyegeria.output_formatter import (generate_output,
                                       _extract_referenceable_properties)
from pyegeria.utils import body_slimmer, dynamic_catch


def query_seperator(current_string):
    if current_string == "":
        return "?"
    else:
        return "&"


# ("params are in the form of [(paramName, value), (param2Name, value)] if the value is not None, it will be added to "
# "the query string")


def query_string(params):
    result = ""
    for i in range(len(params)):
        if params[i][1] is not None:
            result = f"{result}{query_seperator(result)}{params[i][0]}={params[i][1]}"
    return result


def base_path(client, view_server: str):
    return f"{client.platform_url}/servers/{view_server}/api/open-metadata/data-designer"


class DataDesigner(Client2):
    """DataDesigner is a class that extends the Client class. The Data Designer OMVS provides APIs for
      building specifications for data. This includes common data fields in a data dictionary, data specifications
      for a project and data classes for data quality validation.
    """

    def __init__(self, view_server_name: str, platform_url: str, user_id: str = None, user_pwd: str = None,
                 token: str = None, ):
        self.view_server = view_server_name
        self.platform_url = platform_url
        self.user_id = user_id
        self.user_pwd = user_pwd
        self.data_designer_root: str = (
            f"{self.platform_url}/servers/{self.view_server}/api/open-metadata/data-designer")
        Client2.__init__(self, view_server_name, platform_url, user_id=user_id, user_pwd=user_pwd, token=token, )

    #
    #    Data Structures
    #
    @dynamic_catch
    async def _async_create_data_structure(self, body: dict | NewElementRequestBody) -> str:
        """
        Create a new data structure from a provided dict body. Async version.

        Parameters
        ----------
        body : dict | NewElementRequestBody
            - a dictionary or NewElementRequestBody object containing the data structure details

        Returns
        -------
        str
            The GUID of the element - or "No element found"

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Notes
        -----
        Sample body:
        {
          "class" : "NewElementRequestBody",
          "anchorGUID" : "add guid here",
          "isOwnAnchor": false,
          "parentGUID": "add guid here",
          "parentRelationshipTypeName": "add type name here",
          "parentRelationshipProperties": {
            "class": "RelationshipElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "parentAtEnd1": false,
          "properties": {
            "class" : "DataStructureProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "description": "add description here",
            "namespace": "add namespace for this structure",
            "versionIdentifier": "add version for this structure",
            "additionalProperties": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            },
            "effectiveFrom": "{{$isoTimestamp}}",
            "effectiveTo": "{{$isoTimestamp}}"
          },
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false
        }

        """

        url = f"{base_path(self, self.view_server)}/data-structures"

        return await self._async_create_element_body_request(url, "DataStructure", body)

    @dynamic_catch
    def create_data_structure(self, body: dict | NewElementRequestBody) -> str:
        """
        Create a new data structure from a provided dict body.

        Parameters
        ----------
        body : dict | NewElementRequestBody
            - a dictionary or NewElementRequestBody object containing the data structure details

        Returns
        -------
        str
            The GUID of the element - or "No element found"

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Notes
        -----
        Sample body:
        {
          "class" : "NewElementRequestBody",
          "anchorGUID" : "add guid here",
          "isOwnAnchor": false,
          "parentGUID": "add guid here",
          "parentRelationshipTypeName": "add type name here",
          "parentRelationshipProperties": {
            "class": "RelationshipElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "parentAtEnd1": false,
          "properties": {
            "class" : "DataStructureProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "description": "add description here",
            "namespace": "add namespace for this structure",
            "versionIdentifier": "add version for this structure",
            "additionalProperties": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            },
            "effectiveFrom": "{{$isoTimestamp}}",
            "effectiveTo": "{{$isoTimestamp}}"
          },
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false
        }

        """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self._async_create_data_structure(body))
        return response

    @dynamic_catch
    async def _async_create_data_structure_from_template(self, body: dict | TemplateRequestBody) -> str:
        """
        Create a new metadata element to represent a data structure using an existing metadata element as a template.
        The template defines additional classifications and relationships that should be added to the new element.
        Async version.

        Parameters
        ----------
        body: dict
            - a dictionary containing the properties of the data structure to be created.

        Returns
        -------
        str
            The GUID of the element - or "No element found"

        Raises
        ------
        PyegeriaException

        ValidationError


        Note
        ----

        Full sample body:

        {
          "class" : "TemplateRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "anchorGUID" : "add guid here",
          "isOwnAnchor": false,
          "parentGUID": "add guid here",
          "parentRelationshipTypeName": "add type name here",
          "parentRelationshipProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "parentAtEnd1": false,
          "templateGUID": "add guid here",
          "replacementProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "placeholderPropertyValues":  {
            "placeholder1" : "propertyValue1",
            "placeholder2" : "propertyValue2"
          }
        }

        """
        url = f"{self.data_designer_root}/data-structures/from-template"
        return await self._async_create_element_from_template(url, body)

    @dynamic_catch
    def create_data_structure_from_template(self, body: dict | TemplateRequestBody) -> str:
        """
        Create a new metadata element to represent a data structure using an existing metadata element as a template.
        The template defines additional classifications and relationships that should be added to the new element.

        Parameters
        ----------
        body: dict
            - a dictionary containing the properties of the data structure to be created.

        Returns
        -------
        str
            The GUID of the element - or "No element found"

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:

        {
          "class" : "TemplateRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "anchorGUID" : "add guid here",
          "isOwnAnchor": false,
          "parentGUID": "add guid here",
          "parentRelationshipTypeName": "add type name here",
          "parentRelationshipProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "parentAtEnd1": false,
          "templateGUID": "add guid here",
          "replacementProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "placeholderPropertyValues":  {
            "placeholder1" : "propertyValue1",
            "placeholder2" : "propertyValue2"
          }
        }

        """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._async_create_data_structure_from_template(body))
        return response

    @dynamic_catch
    async def _async_update_data_structure(self, data_struct_guid: str, body: dict | UpdateElementRequestBody) -> None:
        """
        Update the properties of a data structure. Async version.

        Parameters
        ----------
        data_struct_guid: str
            - the GUID of the data structure to be updated.
        body: dict
            - a dictionary containing the properties of the data structure to be created.

        Returns
        -------
        None

        Raises
        ------
        PyegeriaException

        ValidationError

        Note
        ----
        Full sample body:
        {
          "class" : "UpdateElementRequestBody",
          "mergeUpdate": true,
          "properties": {
            "class" : "DataStructureProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "description": "add description here",
            "namespace": "add namespace for this structure",
            "versionIdentifier": "add version for this structure",
            "additionalProperties": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            },
            "effectiveFrom": "{{$isoTimestamp}}",
            "effectiveTo": "{{$isoTimestamp}}"
          },
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false
        }

        """

        url = f"{base_path(self, self.view_server)}/data-structures/{data_struct_guid}/update"
        await self._async_update_element_body_request(url, ["DataStructure"], body)
        logger.info(f"Data structure {data_struct_guid} updated.")

    @dynamic_catch
    def update_data_structure(self, data_struct_guid: str, body: dict | UpdateElementRequestBody) -> None:
        """
        Update the properties of a data structure.

        Parameters
        ----------
        data_struct_guid: str
            - the GUID of the data structure to be updated.
        body: dict
            - a dictionary containing the properties of the data structure to be created.

        Returns
        -------
        None

        Raises
        ------
        PyegeriaException

        ValidationError

        Note
        ----
        Full sample body:
        {
          "class" : "UpdateElementRequestBody",
          "mergeUpdate": true,
          "properties": {
            "class" : "DataStructureProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "description": "add description here",
            "namespace": "add namespace for this structure",
            "versionIdentifier": "add version for this structure",
            "additionalProperties": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            },
            "effectiveFrom": "{{$isoTimestamp}}",
            "effectiveTo": "{{$isoTimestamp}}"
          },
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false
        }

        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self._async_update_data_structure(data_struct_guid, body))

    @dynamic_catch
    async def _async_link_member_data_field(self, parent_data_struct_guid: str, member_data_field_guid: str,
                                            body: dict | NewRelationshipRequestBody = None) -> None:
        """
        Connect a data structure to a data field. Async version.

        Parameters
        ----------
        parent_data_struct_guid: str
            - the GUID of the parent data structure the data class will be connected to.
        member_data_field_guid: str
            - the GUID of the data class to be connected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:
        {
          "class" : "NewRelationshipRequestBody",
          "properties": {
            "class": "MemberDataFieldProperties",
            "dataFieldPosition": 0,
            "minCardinality": 0,
            "maxCardinality": 0,
            "effectiveFrom": "{{$isoTimestamp}}",
            "effectiveTo": "{{$isoTimestamp}}"
          },
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false
        }

        """

        url = (f"{base_path(self, self.view_server)}/data-structures/{parent_data_struct_guid}"
               f"/member-data-fields/{member_data_field_guid}/attach")
        await self._async_new_relationship_request(url, ["MemberDataFieldProperties"], body)
        logger.info(f"Data field {member_data_field_guid} attached to Data structure {parent_data_struct_guid}.")

    @dynamic_catch
    def link_member_data_field(self, parent_data_struct_guid: str, member_data_field_guid: str,
                               body: dict | NewRelationshipRequestBody = None) -> None:
        """
         Connect a data structure to a data field.

         Parameters
         ----------
         parent_data_struct_guid: str
             - the GUID of the parent data structure the data class will be connected to.
         member_data_field_guid: str
             - the GUID of the data class to be connected.
         body: dict, optional
             - a dictionary containing additional properties.

         Returns
         -------
         None

         Raises
         ------
         InvalidParameterException
             one of the parameters is null or invalid or
         PropertyServerException
             There is a problem adding the element properties to the metadata repository or
         UserNotAuthorizedException
             the requesting user is not authorized to issue this request.

         Note
         ----

         Full sample body:
         {
           "class" : "NewRelationshipRequestBody",
           "properties": {
             "class": "MemberDataFieldProperties",
             "dataFieldPosition": 0,
             "minCardinality": 0,
             "maxCardinality": 0,
             "effectiveFrom": "{{$isoTimestamp}}",
             "effectiveTo": "{{$isoTimestamp}}"
           },
           "externalSourceGUID": "add guid here",
           "externalSourceName": "add qualified name here",
           "effectiveTime" : "{{$isoTimestamp}}",
           "forLineage" : false,
           "forDuplicateProcessing" : false
         }

         """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self._async_link_member_data_field(parent_data_struct_guid, member_data_field_guid, body))

    @dynamic_catch
    async def _async_detach_member_data_field(self, parent_data_struct_guid: str, member_data_field_guid: str,
                                              body: dict | DeleteRelationshipRequestBody = None,
                                              cascade_delete: bool = False) -> None:
        """
        Detach a data class from a data structure. Request body is optional. Async version.

        Parameters
        ----------
        parent_data_struct_guid: str
            - the GUID of the parent data structure the data class will be detached from..
        member_data_field_guid: str
            - the GUID of the data class to be disconnected.
        body: dict, optional
            - a dictionary containing additional properties.


        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:
        {
          "class": "DeleteRelationshipRequestBody",
          "cascadedDelete": false,
          "deleteMethod": "LOOK_FOR_LINEAGE",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }


        """

        url = (f"{self.data_designer_root}/data-structures/{parent_data_struct_guid}"
               f"/member-data-fields/{member_data_field_guid}/detach")

        await self._async_delete_relationship_request(url, body, cascade_delete)
        logger.info(f"Data field {member_data_field_guid} detached from data structure {parent_data_struct_guid}.")

    @dynamic_catch
    def detach_member_data_field(self, parent_data_struct_guid: str, member_data_field_guid: str,
                                 body: dict = None | DeleteRelationshipRequestBody, cascade_delete: bool = False) -> None:
        """
        Detach a data class from a data structure. Request body is optional.

        Parameters
        ----------
        parent_data_struct_guid: str
            - the GUID of the parent data structure the data class will be detached from..
        member_data_field_guid: str
            - the GUID of the data class to be disconnected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:
        {
          "class": "DeleteRelationshipRequestBody",
          "cascadedDelete": false,
          "deleteMethod": "LOOK_FOR_LINEAGE",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }


        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self._async_detach_member_data_field(parent_data_struct_guid, member_data_field_guid, body, cascade_delete))

    @dynamic_catch
    async def _async_delete_data_structure(self, data_struct_guid: str, body: dict = None,
                                           cascade_delete: bool = False) -> None:
        """
        Delete a data structure. Request body is optional. Async version.

        Parameters
        ----------
        data_struct_guid: str
            - the GUID of the parent data structure to delete.
        body: dict, optional
            - a dictionary containing additional properties.
        cascade_delete: bool, optional
            - if True, then all child data structures will be deleted as well. Otherwise, only the data structure

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:

        {
          "class": "DeleteRelationshipRequestBody",
          "cascadedDelete": false,
          "deleteMethod": "LOOK_FOR_LINEAGE",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        url = f"{self.data_designer_root}/data-structures/{data_struct_guid}/delete"

        await self._async_delete_element_request(url, body, cascade_delete)
        logger.info(f"Data structure {data_struct_guid} deleted.")

    @dynamic_catch
    def delete_data_structure(self, data_struct_guid: str, body: dict = None, cascade_delete: bool = False) -> None:
        """
        Delete a data structure. Request body is optional. Async version.

        Parameters
        ----------
        data_struct_guid: str
            - the GUID of the parent data structure to delete.
        body: dict, optional
            - a dictionary containing additional properties.
        cascade_delete: bool, optional
            - if True, then all child data structures will be deleted as well. Otherwise, only the data structure

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:

        {
          "class": "DeleteRelationshipRequestBody",
          "cascadedDelete": false,
          "deleteMethod": "LOOK_FOR_LINEAGE",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_delete_data_field(data_struct_guid, body, cascade_delete))

    @dynamic_catch
    def find_all_data_structures(self, output_format: str = 'JSON', report_spec: str | dict = None) -> list | str:
        """Returns a list of all known data structures. Async version.

        Parameters
        ----------

        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: dict, optional, default = None
            - The desired output columns/field options.
        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict of elements with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        """

        return self.find_data_structures(search_string="*", output_format=output_format,
                                         report_spec=report_spec)

    @dynamic_catch
    async def _async_find_data_structures(self, search_string: str, start_from: int = 0, page_size: int = 0,
                                          starts_with: bool = True, ends_with: bool = False, ignore_case: bool = True,
                                          body: dict | SearchStringRequestBody = None,
                                          output_format: str = 'JSON',
                                          report_spec: str | dict = None) -> list | str:
        """ Find the list of data structure metadata elements that contain the search string.
            Async version.

        Parameters
        ----------
        search_string: str
            - search string to filter on.
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        starts_with: bool, default = True
            - if True, the search string filters from the beginning of the string.
        ends_with: bool, default = False
            - if True, the search string filters from the end of the string.
        ignore_case: bool, default = True
            - If True, the case of the search string is ignored.
        output_format: str, default = "DICT"
            - one of "DICT", "MERMAID" or "JSON"
        report_spec: dict|str, optional, default = None
            - The desired output columns/field options.
        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict  with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Notes:
        _____
        Sample Body:
        {
          "class" : "SearchStringRequestBody",
          "startsWith" : false,
          "endsWith" : false,
          "ignoreCase" : true,
          "startFrom" : 0,
          "pageSize": 0,
          "asOfTime" : "{{$isoTimestamp}}",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "limitResultsByStatus" : ["ACTIVE"],
          "sequencingOrder" : "PROPERTY_ASCENDING",
          "sequencingProperty" : "qualifiedName"
        }

        """

        url = f"{base_path(self, self.view_server)}/data-structures/by-search-string"

        return await self._async_find_request(url, "DataStructure", self._generate_data_structure_output,
                                              search_string, start_from=start_from, page_size=page_size,
                                              starts_with=starts_with, ends_with=ends_with, ignore_case=ignore_case,
                                              body=body, output_format=output_format,
                                              report_spec=report_spec)

    @dynamic_catch
    def find_data_structures(self, search_string: str, start_from: int = 0, page_size: int = 0,
                             starts_with: bool = True, ends_with: bool = False, ignore_case: bool = True,
                             body: dict | SearchStringRequestBody = None,
                             output_format: str = 'JSON', report_spec: str | dict = None) -> list | str:
        """ Find the list of data structure metadata elements that contain the search string.

        Parameters
        ----------
        search_string: str
            - search string to filter on.
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        starts_with: bool, default = True
            - if True, the search string filters from the beginning of the string.
        ends_with: bool, default = False
            - if True, the search string filters from the end of the string.
        ignore_case: bool, default = True
            - If True, the case of the search string is ignored.
        output_format: str, default = "DICT"
            - one of "DICT", "MERMAID" or "JSON"
        report_spec: dict|str, optional, default = None
            - The desired output columns/field options.
        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict  with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Notes:
        _____
        Sample Body:
        {
          "class" : "SearchStringRequestBody",
          "startsWith" : false,
          "endsWith" : false,
          "ignoreCase" : true,
          "startFrom" : 0,
          "pageSize": 0,
          "asOfTime" : "{{$isoTimestamp}}",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "limitResultsByStatus" : ["ACTIVE"],
          "sequencingOrder" : "PROPERTY_ASCENDING",
          "sequencingProperty" : "qualifiedName"
        }

        """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self._async_find_data_structures(search_string, start_from, page_size, starts_with, ends_with, ignore_case,
                                             body, output_format, report_spec))
        return response

    @dynamic_catch
    async def _async_get_data_structures_by_name(self, filter_string: str, classification_names: list[str] = None,
                                                 body: dict | FilterRequestBody = None, start_from: int = 0,
                                                 page_size: int = 0,
                                                 output_format: str = 'JSON',
                                                 report_spec: str | dict = None) -> list | str:
        """ Get the list of data structure metadata elements with a matching name to the search string filter.
            Async version.

        Parameters
        ----------
        filter: str
            - search string to filter on.
        body: dict, optional
            - a dictionary containing additional properties for the request.
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        output_format: str, default = "DICT"
            - one of "DICT", "MERMAID" or "JSON"
        report_spec: str | dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict  with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Notes
        -----
        {
          "class": "FilterRequestBody",
          "asOfTime": "{{$isoTimestamp}}",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false,
          "limitResultsByStatus": ["ACTIVE"],
          "sequencingOrder": "PROPERTY_ASCENDING",
          "sequencingProperty": "qualifiedName",
          "filter": "Add name here"
        }
        """

        url = f"{base_path(self, self.view_server)}/data-structures/by-name"
        response = await self._async_get_name_request(url, _type="DataStructure",
                                                      _gen_output=self._generate_data_structure_output,
                                                      filter_string=filter_string,
                                                      classification_names=classification_names,
                                                      start_from=start_from, page_size=page_size,
                                                      output_format=output_format, report_spec=report_spec,
                                                      body=body)

        return response

    @dynamic_catch
    def get_data_structures_by_name(self, filter: str, classification_names: list[str] = None,
                                    body: dict | FilterRequestBody = None, start_from: int = 0,
                                    page_size: int = max_paging_size, output_format: str = 'JSON',
                                    report_spec: str | dict = None) -> list | str:
        """ Get the list of data structure metadata elements with a matching name to the search string filter.

        Parameters
        ----------
        filter: str
            - search string to filter on.
        body: dict, optional
            - a dictionary containing additional properties for the request.
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        output_format: str, default = "DICT"
         - one of "DICT", "MERMAID" or "JSON"
        report_spec: str | dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict  with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.


    """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self._async_get_data_structures_by_name(filter, classification_names, body, start_from, page_size,
                                                    output_format, report_spec))
        return response

    @dynamic_catch
    async def _async_get_data_structure_by_guid(self, guid: str, element_type: str = None,
                                                body: dict | GetRequestBody = None,
                                                output_format: str = 'JSON',
                                                report_spec: str | dict = None) -> list | str:
        """ Get the  data structure metadata elements for the specified GUID.
            Async version.

        Parameters
        ----------
        guid: str
            - unique identifier of the data structure metadata element.
        element_type: str, optional
            - optional element type.
        body: dict | GetRequestBody, optional
            - optional request body.
        output_format: str, default = "DICT"
         - one of "DICT", "MERMAID" or "JSON"
        report_spec: str | dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict  with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Notes
        ----

        Optional request body:
        {
          "class" : "GetRequestBody",
          "asOfTime" : "{{$isoTimestamp}}",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false
        }


        """

        url = (f"{base_path(self, self.view_server)}/data-structures/{guid}/retrieve")
        type = element_type if element_type else "DataStructure"

        response = await self._async_get_guid_request(url, _type=type,
                                                      _gen_output=self._generate_data_structure_output,
                                                      output_format=output_format, report_spec=report_spec,
                                                      body=body)

        return response

    @dynamic_catch
    def get_data_structure_by_guid(self, guid: str, element_type: str = None, body: str = None,
                                   output_format: str = 'JSON', report_spec: str | dict = None) -> list | str:
        """ Get the data structure metadata element with the specified unique identifier..

        Parameters
        ----------
        guid: str
            - unique identifier of the data structure metadata element.
        element_type: str, optional
            - optional element type.
        body: dict, optional
            - optional request body.
        output_format: str, default = "DICT"
         - one of "DICT", "MERMAID" or "JSON"
        report_spec: str | dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict  with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Notes
        ----

        Optional request body:
        {
          "class": "GetRequestBody",
          "asOfTime": "{{$isoTimestamp}}",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

    """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self._async_get_data_structure_by_guid(guid, element_type, body, output_format, report_spec))
        return response

    def get_data_memberships(self, data_get_fcn: callable, data_struct_guid: str) -> dict | None:
        data_structure_info = data_get_fcn(data_struct_guid, output_format="JSON")
        if data_structure_info == "No elements found":
            return None
        collection_list = {"DictList": [], "SpecList": [], "CollectionDetails": []}
        if isinstance(data_structure_info, (dict, list)):
            member_of_collections = data_structure_info.get('memberOfCollections', "")
            if isinstance(member_of_collections, list):
                for member_rel in member_of_collections:
                    props = member_rel["relatedElement"]["properties"]
                    qname = props.get('qualifiedName', None)
                    guid = member_rel['relatedElement']['elementHeader']['guid']
                    description = props.get('description', None)
                    collection_type = props.get('collectionType', None)
                    if collection_type == "Data Dictionary":
                        collection_list["DictList"].append(guid)
                    elif collection_type == "Data Specification":
                        collection_list["SpecList"].append(guid)
                    collection_list["CollectionDetails"].append({
                        "guid": guid, "description": description,
                        "collectionType": collection_type,
                        "qualifiedName": qname
                        })
            else:
                return None
            return collection_list
        else:
            return None

    def get_data_memberships_with_dict(self, data_field_elements: dict) -> dict:
        collection_list = {
            "DictList_guid": [], "DictList_qn": [], "SpecList_guid": [], "SpecList_qn": [], "CollectionDetails": []
            }
        if isinstance(data_field_elements, (dict, list)):

            for member_rel in data_field_elements:
                type_name = ""
                props = member_rel["relatedElement"]["properties"]
                qname = props.get('qualifiedName', None)
                guid = member_rel['relatedElement']['elementHeader']['guid']
                description = props.get('description', None)
                collection_type = props.get('collectionType', None)
                classifications = member_rel["relatedElement"]["elementHeader"]["classifications"]
                for classification in classifications:
                    type_name = classification["type"]['typeName']
                    if type_name == "DataDictionary":
                        collection_list["DictList_guid"].append(guid)
                        collection_list["DictList_qn"].append(qname)
                    elif type_name == "DataSpec":
                        collection_list["SpecList_guid"].append(guid)
                        collection_list["SpecList_qn"].append(qname)
                collection_list["CollectionDetails"].append({
                    "typeName": type_name, "guid": guid,
                    "description": description,
                    "collectionType": collection_type,
                    "qualifiedName": qname
                    })
        return collection_list

    def get_data_rel_elements_dict(self, el_struct: dict) -> dict | str:
        """return the lists of objects related to a data field"""

        parent_guids = []
        parent_names = []
        parent_qnames = []

        data_structure_guids = []
        data_structure_names = []
        data_structure_qnames = []

        assigned_meanings_guids = []
        assigned_meanings_names = []
        assigned_meanings_qnames = []

        data_class_guids = []
        data_class_names = []
        data_class_qnames = []

        external_references_guids = []
        external_references_names = []
        external_references_qnames = []

        member_of_data_dicts_guids = []
        member_of_data_dicts_names = []
        member_of_data_dicts_qnames = []

        member_of_data_spec_guids = []
        member_of_data_spec_names = []
        member_of_data_spec_qnames = []

        member_data_field_guids = []
        member_data_field_names = []
        member_data_field_qnames = []

        nested_data_classes_guids = []
        nested_data_classes_names = []
        nested_data_classes_qnames = []

        specialized_data_classes_guids = []
        specialized_data_classes_names = []
        specialized_data_classes_qnames = []

        # terms
        assigned_meanings = el_struct.get("assignedMeanings", {})
        for meaning in assigned_meanings:
            assigned_meanings_guids.append(meaning['relatedElement']['elementHeader']['guid'])
            assigned_meanings_names.append(meaning['relatedElement']['properties']['displayName'])
            assigned_meanings_qnames.append(meaning['relatedElement']['properties']['qualifiedName'])

        # extract existing related data structure and data field elements
        part_of_data_struct = el_struct.get("partOfDataStructures", None)
        if part_of_data_struct:
            for rel in part_of_data_struct:
                related_element = rel["relatedElement"]
                guid = related_element["elementHeader"]["guid"]
                qualified_name = related_element["properties"].get("qualifiedName", "") or ""
                display_name = related_element["properties"].get("displayName", "") or ""
                data_structure_guids.append(guid)
                data_structure_names.append(display_name)
                data_structure_qnames.append(qualified_name)
# Todo - check the logic here
        # elif type == "DataField":
        #     parent_guids.append(guid)
        #     parent_names.append(display_name)
        #     parent_qnames.append(qualified_name)

        member_of_collections = el_struct.get("memberOfCollections", {})
        for collection in member_of_collections:
            type_name = collection["relatedElement"]["elementHeader"]["type"].get("typeName", "") or ""
            guid = collection["relatedElement"]["elementHeader"]["guid"]
            name = collection["relatedElement"]["properties"].get("displayName", "") or ""
            qualifiedName = collection['relatedElement']["properties"].get("qualifiedName", "") or ""
            if type_name:
                if type_name == "DataDictionary":
                    member_of_data_dicts_guids.append(guid)
                    member_of_data_dicts_names.append(name)
                    member_of_data_dicts_qnames.append(qualifiedName)
                elif type_name == "DataSpec":
                    member_of_data_spec_guids.append(guid)
                    member_of_data_spec_names.append(name)
                    member_of_data_spec_qnames.append(qualifiedName)

        member_data_fields = el_struct.get("containsDataFields", {})
        for data_field in member_data_fields:
            rel_el = data_field.get("relatedElement",{})
            member_data_field_guids.append(rel_el["elementHeader"]["guid"])
            member_data_field_names.append(rel_el["properties"]["displayName"])
            member_data_field_qnames.append(rel_el["properties"]["qualifiedName"])

        data_classes = el_struct.get("assignedDataClasses", {})
        for data_class in data_classes:
            data_class_guids.append(data_class['relatedElement']["elementHeader"]["guid"])
            data_class_names.append(data_class['relatedElement']["properties"]["displayName"])
            data_class_qnames.append(data_class['relatedElement']["properties"]["qualifiedName"])

        nested_data_classes = el_struct.get("nestedDataClasses", {})
        for nested_data_class in nested_data_classes:
            nested_data_classes_guids.append(nested_data_class['relatedElement']["elementHeader"]["guid"])
            nested_data_classes_names.append(nested_data_class['relatedElement']["properties"]["displayName"])
            nested_data_classes_qnames.append(nested_data_class['relatedElement']["properties"]["qualifiedName"])

        specialized_data_classes = el_struct.get("specializedDataClasses", {})
        for nested_data_class in specialized_data_classes:
            specialized_data_classes_guids.append(nested_data_class['relatedElement']["elementHeader"]["guid"])
            specialized_data_classes_names.append(nested_data_class['relatedElement']["properties"]["displayName"])
            specialized_data_classes_qnames.append(nested_data_class['relatedElement']["properties"]["qualifiedName"])

        mermaid = el_struct.get("mermaidGraph", {})

        return {
            "parent_guids": parent_guids,
            "parent_names": parent_names,
            "parent_qnames": parent_qnames,

            "data_structure_guids": data_structure_guids,
            "data_structure_names": data_structure_names,
            "in_data_structure": data_structure_qnames,

            "assigned_meanings_guids": assigned_meanings_guids,
            "assigned_meanings_names": assigned_meanings_names,
            "assigned_meanings_qnames": assigned_meanings_qnames,

            "data_class_guids": data_class_guids,
            "data_class_names": data_class_names,
            "data_class_qnames": data_class_qnames,

            "nested_data_class_guids": nested_data_classes_guids,
            "nested_data_class_names": nested_data_classes_names,
            "nested_data_class_qnames": nested_data_classes_qnames,

            "specialized_data_class_guids": specialized_data_classes_guids,
            "specialized_data_class_names": specialized_data_classes_names,
            "specialized_data_class_qnames": specialized_data_classes_qnames,

            "external_references_guids": external_references_guids,
            "external_references_names": external_references_names,
            "external_references_qnames": external_references_qnames,

            "member_of_data_dicts_guids": member_of_data_dicts_guids,
            "member_of_data_dicts_names": member_of_data_dicts_names,
            "in_data_dictionary": member_of_data_dicts_qnames,

            "member_of_data_spec_guids": member_of_data_spec_guids,
            "member_of_data_spec_names": member_of_data_spec_names,
            "in_data_spec": member_of_data_spec_qnames,

            "member_data_field_guids": member_data_field_guids,
            "member_data_field_names": member_data_field_names,
            "member_data_fields": member_data_field_qnames,

            "mermaid": mermaid,
            }

    def get_data_field_rel_elements(self, guid: str) -> dict | str:
        """return the lists of objects related to a data field"""

        data_field_entry = self.get_data_field_by_guid(guid, output_format="JSON")
        if isinstance(data_field_entry, str):
            return None
        return self.get_data_rel_elements_dict(data_field_entry)

    def get_data_class_rel_elements(self, guid: str) -> dict | str:
        """return the lists of objects related to a data class"""

        data_class_entry = self.get_data_class_by_guid(guid, output_format="JSON")
        if isinstance(data_class_entry, str):
            return None
        return self.get_data_rel_elements_dict(data_class_entry)

    #
    # Work with Data Fields
    # https://egeria-project.org/concepts/data-class
    #
    @dynamic_catch
    async def _async_create_data_field(self, body: dict | NewElementRequestBody) -> str:
        """
        Create a new data class with parameters defined in the body. Async version.

        Parameters
        ----------
        body: dict
            - a dictionary containing the properties of the data class to be created.

        Returns
        -------
        str
            The GUID of the element - or "No element found"

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----
        Sample bodies:

        {
          "class" : "NewElementRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "anchorGUID" : "add guid here",
          "isOwnAnchor": false,
          "parentGUID": "add guid here",
          "parentRelationshipTypeName": "add type name here",
          "parentRelationshipProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "parentAtEnd1": false,
          "properties": {
            "class" : "DataFieldProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "namespace": "",
            "description": "add description here",
            "versionIdentifier": "add version",
            "aliases": ["alias1", "alias2"],
            "isDeprecated": false,
            "isNullable" : false,
            "defaultValue": "",
            "dataType": "",
            "minimumLength": 0,
            "length": 0,
            "precision": 0,
            "orderedValues": false,
            "sortOrder": "UNSORTED",
            "additionalProperties": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            },
            "effectiveFrom": "{{$isoTimestamp}}",
            "effectiveTo": "{{$isoTimestamp}}"
          }
        }
    or
       {
          "properties": {
            "class": "DataFieldProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "namespace": "",
            "description": "add description here",
            "versionIdentifier": "add version",
            "aliases": [
              "alias1",
              "alias2"
            ],
            "namePatterns": [],
            "isDeprecated": false,
            "isNullable": false,
            "defaultValue": "",
            "dataType": "",
            "minimumLength": 0,
            "length": 0,
            "precision": 0,
            "orderedValues": false,
            "sortOrder": "UNSORTED",
            "additionalProperties": {
              "property1": "propertyValue1",
              "property2": "propertyValue2"
            }
          }
        }


        """

        url = f"{base_path(self, self.view_server)}/data-fields"

        return await self._async_create_element_body_request(url, "DataField", body)

    @dynamic_catch
    def create_data_field(self, body: dict | NewElementRequestBody) -> str:
        """
        Create a new data class with parameters defined in the body..

        Parameters
        ----------
        body: dict
            - a dictionary containing the properties of the data class to be created.

        Returns
        -------
        str
            The GUID of the element - or "No element found"

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample bodies:

        {
          "class" : "NewDataFieldRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "anchorGUID" : "add guid here",
          "isOwnAnchor": false,
          "parentGUID": "add guid here",
          "parentRelationshipTypeName": "add type name here",
          "parentRelationshipProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "parentAtEnd1": false,
          "properties": {
            "class" : "DataFieldProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "namespace": "",
            "description": "add description here",
            "versionIdentifier": "add version",
            "aliases": ["alias1", "alias2"],
            "isDeprecated": false,
            "isNullable" : false,
            "defaultValue": "",
            "dataType": "",
            "minimumLength": 0,
            "length": 0,
            "precision": 0,
            "orderedValues": false,
            "sortOrder": "UNSORTED",
            "additionalProperties": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            },
            "effectiveFrom": "{{$isoTimestamp}}",
            "effectiveTo": "{{$isoTimestamp}}"
          }
        }
    or
       {
          "properties": {
            "class": "DataFieldProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "namespace": "",
            "description": "add description here",
            "versionIdentifier": "add version",
            "aliases": [
              "alias1",
              "alias2"
            ],
            "namePatterns": [],
            "isDeprecated": false,
            "isNullable": false,
            "defaultValue": "",
            "dataType": "",
            "minimumLength": 0,
            "length": 0,
            "precision": 0,
            "orderedValues": false,
            "sortOrder": "UNSORTED",
            "additionalProperties": {
              "property1": "propertyValue1",
              "property2": "propertyValue2"
            }
          }
        }


        """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._async_create_data_field(body))
        return response

    @dynamic_catch
    async def _async_create_data_field_from_template(self, body: dict | TemplateRequestBody) -> str:
        """
        Create a new metadata element to represent a data class using an existing metadata element as a template.
        The template defines additional classifications and relationships that should be added to the new element.
        Async version.

        Parameters
        ----------
        body: dict
            - a dictionary containing the properties of the data class to be created.

        Returns
        -------
        str
            The GUID of the element - or "No element found"

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----
        {
          "class" : "TemplateRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "anchorGUID" : "add guid here",
          "isOwnAnchor": false,
          "parentGUID": "add guid here",
          "parentRelationshipTypeName": "add type name here",
          "parentRelationshipProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "parentAtEnd1": false,
          "templateGUID": "add guid here",
          "replacementProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "placeholderPropertyValues":  {
            "placeholder1" : "propertyValue1",
            "placeholder2" : "propertyValue2"
          }
        }

        """

        url = f"{base_path(self, self.view_server)}/data-fields/from-template"

        return await self._async_create_element_from_template(url, body)

    @dynamic_catch
    def create_data_field_from_template(self, body: dict | TemplateRequestBody) -> str:
        """
        Create a new metadata element to represent a data class using an existing metadata element as a template.
        The template defines additional classifications and relationships that should be added to the new element.
        Async version.

        Parameters
        ----------
        body: dict
            - a dictionary containing the properties of the data class to be created.

        Returns
        -------
        str
            The GUID of the element - or "No element found"

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----
        {
          "class" : "TemplateRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "anchorGUID" : "add guid here",
          "isOwnAnchor": false,
          "parentGUID": "add guid here",
          "parentRelationshipTypeName": "add type name here",
          "parentRelationshipProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "parentAtEnd1": false,
          "templateGUID": "add guid here",
          "replacementProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "placeholderPropertyValues":  {
            "placeholder1" : "propertyValue1",
            "placeholder2" : "propertyValue2"
          }
        }

        """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._async_create_data_field_from_template(body))
        return response

    @dynamic_catch
    async def _async_update_data_field(self, data_field_guid: str, body: dict | UpdateElementRequestBody) -> None:
        """
        Update the properties of a data class. Async version.

        Parameters
        ----------
        data_field_guid: str
            - the GUID of the data class to be updated.
        body: dict
            - a dictionary containing the properties of the data structure to be created.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:

       {
          "class" : "UpdateDataFieldRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "properties": {
            "class" : "DataFieldProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "namespace": "",
            "description": "add description here",
            "versionIdentifier": "add version",
            "aliases": ["alias1", "alias2"],
            "namePatterns": [],
            "isDeprecated": false,
            "isNullable" : false,
            "defaultValue": "",
            "dataType": "",
            "minimumLength": 0,
            "length": 0,
            "precision": 0,
            "orderedValues": false,
            "sortOrder": "UNSORTED",
            "additionalProperties": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            },
            "effectiveFrom": "{{$isoTimestamp}}",
            "effectiveTo": "{{$isoTimestamp}}"
          }
        }

        """

        url = f"{base_path(self, self.view_server)}/data-fields/{data_field_guid}/update"

        await self._async_update_element_body_request(url, ["DataField"], body)
        logger.info(f"Data Field {data_field_guid} updated.")

    @dynamic_catch
    def update_data_field(self, data_field_guid: str, body: dict | UpdateElementRequestBody) -> None:
        """
        Update the properties of a data class.

        Parameters
        ----------
        data_field_guid: str
            - the GUID of the data class to be updated.
        body: dict
            - a dictionary containing the properties of the data structure to be created.
        replace_all_properties: bool, default = False
            - if true, then all properties will be replaced with the new ones. Otherwise, only the specified ones
              will be replaced.
        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:

       {
          "class" : "UpdateDataFieldRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "properties": {
            "class" : "DataFieldProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "namespace": "",
            "description": "add description here",
            "versionIdentifier": "add version",
            "aliases": ["alias1", "alias2"],
            "namePatterns": [],
            "isDeprecated": false,
            "isNullable" : false,
            "defaultValue": "",
            "dataType": "",
            "minimumLength": 0,
            "length": 0,
            "precision": 0,
            "orderedValues": false,
            "sortOrder": "UNSORTED",
            "additionalProperties": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            },
            "effectiveFrom": "{{$isoTimestamp}}",
            "effectiveTo": "{{$isoTimestamp}}"
          }
        }
        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_update_data_field(data_field_guid, body))

    @dynamic_catch
    async def _async_link_nested_data_field(self, parent_data_field_guid: str, nested_data_field_guid: str,
                                            body: dict | NewRelationshipRequestBody = None) -> None:
        """
        Connect a nested data field to a data field. Request body is optional. Async version.

        Parameters
        ----------
        parent_data_field_guid: str
            - the GUID of the parent data field the nested data field will be connected to.
        nested_data_field_guid: str
            - the GUID of the nested data field to be connected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:

        {
          "class" : "MemberDataFieldRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "properties": {
            "class": "MemberDataFieldProperties",
            "dataFieldPosition": 0,
            "minCardinality": 0,
            "maxCardinality": 0,
            "effectiveFrom": "{{$isoTimestamp}}",
            "effectiveTo": "{{$isoTimestamp}}"
          }
        }

        """

        url = (f"{base_path(self, self.view_server)}/data-fields/{parent_data_field_guid}"
               f"/nested-data-fields/{nested_data_field_guid}/attach")

        await self._async_new_relationship_request(url, ["NestedDataFieldProperties"], body)
        logger.info(f"Data field {parent_data_field_guid} attached to Data structure {nested_data_field_guid}.")

    @dynamic_catch
    def link_nested_data_field(self, parent_data_field_guid: str, nested_data_field_guid: str,
                               body: dict | NewRelationshipRequestBody = None) -> None:
        """
        Connect a nested data class to a data class. Request body is optional.

        Parameters
        ----------
        parent_data_field_guid: str
            - the GUID of the parent data field the nested data field will be connected to.
        nested_data_field_guid: str
            - the GUID of the nested data field to be connected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:

        {
          "class" : "MemberDataFieldRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "properties": {
            "class": "MemberDataFieldProperties",
            "dataFieldPosition": 0,
            "minCardinality": 0,
            "maxCardinality": 0,
            "effectiveFrom": "{{$isoTimestamp}}",
            "effectiveTo": "{{$isoTimestamp}}"
          }
        }

        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self._async_link_nested_data_field(parent_data_field_guid, nested_data_field_guid, body))

    @dynamic_catch
    async def _async_detach_nested_data_field(self, parent_data_field_guid: str, nested_data_field_guid: str,
                                              body: dict | DeleteRelationshipRequestBody = None) -> None:
        """
        Detach a nested data class from a data class. Request body is optional. Async version.

        Parameters
        ----------
        parent_data_field_guid: str
            - the GUID of the parent data class the data class will be detached from..
        nested_data_field_guid: str
            - the GUID of the data class to be disconnected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:

       {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }


        """

        url = (f"{base_path(self, self.view_server)}/data-fields/{parent_data_field_guid}"
               f"/member-data-fields/{nested_data_field_guid}/detach")

        await self._async_delete_relationship_request(url, body)
        logger.info(f"Data field {parent_data_field_guid} detached from data structure {nested_data_field_guid}.")

    @dynamic_catch
    def detach_nested_data_field(self, parent_data_field_guid: str, nested_data_field_guid: str,
                                 body: dict | DeleteRelationshipRequestBody = None) -> None:
        """
        Detach a nested data class from a data class. Request body is optional.

        Parameters
        ----------
        parent_data_field_guid: str
            - the GUID of the parent data structure the data class will be detached fromo.
        nested_data_field_guid: str
            - the GUID of the data class to be disconnected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self._async_detach_nested_data_field(parent_data_field_guid, nested_data_field_guid, body))

    @dynamic_catch
    async def _async_delete_data_field(self, data_field_guid: str, body: dict | DeleteElementRequestBody = None,
                                       cascade_delete: bool = False) -> None:
        """
        Delete a data class. Request body is optional. Async version.

        Parameters
        ----------
        data_field_guid: str
            - the GUID of the data class to delete.
        body: dict| DeleteElementRequestBody, optional
            - a dictionary containing additional properties.
        cascade: bool, optional
            - if True, then all child data fields will be deleted as well.


        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:

       {
          "class": "DeleteElementRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }


        """

        url = f"{base_path(self, self.view_server)}/data-fields/{data_field_guid}/delete"

        await self._async_delete_element_request(url, body, cascade_delete)
        logger.info(f"Data Field {data_field_guid} deleted.")

    @dynamic_catch
    def delete_data_field(self, data_field_guid: str, body: dict | DeleteElementRequestBody = None,
                          cascade_delete: bool = False) -> None:
        """
        Delete a data class. Request body is optional.

        Parameters
        ----------
        data_field_guid: str
            - the GUID of the data class the data class to delete.
        body: dict | DeleteElementRequestBody, optional
            - a dictionary containing additional properties.
        cascade: bool, optional
            - if True, then all child data fields will be deleted as well.


        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_delete_data_field(data_field_guid, body, cascade_delete))

    @dynamic_catch
    async def _async_find_all_data_fields(self, output_format: str = 'JSON',
                                          report_spec: str | dict = None) -> list | str:
        """Returns a list of all known data fields. Async version.

        Parameters
        ----------
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict elements with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        """

        return self.find_data_fields(search_string="*", output_format=output_format,
                                     report_spec=report_spec)

    @dynamic_catch
    def find_all_data_fields(self, output_format: str = 'JSON', report_spec: str | dict = None) -> list | str:
        """ Returns a list of all known data fields.

        Parameters
        ----------
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict elements with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self._async_find_all_data_fields(output_format, report_spec))
        return response

    @dynamic_catch
    async def _async_find_data_fields(self, search_string: str, start_from: int = 0, page_size: int = 0,
                                      starts_with: bool = True, ends_with: bool = False, ignore_case: bool = True,
                                      body: dict | SearchStringRequestBody = None,
                                      output_format: str = 'JSON', report_spec: str | dict = None) -> list | str:
        """ Find the list of data class elements that contain the search string.
            Async version.

        Parameters
        ----------
        filter: str
            - search string to filter on.
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        starts_with: bool, default = True
            - if True, the search string filters from the beginning of the string.
        ends_with: bool, default = False
            - if True, the search string filters from the end of the string.
        ignore_case: bool, default = True
            - If True, the case of the search string is ignored.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        """

        url = f"{base_path(self, self.view_server)}/data-fields/by-search-string"

        return await self._async_find_request(url, "DataField", self._generate_data_field_output,
                                              search_string, start_from=start_from, page_size=page_size,
                                              starts_with=starts_with, ends_with=ends_with, ignore_case=ignore_case,
                                              body=body, output_format=output_format,
                                              report_spec=report_spec)

    @dynamic_catch
    def find_data_fields(self, search_string: str, start_from: int = 0, page_size: int = max_paging_size,
                         starts_with: bool = True, ends_with: bool = False, ignore_case: bool = True,
                         body: dict | SearchStringRequestBody = None,
                         output_format: str = 'JSON', report_spec: str | dict = None) -> list | str:
        """ Retrieve the list of data fields elements that contain the search string filter.

        Parameters
        ----------
        filter: str
            - search string to filter on.
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        starts_with: bool, default = True
            - if True, the search string filters from the beginning of the string.
        ends_with: bool, default = False
            - if True, the search string filters from the end of the string.
        ignore_case: bool, default = True
            - If True, the case of the search string is ignored.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict  with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.


    """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self._async_find_data_fields(search_string, start_from, page_size, starts_with, ends_with, ignore_case,
                                         body, output_format, report_spec))
        return response

    @dynamic_catch
    async def _async_get_data_fields_by_name(self, filter_string: str, classification_names: list[str] = None,
                                             body: dict = None | FilterRequestBody, start_from: int = 0,
                                             page_size: int = 0,
                                             output_format: str = 'JSON',
                                             report_spec: str | dict = None) -> list | str:
        """ Get the list of data class metadata elements with a matching name to the search string filter.
            Async version.

        Parameters
        ----------
        filter: str
            - search string to filter on.
        body: dict, optional
            - a dictionary containing additional properties to use in the request.
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.
        Notes
        -----

        {
          "class": "FilterRequestBody",
          "asOfTime": "{{$isoTimestamp}}",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false,
          "limitResultsByStatus": ["ACTIVE"],
          "sequencingOrder": "PROPERTY_ASCENDING",
          "sequencingProperty": "qualifiedName",
          "filter": "Add name here"
        }
        """

        url = f"{base_path(self, self.view_server)}/data-fields/by-name"

        response = await self._async_get_name_request(url, _type="DataField",
                                                      _gen_output=self._generate_data_field_output,
                                                      filter_string=filter_string,
                                                      classification_names=classification_names,
                                                      start_from=start_from, page_size=page_size,
                                                      output_format=output_format, report_spec=report_spec,
                                                      body=body)

        return response

    @dynamic_catch
    def get_data_fields_by_name(self, filter_string: str, classification_names: list[str] = None, body: dict = None,
                                start_from: int = 0,
                                page_size: int = max_paging_size, output_format: str = 'JSON',
                                report_spec: str | dict = None) -> list | str:
        """ Get the list of data class elements with a matching name to the search string filter.

        Parameters
        ----------
        filter: str
            - search string to filter on.
        body: dict, optional
            - a dictionary containing additional properties to use in the request.
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Notes
        -----
        {
          "class": "FilterRequestBody",
          "asOfTime": "{{$isoTimestamp}}",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false,
          "limitResultsByStatus": ["ACTIVE"],
          "sequencingOrder": "PROPERTY_ASCENDING",
          "sequencingProperty": "qualifiedName",
          "filter": "Add name here"
        }


    """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self._async_get_data_fields_by_name(filter_string, classification_names, body, start_from, page_size,
                                                output_format, report_spec))
        return response

    @dynamic_catch
    async def _async_get_data_field_by_guid(self, guid: str, element_type: str = None,
                                            body: dict | GetRequestBody = None,
                                            output_format: str = 'JSON',
                                            report_spec: str | dict = None) -> list | str:
        """ Get the  data class elements for the specified GUID.
            Async version.

        Parameters
        ----------
        guid: str
            - unique identifier of the data class metadata element.
        body: dict, optional
            - optional request body.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict  with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.


        Notes
        ----

        Optional request body:
        {
          "class": "AnyTimeRequestBody",
          "asOfTime": "{{$isoTimestamp}}",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        url = (f"{base_path(self, self.view_server)}/data-fields/{guid}/retrieve")
        type = element_type if element_type else "DataField"
        response = await self._async_get_guid_request(url, _type=type,
                                                      _gen_output=self._generate_data_field_output,
                                                      output_format=output_format, report_spec=report_spec,
                                                      body=body)

        return response

    @dynamic_catch
    def get_data_field_by_guid(self, guid: str, element_type: str = None, body: str | GetRequestBody = None,
                               output_format: str = 'JSON', report_spec: str | dict = None) -> list | str:
        """ Get the  data structure metadata element with the specified unique identifier..

        Parameters
        ----------
        guid: str
            - unique identifier of the data structure metadata element.
        body: dict, optional
            - optional request body.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict  with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Notes
        ----

        Optional request body:
        {
          "class": "AnyTimeRequestBody",
          "asOfTime": "{{$isoTimestamp}}",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

    """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._async_get_data_field_by_guid(guid, element_type,
                                                                              body, output_format, report_spec))
        return response

    ###
    # =====================================================================================================================
    # Work with Data Classes
    # https://egeria-project.org/concepts/data-class
    #
    #
    @dynamic_catch
    async def _async_create_data_class(self, body: dict | NewElementRequestBody) -> str:
        """
        Create a new data class with parameters defined in the body. Async version.

        Parameters
        ----------
        body: dict
            - a dictionary containing the properties of the data class to be created.

        Returns
        -------
        str
            The GUID of the element - or "No element found"

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----
        Sample bodies:

        {
          "class" : "NewDataClassRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "anchorGUID" : "add guid here",
          "isOwnAnchor": false,
          "parentGUID": "add guid here",
          "parentRelationshipTypeName": "add type name here",
          "parentRelationshipProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "parentAtEnd1": false,
          "properties": {
            "class" : "DataClassProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "description": "add description here",
            "namespace": "add scope of this data class's applicability.",
            "matchPropertyNames": ["name1", "name2"],
            "matchThreshold": 0,
            "specification": "",
            "specificationDetails": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            },
            "dataType": "",
            "allowsDuplicateValues": true,
            "isNullable": false,
            "defaultValue": "",
            "averageValue": "",
            "valueList": [],
            "valueRangeFrom": "",
            "valueRangeTo": "",
            "sampleValues": [],
            "dataPatterns" : [],
            "additionalProperties": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            },
            "effectiveFrom": "{{$isoTimestamp}}",
            "effectiveTo": "{{$isoTimestamp}}"
          }
        }
        or
        {
          "properties": {
            "class": "DataClassProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "description": "add description here",
            "namespace": "add scope of this data class's applicability.",
            "matchPropertyNames": [
              "name1",
              "name2"
            ],
            "matchThreshold": 0,
            "specification": "",
            "specificationDetails": {
              "property1": "propertyValue1",
              "property2": "propertyValue2"
            },
            "dataType": "",
            "allowsDuplicateValues": true,
            "isNullable": false,
            "defaultValue": "",
            "averageValue": "",
            "valueList": [],
            "valueRangeFrom": "",
            "valueRangeTo": "",
            "sampleValues": [],
            "dataPatterns": [],
            "additionalProperties": {
              "property1": "propertyValue1",
              "property2": "propertyValue2"
            }
          }
        }

        """

        url = f"{base_path(self, self.view_server)}/data-classes"

        return await self._async_create_element_body_request(url, "DataClass", body)

    @dynamic_catch
    def create_data_class(self, body: dict | NewElementRequestBody) -> str:
        """
        Create a new data class with parameters defined in the body..

        Parameters
        ----------
        body: dict
            - a dictionary containing the properties of the data class to be created.

        Returns
        -------
        str
            The GUID of the element - or "No element found"

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        {
          "class" : "NewDataClassRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "anchorGUID" : "add guid here",
          "isOwnAnchor": false,
          "parentGUID": "add guid here",
          "parentRelationshipTypeName": "add type name here",
          "parentRelationshipProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "parentAtEnd1": false,
          "properties": {
            "class" : "DataClassProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "description": "add description here",
            "namespace": "add scope of this data class's applicability.",
            "matchPropertyNames": ["name1", "name2"],
            "matchThreshold": 0,
            "specification": "",
            "specificationDetails": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            },
            "dataType": "",
            "allowsDuplicateValues": true,
            "isNullable": false,
            "defaultValue": "",
            "averageValue": "",
            "valueList": [],
            "valueRangeFrom": "",
            "valueRangeTo": "",
            "sampleValues": [],
            "dataPatterns" : [],
            "additionalProperties": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            },
            "effectiveFrom": "{{$isoTimestamp}}",
            "effectiveTo": "{{$isoTimestamp}}"
          }
        }

        or
        {
          "properties": {
            "class": "DataClassProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "description": "add description here",
            "namespace": "add scope of this data class's applicability.",
            "matchPropertyNames": [
              "name1",
              "name2"
            ],
            "matchThreshold": 0,
            "specification": "",
            "specificationDetails": {
              "property1": "propertyValue1",
              "property2": "propertyValue2"
            },
            "dataType": "",
            "allowsDuplicateValues": true,
            "isNullable": false,
            "defaultValue": "",
            "averageValue": "",
            "valueList": [],
            "valueRangeFrom": "",
            "valueRangeTo": "",
            "sampleValues": [],
            "dataPatterns": [],
            "additionalProperties": {
              "property1": "propertyValue1",
              "property2": "propertyValue2"
            }
          }
        }

        """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._async_create_data_class(body))
        return response

    @dynamic_catch
    async def _async_create_data_class_from_template(self, body: dict | TemplateRequestBody) -> str:
        """
        Create a new metadata element to represent a data class using an existing metadata element as a template.
        The template defines additional classifications and relationships that should be added to the new element.
        Async version.

        Parameters
        ----------
        body: dict
            - a dictionary containing the properties of the data class to be created.

        Returns
        -------
        str
            The GUID of the element - or "No element found"

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----
        {
          "class" : "TemplateRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "anchorGUID" : "add guid here",
          "isOwnAnchor": false,
          "parentGUID": "add guid here",
          "parentRelationshipTypeName": "add type name here",
          "parentRelationshipProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "parentAtEnd1": false,
          "templateGUID": "add guid here",
          "replacementProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "placeholderPropertyValues":  {
            "placeholder1" : "propertyValue1",
            "placeholder2" : "propertyValue2"
          }
        }

        """

        url = f"{base_path(self, self.view_server)}/data-classes/from-template"
        return await self._async_create_element_from_template(url, body)

    @dynamic_catch
    def create_data_class_from_template(self, body: dict | TemplateRequestBody) -> str:
        """
        Create a new metadata element to represent a data class using an existing metadata element as a template.
        The template defines additional classifications and relationships that should be added to the new element.
        Async version.

        Parameters
        ----------
        body: dict
            - a dictionary containing the properties of the data class to be created.

        Returns
        -------
        str
            The GUID of the element - or "No element found"

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----
        {
          "class" : "TemplateRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "anchorGUID" : "add guid here",
          "isOwnAnchor": false,
          "parentGUID": "add guid here",
          "parentRelationshipTypeName": "add type name here",
          "parentRelationshipProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "parentAtEnd1": false,
          "templateGUID": "add guid here",
          "replacementProperties": {
            "class": "ElementProperties",
            "propertyValueMap" : {
              "description" : {
                "class": "PrimitiveTypePropertyValue",
                "typeName": "string",
                "primitiveValue" : "New description"
              }
            }
          },
          "placeholderPropertyValues":  {
            "placeholder1" : "propertyValue1",
            "placeholder2" : "propertyValue2"
          }
        }
        """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._async_create_data_class_from_template(body))
        return response

    @dynamic_catch
    async def _async_update_data_class(self, data_class_guid: str, body: dict | UpdateElementRequestBody,
                                       ) -> None:
        """
        Update the properties of a data class. Async version.

        Parameters
        ----------
        data_class_guid: str
            - the GUID of the data class to be updated.
        body: dict
            - a dictionary containing the properties of the data structure to be created.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----
        Full sample body:
        {
          "class" : "UpdateDataClassRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "properties": {
            "class" : "DataClassProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "description": "add description here",
            "namespace": "add scope of this data class's applicability.",
            "matchPropertyNames": ["name1", "name2"],
            "matchThreshold": 0,
            "specification": "",
            "specificationDetails": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            },
            "dataType": "",
            "allowsDuplicateValues": true,
            "isNullable": false,
            "defaultValue": "",
            "averageValue": "",
            "valueList": [],
            "valueRangeFrom": "",
            "valueRangeTo": "",
            "sampleValues": [],
            "dataPatterns" : [],
            "additionalProperties": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            }
          }
        }
        """

        url = f"{base_path(self, self.view_server)}/data-classes/{data_class_guid}/update"
        await self._async_update_element_body_request(url, ["DataClass"], body)
        logger.info(f"Data class {data_class_guid} updated.")

    @dynamic_catch
    def update_data_class(self, data_class_guid: str, body: dict | UpdateElementRequestBody) -> None:
        """
        Update the properties of a data class.

        Parameters
        ----------
        data_class_guid: str
            - the GUID of the data class to be updated.
        body: dict
            - a dictionary containing the properties of the data structure to be created.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        {
          "class" : "UpdateDataClassRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime" : "{{$isoTimestamp}}",
          "forLineage" : false,
          "forDuplicateProcessing" : false,
          "properties": {
            "class" : "DataClassProperties",
            "qualifiedName": "add unique name here",
            "displayName": "add short name here",
            "description": "add description here",
            "namespace": "add scope of this data class's applicability.",
            "matchPropertyNames": ["name1", "name2"],
            "matchThreshold": 0,
            "specification": "",
            "specificationDetails": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            },
            "dataType": "",
            "allowsDuplicateValues": true,
            "isNullable": false,
            "defaultValue": "",
            "averageValue": "",
            "valueList": [],
            "valueRangeFrom": "",
            "valueRangeTo": "",
            "sampleValues": [],
            "dataPatterns" : [],
            "additionalProperties": {
              "property1" : "propertyValue1",
              "property2" : "propertyValue2"
            }
          }
        }
        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_update_data_class(data_class_guid, body))

    @dynamic_catch
    async def _async_link_nested_data_class(self, parent_data_class_guid: str, child_data_class_guid: str,
                                            body: dict | NewRelationshipRequestBody = None) -> None:
        """
        Connect two data classes to show that one is used by the other when it is validating (typically a complex
        data item). Request body is optional. Async version.

        Parameters
        ----------
        parent_data_class_guid: str
            - the GUID of the parent data class the nested data class will be connected to.
        child_data_class_guid: str
            - the GUID of the nested data class to be connected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        url = (f"{base_path(self, self.view_server)}/data-classes/{parent_data_class_guid}"
               f"/nested-data-classes/{child_data_class_guid}/attach")

        await self._async_new_relationship_request(url, ["MemberDataClassProperties"], body)
        logger.info(f"Data field {child_data_class_guid} attached to Data structure {parent_data_class_guid}.")

    @dynamic_catch
    def link_nested_data_class(self, parent_data_class_guid: str, child_data_class_guid: str,
                               body: dict | NewRelationshipRequestBody = None) -> None:
        """
        Connect a nested data class to a data class. Request body is optional.

        Parameters
        ----------
        parent_data_class_guid: str
            - the GUID of the parent data class the nested data class will be connected to.
        child_data_class_guid: str
            - the GUID of the nested data class to be connected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

            {
              "class": "MetadataSourceRequestBody",
              "externalSourceGUID": "add guid here",
              "externalSourceName": "add qualified name here",
              "effectiveTime": "{{$isoTimestamp}}",
              "forLineage": false,
              "forDuplicateProcessing": false
            }

        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_link_nested_data_class(parent_data_class_guid, child_data_class_guid, body))

    @dynamic_catch
    async def _async_detach_nested_data_class(self, parent_data_class_guid: str, child_data_class_guid: str,
                                              body: dict | DeleteRelationshipRequestBody = None,
                                              cascade_delete: bool = False) -> None:
        """
        Detach two nested data classes from each other. Request body is optional. Async version.

        Parameters
        ----------
        parent_data_class_guid: str
            - the GUID of the parent data class the data class will be detached from..
        child_data_class_guid: str
            - the GUID of the data class to be disconnected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

       {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }


        """

        url = (f"{base_path(self, self.view_server)}/data-classes/{parent_data_class_guid}"
               f"/nested-data-classes/{child_data_class_guid}/detach")

        await self._async_delete_relationship_request(url, body, cascade_delete)
        logger.info(f"Data Class {child_data_class_guid} detached from data structure {parent_data_class_guid}.")

    @dynamic_catch
    def detach_nested_data_class(self, parent_data_class_guid: str, child_data_class_guid: str,
                                 body: dict | DeleteRelationshipRequestBody = None, cascade_delete: bool = False) -> None:
        """
        Detach two nested data classes from each other. Request body is optional.

        Parameters
        ----------
        parent_data_class_guid: str
            - the GUID of the parent data structure the data class will be detached fromo.
        child_data_class_guid: str
            - the GUID of the data class to be disconnected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self._async_detach_nested_data_class(parent_data_class_guid, child_data_class_guid, body, cascade_delete))

    @dynamic_catch
    async def _async_link_specialized_data_class(self, parent_data_class_guid: str, child_data_class_guid: str,
                                                 body: dict | NewRelationshipRequestBody = None, ) -> None:
        """
        Connect two data classes to show that one provides a more specialist evaluation. Request body is optional.
        Async version.

        Parameters
        ----------
        parent_data_class_guid: str
            - the GUID of the parent data class the nested data class will be connected to.
        child_data_class_guid: str
            - the GUID of the nested data class to be connected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        url = (f"{base_path(self, self.view_server)}/data-classes/{parent_data_class_guid}"
               f"/specialized-data-classes/{child_data_class_guid}/attach")

        await self._async_new_relationship_request(url, ["DataClassHierarchyProperties"], body)
        logger.info(f"Data field {child_data_class_guid} attached to Data structure {parent_data_class_guid}.")

    @dynamic_catch
    def link_specialized_data_class(self, parent_data_class_guid: str, child_data_class_guid: str,
                                    body: dict | NewRelationshipRequestBody = None) -> None:
        """
        Connect two data classes to show that one provides a more specialist evaluation. Request body is optional.

        Parameters
        ----------
        parent_data_class_guid: str
            - the GUID of the parent data class the nested data class will be connected to.
        child_data_class_guid: str
            - the GUID of the nested data class to be connected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self._async_link_specialized_data_class(parent_data_class_guid, child_data_class_guid, body))

    @dynamic_catch
    async def _async_detach_specialized_data_class(self, parent_data_class_guid: str, child_data_class_guid: str,
                                                   body: dict | DeleteRelationshipRequestBody = None,
                                                   cascade_delete: bool = False) -> None:
        """
        Detach two data classes from each other. Request body is optional. Async version.

        Parameters
        ----------
        parent_data_class_guid: str
            - the GUID of the parent data class the data class will be detached from..
        child_data_class_guid: str
            - the GUID of the data class to be disconnected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

       {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }


        """

        url = (f"{base_path(self, self.view_server)}/data-classes/{parent_data_class_guid}"
               f"/specialized-data-classes/{child_data_class_guid}/detach")

        await self._async_delete_relationship_request(url, body, cascade_delete)
        logger.info(f"Data field {child_data_class_guid} detached from data structure {parent_data_class_guid}.")

    @dynamic_catch
    def detach_specialized_data_class(self, parent_data_class_guid: str, child_data_class_guid: str,
                                      body: dict | DeleteRelationshipRequestBody = None, cascade_delete: bool = False) -> None:
        """
        Detach two data classes from each other. Request body is optional.

        Parameters
        ----------
        parent_data_class_guid: str
            - the GUID of the parent data structure the data class will be detached from.
        child_data_class_guid: str
            - the GUID of the data class to be disconnected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self._async_detach_specialized_data_class(parent_data_class_guid, child_data_class_guid, body,
                                                      cascade_delete))

    @dynamic_catch
    async def _async_delete_data_class(self, data_class_guid: str, body: dict | DeleteElementRequestBody = None,
                                       cascade_delete: bool = False) -> None:
        """
        Delete a data class. Request body is optional. Async version.

        Parameters
        ----------
        data_class_guid: str
            - the GUID of the data class to delete.
        body: dict, optional
            - a dictionary containing additional properties.
        cascade: bool, optional
            - if True, then the delete cascades to dependents


        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:

       {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }


        """

        url = f"{base_path(self, self.view_server)}/data-classes/{data_class_guid}/delete"

        await self._async_delete_element_request(url, body, cascade_delete)
        logger.info(f"Data structure {data_class_guid} deleted.")

    @dynamic_catch
    def delete_data_class(self,
                          data_class_guid: str,
                          body: dict | DeleteElementRequestBody = None,
                          cascade_delete: bool = False) -> None:
        """
        Delete a data class. Request body is optional.

        Parameters
        ----------
        data_class_guid: str
            - the GUID of the data class the data class to delete.
        body: dict, optional
            - a dictionary containing additional properties.
        cascade: bool, optional
            - if True, then the delete cascades to dependents


        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Full sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_delete_data_class(data_class_guid, body, cascade_delete))

    @dynamic_catch
    async def _async_find_all_data_classes(self,
                                           output_format: str = 'JSON',
                                           report_spec: str | dict = None) -> list | str:
        """ Returns a list of all data classes. Async version.

        Parameters
        ----------
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.


        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict elements with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        """

        url = f"{base_path(self, self.view_server)}/data-classes/by-search-string"

        return self.find_data_classes(search_string="*", output_format=output_format,
                                      report_spec=report_spec)

    @dynamic_catch
    def find_all_data_classes(self,
                              output_format: str = 'JSON', report_spec: str | dict = None) -> list | str:
        """ Returns a list of all data classes.

        Parameters
        ----------
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict elements with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self._async_find_all_data_classes(output_format, report_spec))
        return response

    @dynamic_catch
    async def _async_find_data_classes(self, search_string: str, start_from: int = 0, page_size: int = max_paging_size,
                                       starts_with: bool = True, ends_with: bool = False, ignore_case: bool = True,
                                       output_format: str = 'JSON', report_spec: str | dict = None,
                                       body: dict | SearchStringRequestBody = None) -> list | str:
        """ Find the list of data class elements that contain the search string.
            Async version.

        Parameters
        ----------
        filter: str
            - search string to filter on.
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        starts_with: bool, default = True
            - if True, the search string filters from the beginning of the string.
        ends_with: bool, default = False
            - if True, the search string filters from the end of the string.
        ignore_case: bool, default = True
            - If True, the case of the search string is ignored.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.


        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        """

        url = f"{base_path(self, self.view_server)}/data-classes/by-search-string"
        return await self._async_find_request(url, "DataClass", self._generate_data_class_output,
                                              search_string, start_from=start_from, page_size=page_size,
                                              starts_with=starts_with, ends_with=ends_with, ignore_case=ignore_case,
                                              body=body, output_format=output_format,
                                              report_spec=report_spec)

    @dynamic_catch
    def find_data_classes(self, search_string: str, start_from: int = 0, page_size: int = max_paging_size,
                          starts_with: bool = True, ends_with: bool = False, ignore_case: bool = True,
                          output_format: str = 'JSON', report_spec: str | dict = None,
                          body: dict | SearchStringRequestBody = None) -> list | str:
        """ Retrieve the list of data fields elements that contain the search string filter.

        Parameters
        ----------
        filter: str
            - search string to filter on.
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        starts_with: bool, default = True
            - if True, the search string filters from the beginning of the string.
        ends_with: bool, default = False
            - if True, the search string filters from the end of the string.
        ignore_case: bool, default = True
            - If True, the case of the search string is ignored.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.


        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict  with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.


    """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self._async_find_data_classes(search_string, start_from, page_size, starts_with, ends_with, ignore_case,
                                          output_format, report_spec, body))
        return response

    @dynamic_catch
    async def _async_get_data_classes_by_name(self, filter_string: str, classification_names: list[str],
                                              body: dict | FilterRequestBody = None, start_from: int = 0,
                                              page_size: int = 0,
                                              output_format: str = 'JSON',
                                              report_spec: str | dict = None) -> list | str:
        """ Get the list of data class metadata elements with a matching name to the search string filter.
            Async version.

        Parameters
        ----------
        filter: str
            - search string to filter on.
        body: dict, optional
            - a dictionary containing additional properties to use in the request.
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.
        Notes
        -----

        {
          "class": "FilterRequestBody",
          "asOfTime": "{{$isoTimestamp}}",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false,
          "limitResultsByStatus": ["ACTIVE"],
          "sequencingOrder": "PROPERTY_ASCENDING",
          "sequencingProperty": "qualifiedName",
          "filter": "Add name here"
        }
        """

        url = f"{base_path(self, self.view_server)}/data-classes/by-name"

        response = await self._async_get_name_request(url, _type="DataClass",
                                                      _gen_output=self._generate_data_class_output,
                                                      filter_string=filter_string,
                                                      classification_names=classification_names,
                                                      start_from=start_from, page_size=page_size,
                                                      output_format=output_format, report_spec=report_spec,
                                                      body=body)

        return response

    @dynamic_catch
    def get_data_classes_by_name(self, filter_string: str, classification_names: list[str] = None,
                                 body: dict | FilterRequestBody = None, start_from: int = 0,
                                 page_size: int = max_paging_size, output_format: str = 'JSON',
                                 report_spec: str | dict = None) -> list | str:
        """ Get the list of data class elements with a matching name to the search string filter.

        Parameters
        ----------
        filter: str
            - search string to filter on.
        body: dict, optional
            - a dictionary containing additional properties to use in the request.
        start_from: int, default = 0
            - index of the list to start from (0 for start).
        page_size
            - maximum number of elements to return.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.


        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Notes
        -----
        {
          "class": "FilterRequestBody",
          "asOfTime": "{{$isoTimestamp}}",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false,
          "limitResultsByStatus": ["ACTIVE"],
          "sequencingOrder": "PROPERTY_ASCENDING",
          "sequencingProperty": "qualifiedName",
          "filter": "Add name here"
        }

    """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self._async_get_data_classes_by_name(filter_string, classification_names, body,
                                                 start_from, page_size, output_format, report_spec
                                                 ))
        return response

    @dynamic_catch
    async def _async_get_data_class_by_guid(self, guid: str, element_type: str = None,
                                            body: dict | GetRequestBody = None,
                                            output_format: str = 'JSON',
                                            report_spec: str | dict = None) -> list | str:
        """ Get the  data class elements for the specified GUID.
            Async version.

        Parameters
        ----------
        guid: str
            - unique identifier of the data class metadata element.
        body: dict, optional
            - optional request body.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict  with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Notes
        ----

        Optional request body:
        {
          "class": "AnyTimeRequestBody",
          "asOfTime": "{{$isoTimestamp}}",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        url = (f"{base_path(self, self.view_server)}/data-classes/{guid}/retrieve")
        type = element_type if element_type else "DataClass"

        response = await self._async_get_guid_request(url, _type=type,
                                                      _gen_output=self._generate_data_class_output,
                                                      output_format=output_format, report_spec=report_spec,
                                                      body=body)
        return response

    @dynamic_catch
    def get_data_class_by_guid(self, guid: str, element_type: str = None, body: dict | FilterRequestBody = None,
                               output_format: str = 'JSON',
                               report_spec: str | dict = None) -> list | str:
        """ Get the  data structure metadata element with the specified unique identifier..

        Parameters
        ----------
        guid: str
            - unique identifier of the data structure metadata element.
        body: dict, optional
            - optional request body.
        output_format: str, default = "DICT"
            - output format of the data structure. Possible values: "DICT", "JSON", "MERMAID".
        report_spec: str|dict, optional, default = None
            - The desired output columns/field options.

        Returns
        -------
        [dict] | str
            Returns a string if no elements are found and a list of dict  with the results.

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Notes
        ----

        Optional request body:
        {
          "class": "AnyTimeRequestBody",
          "asOfTime": "{{$isoTimestamp}}",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

    """

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self._async_get_data_class_by_guid(guid, element_type, body, output_format, report_spec))
        return response

    ###
    # =====================================================================================================================
    # Assembling a data specification
    # https://egeria-project.org/concepts/data-specification
    #
    @dynamic_catch
    async def _async_link_data_class_definition(self, data_definition_guid: str, data_class_guid: str,
                                                body: dict | NewRelationshipRequestBody = None) -> None:
        """
         Connect an element that is part of a data design to a data class to show that the data class should be used as
         the specification for the data values when interpreting the data definition. Request body is optional.
         Async version
        Parameters
        ----------
        data_definition_guid: str
            - the GUID of the data class definition to link.
        data_class_guid: str
            - the GUID of the data class to be connected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        url = (f"{base_path(self, self.view_server)}/data-definitions/{data_definition_guid}"
               f"/data-class-definition/{data_class_guid}/attach")

        await self._async_new_relationship_request(url, ["DataClassDefinitionProperties"], body)
        logger.info(f"Data class {data_class_guid} attached to Data definition {data_definition_guid}.")

    @dynamic_catch
    def link_data_class_definition(self, data_definition_guid: str, data_class_guid: str,
                                   body: dict | NewRelationshipRequestBody = None) -> None:
        """
         Connect an element that is part of a data design to a data class to show that the data class should be used as
         the specification for the data values when interpreting the data definition. Request body is optional.
         Async version
        Parameters
        ----------
        data_definition_guid: str
            - the GUID of the data class definition to link.
        data_class_guid: str
            - the GUID of the data class to be connected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_link_data_class_definition(data_definition_guid, data_class_guid, body))

    @dynamic_catch
    async def _async_detach_data_class_definition(self, data_definition_guid: str, data_class_guid: str,
                                                  body: dict | DeleteRelationshipRequestBody = None,
                                                  cascade_delete: bool = False) -> None:
        """
        Detach a data definition from a data class. Request body is optional. Async version.

        Parameters
        ----------
        data_definition_guid: str
            - the GUID of the data class definition.
        data_class_guid: str
            - the GUID of the data class to be disconnected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

       {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }


        """

        url = (f"{base_path(self, self.view_server)}/data-definitions/{data_definition_guid}"
               f"/data-class-definition/{data_class_guid}/detach")

        await self._async_delete_relationship_request(url, body, cascade_delete)
        logger.info(f"Data class {data_class_guid} detached from data definition {data_definition_guid}.")

    @dynamic_catch
    def detach_data_class_definition(self, data_definition_guid: str, data_class_guid: str,
                                     body: dict | DeleteRelationshipRequestBody = None, cascade_delete: bool = False) -> None:
        """
        Detach a data definition from a data class. Request body is optional.

        Parameters
        ----------
        data_definition_guid: str
            - the GUID of the data class definition.
        data_class_guid: str
            - the GUID of the data class to be disconnected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

       {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }


        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self._async_detach_data_class_definition(data_definition_guid, data_class_guid, body, cascade_delete))

    @dynamic_catch
    async def _async_link_semantic_definition(self, data_definition_guid: str, glossary_term_guid: str,
                                              body: dict | NewRelationshipRequestBody = None) -> None:
        """
        Connect an element that is part of a data design to a glossary term to show that the term should be used as
        the semantic definition for the data values when interpreting the data definition. Request body is optional.
        Async version

        Parameters
        ----------
        data_definition_guid: str
            - the GUID of the data class definition to link.
        glossary_term_guid: str
            - the GUID of the glossary term to be connected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        url = (f"{base_path(self, self.view_server)}/data-definitions/{data_definition_guid}"
               f"/semantic-definition/{glossary_term_guid}/attach")

        await self._async_new_relationship_request(url, ["SemanticDefinitionProperties"], body)
        logger.info(f"Data class {data_definition_guid} attached to term definition {glossary_term_guid}.")

    @dynamic_catch
    def link_semantic_definition(self, data_definition_guid: str, glossary_term_guid: str,
                                 body: dict | NewRelationshipRequestBody = None) -> None:
        """
        Connect an element that is part of a data design to a glossary term to show that the term should be used as
        the semantic definition for the data values when interpreting the data definition. Request body is optional.
        Async version

        Parameters
        ----------
        data_definition_guid: str
            - the GUID of the data class definition to link.
        glossary_term_guid: str
            - the GUID of the glossary term to be connected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_link_semantic_definition(data_definition_guid, glossary_term_guid, body))

    @dynamic_catch
    async def _async_detach_semantic_definition(self, data_definition_guid: str, glossary_term_guid: str,
                                                body: dict | DeleteRelationshipRequestBody = None,
                                                cascade_delete: bool = False) -> None:
        """
        Detach a data definition from a glossary term. Request body is optional. Async version.

        Parameters
        ----------
        data_definition_guid: str
            - the GUID of the data class definition.
        glossary_term_guid: str
            - the GUID of the glossary term to be disconnected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

       {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }


        """

        url = (f"{base_path(self, self.view_server)}/data-definitions/{data_definition_guid}"
               f"/semantic-definition/{glossary_term_guid}/detach")
        await self._async_delete_relationship_request(url, body, cascade_delete)
        logger.info(f"Data definition {data_definition_guid} detached from term {glossary_term_guid}.")

    @dynamic_catch
    def detach_semantic_definition(self, data_definition_guid: str, glossary_term_guid: str,
                                   body: dict | DeleteRelationshipRequestBody = None, cascade_delete: bool = False) -> None:
        """
        Detach a data definition from a glossary term. Request body is optional.

        Parameters
        ----------
        data_definition_guid: str
            - the GUID of the data class definition.
        glossary_term_guid: str
            - the GUID of the glossary term to be disconnected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

       {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }


        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self._async_detach_semantic_definition(data_definition_guid, glossary_term_guid, body, cascade_delete))



    async def _async_link_certification_type_to_data_structure(self, certification_type_guid: str,
                                                               data_structure_guid: str, body: dict | NewRelationshipRequestBody = None) -> None:
        """
         Connect a certification type to a data structure to guide the survey action service (that checks the data
         quality of a data resource as part of certifying it with the supplied certification type) to the definition
         of the data structure to use as a specification of how the data should be both structured and (if data
        classes are attached to the associated data fields using the DataClassDefinition relationship) contain the
        valid values. Request body is optional.
         Async version

        Parameters
        ----------
        certification_type_guid: str
            - the GUID of the certification type to link.
        data_structure_guid: str
            - the GUID of the data structure to be connected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        url = (f"{base_path(self, self.view_server)}/certification-types/{certification_type_guid}"
               f"/data-structure-definition/{data_structure_guid}/attach")
        await self._async_new_relationship_request(url, ["CertificationTypeProperties"], body)
        logger.info(f"Certification type {certification_type_guid} linked to {data_structure_guid}.")


    def link_certification_type_to_data_structure(self, certification_type_guid: str, data_structure_guid: str,
                                                  body: dict |NewRelationshipRequestBody = None) -> None:
        """
        Connect a certification type to a data structure to guide the survey action service (that checks the data
         quality of a data resource as part of certifying it with the supplied certification type) to the definition
         of the data structure to use as a specification of how the data should be both structured and (if data
        classes are attached to the associated data fields using the DataClassDefinition relationship) contain the
        valid values. Request body is optional.

        Parameters
        ----------
        certification_type_guid: str
            - the GUID of the certification type to link.
        data_structure_guid: str
            - the GUID of the data structure to be connected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self._async_link_certification_type_to_data_structure(certification_type_guid, data_structure_guid, body))

    async def _async_detach_certification_type_from_data_structure(self, certification_type_guid: str,
                                                                   data_structure_guid: str, body: dict | DeleteRelationshipRequestBody = None, cascade_delete: bool = False) -> None:
        """
        Detach a data structure from a certification type. Request body is optional. Async version.

        Parameters
        ----------
        certification_type_guid: str
            - the GUID of the certification type to link.
        data_structure_guid: str
            - the GUID of the data structure to be connected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        url = (f"{base_path(self, self.view_server)}/certification-stypes/{certification_type_guid}"
               f"/data-structure-definition/{data_structure_guid}/detach")

        await self._async_delete_relationship_request(url, body, cascade_delete)
        logger.info(f"Certification type {certification_type_guid} detached from data structure {data_structure_guid}.")


    def detach_certification_type_from_data_structure(self, certification_type_guid: str, data_structure_guid: str,
                                                      body: dict | DeleteRelationshipRequestBody= None, cascade_delete: bool = False) -> None:
        """
        Detach a data structure from a certification type. Request body is optional.

        Parameters
        ----------
        certification_type_guid: str
            - the GUID of the certification type to link.
        data_structure_guid: str
            - the GUID of the data structure to be connected.
        body: dict, optional
            - a dictionary containing additional properties.

        Returns
        -------
        None

        Raises
        ------
        InvalidParameterException
            one of the parameters is null or invalid or
        PropertyServerException
            There is a problem adding the element properties to the metadata repository or
        UserNotAuthorizedException
            the requesting user is not authorized to issue this request.

        Note
        ----

        Sample body:

        {
          "class": "MetadataSourceRequestBody",
          "externalSourceGUID": "add guid here",
          "externalSourceName": "add qualified name here",
          "effectiveTime": "{{$isoTimestamp}}",
          "forLineage": false,
          "forDuplicateProcessing": false
        }

        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self._async_detach_certification_type_from_data_structure(certification_type_guid, data_structure_guid,
                                                                      body, cascade_delete))




    def _extract_data_structure_properties(self, element: dict, columns_struct: dict) -> dict:
        """Extractor for Data Structure elements with related overlay.

        Pattern:
        - Populate common columns via populate_common_columns.
        - Derive related properties using get_data_rel_elements_dict from the element body.
        - Overlay values into matching columns' 'value' fields, handling formats as list or dict.
        - Return the enriched columns_struct.
        """
        col_data = populate_common_columns(element, columns_struct)

        try:
            related_map = self.get_data_rel_elements_dict(element)
        except Exception:
            related_map = {}

        if isinstance(related_map, dict) and related_map:
            try:
                formats = col_data.get("formats") if isinstance(col_data, dict) else None
                if isinstance(formats, list):
                    targets = formats
                elif isinstance(formats, dict):
                    inner = formats.get("formats") if isinstance(formats.get("formats"), (dict, list)) else None
                    if isinstance(inner, list):
                        targets = inner
                    elif isinstance(inner, dict):
                        targets = [inner]
                    else:
                        targets = [formats]
                else:
                    targets = []

                if targets:
                    for fmt in targets:
                        cols = fmt.get("attributes", []) if isinstance(fmt, dict) else []
                        for col in cols:
                            key = col.get("key") if isinstance(col, dict) else None
                            if key and key in related_map:
                                col["value"] = related_map.get(key)
                else:
                    cols = col_data.get("attributes", []) if isinstance(col_data, dict) else []
                    for col in cols:
                        key = col.get("key") if isinstance(col, dict) else None
                        if key and key in related_map:
                            col["value"] = related_map.get(key)
            except Exception:
                pass

        return col_data


    def _extract_data_class_properties(self, element: dict,columns_struct: dict) -> dict:
        """Extractor for Data Class elements with related overlay, mirroring Data Field pattern."""
        col_data = populate_common_columns(element, columns_struct)

        try:
            related_map = self.get_data_rel_elements_dict(element)
        except Exception:
            related_map = {}

        if isinstance(related_map, dict) and related_map:
            try:
                formats = col_data.get("formats") if isinstance(col_data, dict) else None
                if isinstance(formats, list):
                    targets = formats
                elif isinstance(formats, dict):
                    inner = formats.get("formats") if isinstance(formats.get("formats"), (dict, list)) else None
                    if isinstance(inner, list):
                        targets = inner
                    elif isinstance(inner, dict):
                        targets = [inner]
                    else:
                        targets = [formats]
                else:
                    targets = []

                if targets:
                    for fmt in targets:
                        cols = fmt.get("attributes", []) if isinstance(fmt, dict) else []
                        for col in cols:
                            key = col.get("key") if isinstance(col, dict) else None
                            if key and key in related_map:
                                col["value"] = related_map.get(key)
                else:
                    cols = col_data.get("attributes", []) if isinstance(col_data, dict) else []
                    for col in cols:
                        key = col.get("key") if isinstance(col, dict) else None
                        if key and key in related_map:
                            col["value"] = related_map.get(key)
            except Exception:
                pass

        return col_data

    def _extract_data_field_properties(self, element: dict, columns_struct: dict) -> dict:
        """Extractor for Data Field elements.
        
        Steps:
        - Populate base/referenceable/common properties into columns_struct via populate_common_columns.
        - Derive related properties using get_data_rel_elements_dict from the element body.
        - For each column in columns_struct, if its 'key' matches a key from the related dict, set its 'value'.
        - Return the enriched columns_struct.
        """
        # 1) Populate common columns first (header, properties, basic relationships, mermaid)
        col_data = populate_common_columns(element, columns_struct)
        
        # 2) Build a map of related properties/elements from the body. The Data Designer methods
        #    return a body that may include keys like assignedMeanings, otherRelatedElements,
        #    memberOfCollections, memberDataFields, assignedDataClasses, nestedDataClasses, etc.
        try:
            related_map = self.get_data_rel_elements_dict(element)
        except Exception:
            related_map = {}
        
        if isinstance(related_map, dict) and related_map:
            # 3) Walk the configured columns and overlay values when the key matches an entry from related_map
            try:
                formats = col_data.get("formats") if isinstance(col_data, dict) else None
                if isinstance(formats, list):
                    targets = formats
                elif isinstance(formats, dict):
                    # Handle dict variant. It may be a single format dict or a wrapper containing 'formats'.
                    # Examples seen:
                    #   { 'attributes': [...] }
                    #   { 'types': 'ALL', 'attributes': [...] }
                    #   { 'formats': { 'attributes': [...] } }
                    inner = formats.get("formats") if isinstance(formats.get("formats"), dict | list) else None
                    if isinstance(inner, list):
                        targets = inner
                    elif isinstance(inner, dict):
                        targets = [inner]
                    else:
                        targets = [formats]
                else:
                    targets = []
        
                if targets:
                    for fmt in targets:
                        cols = fmt.get("attributes", []) if isinstance(fmt, dict) else []
                        for col in cols:
                            key = col.get("key") if isinstance(col, dict) else None
                            if key and key in related_map:
                                col["value"] = related_map.get(key)
                else:
                    # If attributes are on the top-level (non-standard), attempt to handle gracefully
                    cols = col_data.get("attributes", []) if isinstance(col_data, dict) else []
                    for col in cols:
                        key = col.get("key") if isinstance(col, dict) else None
                        if key and key in related_map:
                            col["value"] = related_map.get(key)
            except Exception:
                # Do not fail rendering due to overlay issues; keep the base columns
                pass
        
        return col_data

    def _generate_basic_structured_output(self, elements: dict, filter: str, type: str = None ,output_format: str = 'DICT',
                                          columns_struct: dict = None) -> str | list:
        """
        Generate output in the specified format for the given elements.

        Args:
            elements: Dictionary or list of dictionaries containing element data
            filter: The search string used to find the elements
            output_format: The desired output format (MD, FORM, REPORT, LIST, DICT, MERMAID, HTML)
            columns_struct: dict, optional, default = None
                - The columns/attributes options to use
        Returns:
            Formatted output as string or list of dictionaries
        """
        # Handle MERMAID and DICT formats using existing methods
        if output_format == "MERMAID":
            return extract_mermaid_only(elements)
        elif output_format == "DICT":
            return extract_basic_dict(elements)
        elif output_format == "HTML":
            return generate_output(
                elements=elements,
                search_string=filter,
                entity_type="Data Element",
                columns_struct=columns_struct,
                output_format="HTML",
                extract_properties_func=self._extract_data_structure_properties
                )

        # For other formats (MD, FORM, REPORT, LIST), use generate_output
        elif output_format in ["MD", "FORM", "REPORT", "LIST"]:
            # Define columns for LIST format

            return generate_output(elements,
                                   filter,
                                   "Data Element",
                                   output_format,
                                   self._extract_data_structure_properties,
                                   None,
                                   columns_struct,
                                   )

    def _generate_data_structure_output(self, elements: dict | list[dict], filter: str = None, type: str = None,
                                        output_format: str = "DICT",
                                        report_spec: str | dict = None) -> str | list:
        """
        Generate output for data structures in the specified format.

        Args:
            elements: Dictionary or list of dictionaries containing data structure elements
            filter: The search string used to find the elements
            output_format: The desired output format (MD, FORM, REPORT, LIST, DICT, MERMAID, HTML)

        Returns:
            Formatted output as string or list of dictionaries
        """
        entity_type = "Data Structure"
        if report_spec is None:
            report_spec = select_report_spec(entity_type, output_format)

        if report_spec:
            if isinstance(report_spec, str):
                output_formats = select_report_spec(report_spec, output_format)
            elif isinstance(report_spec, dict):
                output_formats = get_report_spec_match(report_spec, output_format)
        else:
            output_formats = None
        logger.trace(f"Executing _generate_data_structure_output for {entity_type}: {output_formats}")
        return generate_output(elements,
                               filter,
                               entity_type,
                               output_format,
                               self._extract_data_structure_properties,
                               None,
                               output_formats,
                               )

    def _generate_data_class_output(self, elements: dict | list[dict], filter: str = None, type: str = None, output_format: str = "DICT",
                                    report_spec: str | dict = None) -> str | list:
        """
        Generate output for data classes in the specified format.

        Args:
            elements: Dictionary or list of dictionaries containing data class elements
            filter: The search string used to find the elements
            output_format: The desired output format (MD, FORM, REPORT, LIST, DICT, MERMAID, HTML)
            report_spec: Optional output format set
                - Option column/attribute selection and definition.
        Returns:
            Formatted output as either a string or list of dictionaries
        """
        entity_type = "Data Class"
        if report_spec is None:
            report_spec = select_report_spec(entity_type, output_format)

        if report_spec:
            if isinstance(report_spec, str):
                output_formats = select_report_spec(report_spec, output_format)
            if isinstance(report_spec, dict):
                output_formats = get_report_spec_match(report_spec, output_format)
        else:
            output_formats = None
        logger.trace(f"Executing _generate_data_class_output for {entity_type}: {output_formats}")
        return generate_output(elements,
                               filter,
                               entity_type,
                               output_format,
                               self._extract_data_class_properties,
                               None,
                               output_formats,
                               )

    def _generate_data_field_output(self, elements: dict | list[dict], filter: str = None, type: str = None, output_format: str = "DICT",
                                    report_spec: str | dict = None) -> str | list:
        """
        Generate output for data fields in the specified format.

        Args:
            elements: Dictionary or list of dictionaries containing data field elements
            filter: The search string used to find the elements
            output_format: The desired output format (MD, FORM, REPORT, LIST, DICT, MERMAID, HTML)
            report_spec: str|dict, Optional, default = None
            - Option column/attribute selection and definition.

        Returns:
            Formatted output as a string or list of dictionaries
        """
        entity_type = "Data Field"
        if report_spec is None:
            report_spec = select_report_spec(entity_type, output_format)

        if report_spec:
            if isinstance(report_spec, str):
                output_formats = select_report_spec(report_spec, output_format)
            if isinstance(report_spec, dict):
                output_formats = get_report_spec_match(report_spec, output_format)
        else:
            output_formats = None
        logger.trace(f"Executing _generate_data_field_output for {entity_type}: {output_formats}")
        return generate_output(elements,
                               filter,
                               entity_type,
                               output_format,
                               self._extract_data_field_properties,
                               None,
                               output_formats,
                               )

    def _extract_additional_data_struct_properties(self, element, columns_struct):
        return None
    def _extract_additional_data_field_properties(self, element, columns_struct):
        return None
    def _extract_additional_data_class_properties(self, element, columns_struct):
        return None

if __name__ == "__main__":
    print("Data Designer")
