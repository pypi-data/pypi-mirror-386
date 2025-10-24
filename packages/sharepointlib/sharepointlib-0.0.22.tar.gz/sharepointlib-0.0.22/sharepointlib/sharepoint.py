"""
This library provides access to some SharePoint functionalities.
Its features are designed to remain generic and should not be modified to meet
the specific needs of individual projects.
"""

# import base64
import dataclasses
import json
import logging
from typing import Any, Type
from urllib.parse import quote
import requests

# TypeAdapter v2 vs parse_obj_as v1
from pydantic import BaseModel, parse_obj_as  # pylint: disable=no-name-in-module
from .models import (
    GetSiteInfo,
    GetHostNameInfo,
    ListDrives,
    GetDirInfo,
    ListDir,
    CreateDir,
    RenameFolder,
    GetFileInfo,
    MoveFile,
    RenameFile,
    UploadFile,
    ListLists,
    ListListColumns,
    AddListItem,
)

# Creates a logger for this module
logger = logging.getLogger(__name__)


class SharePoint(object):
    """
    SharePoint client to interact with SharePoint via Microsoft Graph API.
    """

    @dataclasses.dataclass
    class Configuration:
        """Configuration dataclass for SharePoint client."""

        api_domain: str | None = None
        api_version: str | None = None
        sp_domain: str | None = None
        client_id: str | None = None
        tenant_id: str | None = None
        client_secret: str | None = None
        token: str | None = None

    @dataclasses.dataclass
    class Response:
        """Response dataclass for SharePoint client methods."""

        status_code: int
        content: Any = None

    def __init__(
        self,
        client_id: str,
        tenant_id: str,
        client_secret: str,
        sp_domain: str,
        custom_logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialize the SharePoint client.

        Args:
            client_id (str): The Azure client ID used for authentication.
            tenant_id (str): The Azure tenant ID associated with the client.
            client_secret (str): The secret key for the Azure client.
            sp_domain (str): The SharePoint domain. Example: "companygroup.sharepoint.com"
            custom_logger (logging.Logger, optional): Logger instance to use. If None, a default logger is created.
        """
        # Init logging
        # Use provided logger or create a default one
        self._logger = custom_logger or logging.getLogger(name=__name__)

        # Init variables
        self._session: requests.Session = requests.Session()
        api_domain = "graph.microsoft.com"
        api_version = "v1.0"

        # Credentials/Configuration
        self._configuration = self.Configuration(
            api_domain=api_domain,
            api_version=api_version,
            sp_domain=sp_domain,
            client_id=client_id,
            tenant_id=tenant_id,
            client_secret=client_secret,
            token=None,
        )

        # Authenticate
        self.auth()

    def __del__(self) -> None:
        """
        Cleans the house at the exit.
        """
        self._logger.info(msg="Cleans the house at the exit")
        self._session.close()

    def auth(self) -> None:
        """
        Authentication.

        This method performs the authentication process to obtain an access token using the client credentials flow.
        The token is stored in the Configuration dataclass for subsequent API requests.
        """
        self._logger.info(msg="Authentication")

        # Request headers
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # Authorization URL
        url_auth = f"https://login.microsoftonline.com/{self._configuration.tenant_id}/oauth2/v2.0/token"

        # Request body
        body = {
            "grant_type": "client_credentials",
            "client_id": self._configuration.client_id,
            "client_secret": self._configuration.client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }

        # Request
        response = self._session.post(url=url_auth, data=body, headers=headers, verify=True)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Return valid response
        if response.status_code == 200:
            self._configuration.token = json.loads(response.content.decode("utf-8"))["access_token"]

    def _export_to_json(self, content: bytes, save_as: str | None) -> None:
        """
        Export response content to a JSON file.

        This method takes the content to be exported and saves it to a specified file in JSON format.
        If the `save_as` parameter is provided, the content will be written to that file.

        Args:
            content (bytes): The content to be exported, typically the response content from an API call.
            save_as (str): The file path where the JSON content will be saved. If None, the content will not be saved.
        """
        if save_as is not None:
            self._logger.info(msg="Exports response to JSON file.")
            with open(file=save_as, mode="wb") as file:
                file.write(content)

    def _handle_response(
        self, response: requests.Response, model: Type[BaseModel], rtype: str = "scalar"
    ) -> dict | list[dict]:
        """
        Handle and deserialize the JSON content from an API response.

        This method processes the response from an API request and deserializes the JSON content into a Pydantic
        BaseModel or a list of BaseModel instances, depending on the response type.

        Args:
            response (requests.Response): The response object from the API request.
            model (Type[BaseModel]): The Pydantic BaseModel class to use for deserialization and validation.
            rtype (str, optional): The type of response to handle. Use "scalar" for a single record and "list" for a
              list of records. Defaults to "scalar".

        Returns:
            dict or list[dict]: The deserialized content as a dictionary (scalar) or a list of dictionaries (list).
        """
        if rtype.lower() == "scalar":
            # Deserialize json (scalar values)
            content_raw = response.json()
            # Pydantic v1 validation
            validated = model(**content_raw)
            # Convert to dict
            return validated.dict()

        # List of records
        # Deserialize json
        content_raw = response.json()["value"]
        # Pydantic v1 validation
        validated_list = parse_obj_as(list[model], content_raw)
        # return [dict(data) for data in parse_obj_as(list[model], content_raw)]
        # Convert to a list of dicts
        return [item.dict() for item in validated_list]

    def get_site_info(self, name: str, save_as: str | None = None) -> Response:
        """
        Get the site ID for a given site name.

        This method sends a request to the Microsoft Graph API to retrieve the site ID associated with the specified
        site name. If the request is successful, it will return the site ID along with the HTTP status code.
        Optionally, the response can be saved to a JSON file.

        Args:
            name (str): The name of the site for which to retrieve the site ID.
            save_as (str, optional): The file path where the response will be saved in JSON format. If not provided, the
              response will not be saved.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and the content, which includes
              the site ID and other relevant information.
        """
        self._logger.info(msg="Gets the site ID for a given site name")
        self._logger.info(msg=name)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version
        sp_domain = self._configuration.sp_domain

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        # get_sites_id: url_query = f"https://graph.microsoft.com/v1.0/sites?search='{filter}'"
        url_query = rf"https://{api_domain}/{api_version}/sites/{sp_domain}:/sites/{name}"

        # Query parameters
        # Pydantic v1
        alias_list = [field.alias for field in GetSiteInfo.__fields__.values() if field.field_info.alias is not None]
        params = {"$select": ",".join(alias_list)}

        # Request
        response = self._session.get(url=url_query, headers=headers, params=params, verify=True)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code == 200:
            self._logger.info(msg="Request successful")

            # Export response to json file
            self._export_to_json(content=response.content, save_as=save_as)

            # Deserialize json (scalar values)
            content = self._handle_response(response=response, model=GetSiteInfo, rtype="scalar")

        return self.Response(status_code=response.status_code, content=content)

    def get_hostname_info(self, site_id: str, save_as: str | None = None) -> Response:
        """
        Get the hostname and site details for a specified site ID.

        This method sends a request to the Microsoft Graph API to retrieve the hostname, site name, and other relevant
        details associated with the specified site ID. If the request is successful, it will return the site information
        along with the HTTP status code. Optionally, the response can be saved to a JSON file.

        Args:
            site_id (str): The ID of the site for which to retrieve the hostname and details.
            save_as (str, optional): The file path where the response will be saved in JSON format. If not provided, the
              response will not be saved.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and the content, which includes
              the hostname, site name, and other relevant information.
        """
        self._logger.info(msg="Gets the hostname and site details for a specified site ID")
        self._logger.info(msg=site_id)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        url_query = rf"https://{api_domain}/{api_version}/sites/{site_id}"

        # Query parameters
        # Pydantic v1
        alias_list = [
            field.alias for field in GetHostNameInfo.__fields__.values() if field.field_info.alias is not None
        ]
        params = {"$select": ",".join(alias_list)}

        # Request
        response = self._session.get(url=url_query, headers=headers, params=params, verify=True)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code == 200:
            self._logger.info(msg="Request successful")

            # Export response to json file
            self._export_to_json(content=response.content, save_as=save_as)

            # Deserialize json (scalar values)
            content = self._handle_response(response=response, model=GetHostNameInfo, rtype="scalar")

        return self.Response(status_code=response.status_code, content=content)

    # DRIVES
    def list_drives(self, site_id: str, save_as: str | None = None) -> Response:
        """
        Get a list of the Drive IDs for a given site ID.

        This method sends a request to the Microsoft Graph API to retrieve the Drive IDs associated with the specified
        site ID. If the request is successful, it will return the Drive IDs along with the HTTP status code. Optionally,
        the response can be saved to a JSON file.

        Args:
            site_id (str): The ID of the site for which to retrieve the Drive IDs.
            save_as (str, optional): The file path where the response will be saved in JSON format. If not provided, the
              response will not be saved.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and the content, which includes
              the list of Drive IDs and other relevant information.
        """
        self._logger.info(msg="Gets a list of the Drive IDs for a given site")
        self._logger.info(msg=site_id)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        url_query = rf"https://{api_domain}/{api_version}/sites/{site_id}/drives"

        # Query parameters
        # Pydantic v1
        alias_list = [field.alias for field in ListDrives.__fields__.values() if field.field_info.alias is not None]
        params = {"$select": ",".join(alias_list)}

        # Request
        response = self._session.get(url=url_query, headers=headers, params=params, verify=True)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code == 200:
            self._logger.info(msg="Request successful")

            # Export response to json file
            self._export_to_json(content=response.content, save_as=save_as)

            # Deserialize json
            content = self._handle_response(response=response, model=ListDrives, rtype="list")

        return self.Response(status_code=response.status_code, content=content)

    def get_dir_info(self, drive_id: str, path: str | None = None, save_as: str | None = None) -> Response:
        """
        Get the folder ID for a specified folder within a drive ID.

        This method sends a request to the Microsoft Graph API to retrieve the folder ID associated with the specified
        folder path within the given drive ID. If the request is successful, it will return the folder ID along with the
        HTTP status code. Optionally, the response can be saved to a JSON file.

        Args:
            drive_id (str): The ID of the drive where the folder is located.
            path (str, optional): The path of the folder for which to retrieve the folder ID. If not provided, the root
              folder will be used.
            save_as (str, optional): The file path where the response will be saved in JSON format. If not provided, the
              response will not be saved.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and the content, which includes
              the folder ID and other relevant information.
        """
        self._logger.info(msg="Gets the folder ID for a specified folder within a drive")
        self._logger.info(msg=drive_id)
        self._logger.info(msg=path)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        path_quote = "///" if path is None else f"/{quote(string=path)}"
        url_query = rf"https://{api_domain}/{api_version}/drives/{drive_id}/root:{path_quote}"
        # print(url_query)

        # Query parameters
        # Pydantic v1
        alias_list = [field.alias for field in GetDirInfo.__fields__.values() if field.field_info.alias is not None]
        params = {"$select": ",".join(alias_list)}

        # Request
        response = self._session.get(url=url_query, headers=headers, params=params, verify=True)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code == 200:
            self._logger.info(msg="Request successful")

            # Export response to json file
            self._export_to_json(content=response.content, save_as=save_as)

            # Deserialize json (scalar values)
            content = self._handle_response(response=response, model=GetDirInfo, rtype="scalar")

        return self.Response(status_code=response.status_code, content=content)

    def list_dir(self, drive_id: str, path: str | None = None, save_as: str | None = None) -> Response:
        """
        List content (files and folders) of a specific folder.

        This method sends a request to the Microsoft Graph API to retrieve the list of children (files and folders)
        within a specified folder in a drive. If the request is successful, it will return the HTTP status code and a
        list of the children.

        Args:
            drive_id (str): The ID of the drive containing the folder.
            path (str, optional): The path of the folder for which to list the children. If not provided, the root
              folder will be used.
            save_as (str, optional): If provided, the results will be saved to a JSON file at the specified path.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and a list of children
              (files and folders) within the specified folder.
        """
        self._logger.info(msg="List content (files and folders) of a folder")
        self._logger.info(msg=drive_id)
        self._logger.info(msg=path)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        path_quote = "/" if path is None else f"{quote(string=path)}"
        url_query = rf"https://{api_domain}/{api_version}/drives/{drive_id}/items/root:/{path_quote}:/children"
        # print(url_query)

        # Query parameters
        # Pydantic v1
        alias_list = [field.alias for field in ListDir.__fields__.values() if field.field_info.alias is not None]
        params = {"$select": ",".join(alias_list)}

        # Request
        response = self._session.get(url=url_query, headers=headers, params=params, verify=True)
        # print(response.content)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code == 200:
            self._logger.info(msg="Request successful")

            # Export response to json file
            self._export_to_json(content=response.content, save_as=save_as)

            # Deserialize json (scalar values)
            content = self._handle_response(response=response, model=ListDir, rtype="list")

            # Add path to each item
            for item in content:
                item["path"] = path or "/"

        return self.Response(status_code=response.status_code, content=content)

    def create_dir(self, drive_id: str, path: str, name: str, save_as: str | None = None) -> Response:
        """
        Create a new folder in a specified drive ID.

        This method sends a request to the Microsoft Graph API to create a new folder at the specified path within the
        given drive ID. If the request is successful, it will return the HTTP status code and the details of the created
        folder. Optionally, the response can be saved to a JSON file.

        Args:
            drive_id (str): The ID of the drive where the folder will be created.
            path (str): The path of the new folder to be created.
            name (str): The name of the new folder to be created.
            save_as (str, optional): The file path where the response will be saved in JSON format. If not provided, the
              response will not be saved.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and the content, which includes
              the details of the created folder.
        """
        self._logger.info(msg="Creates a new folder in a specified drive")
        self._logger.info(msg=drive_id)
        self._logger.info(msg=path)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        path_quote = quote(string=path)
        url_query = rf"https://{api_domain}/{api_version}/drives/{drive_id}/root:/{path_quote}:/children"

        # Query parameters
        # Pydantic v1
        alias_list = [field.alias for field in CreateDir.__fields__.values() if field.field_info.alias is not None]
        params = {"$select": ",".join(alias_list)}

        # Request body
        # @microsoft.graph.conflictBehavior: fail, rename, replace
        data = {
            "name": name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "replace",
        }

        # Request
        response = self._session.post(url=url_query, headers=headers, params=params, json=data, verify=True)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code in (200, 201):
            self._logger.info(msg="Request successful")

            # Export response to json file
            self._export_to_json(content=response.content, save_as=save_as)

            # Deserialize json (scalar values)
            content = self._handle_response(response=response, model=CreateDir, rtype="scalar")

        return self.Response(status_code=response.status_code, content=content)

    def delete_dir(self, drive_id: str, path: str) -> Response:
        """
        Delete a folder from a specified drive ID.

        This method sends a request to the Microsoft Graph API to delete a folder located at the specified path within
        the given drive ID. If the request is successful, it will return the HTTP status code and the details of the
        deleted folder. Optionally, the response can be saved to a JSON file.

        Args:
            drive_id (str): The ID of the drive containing the folder to be deleted.
            path (str): The full path of the folder to be deleted.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and the content, which includes
              the details of the deleted folder.
        """
        self._logger.info(msg="Deletes a folder from a specified drive")
        self._logger.info(msg=drive_id)
        self._logger.info(msg=path)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        path_quote = quote(string=path)
        url_query = rf"https://{api_domain}/{api_version}/drives/{drive_id}/root:/{path_quote}"

        # Request
        response = self._session.delete(url=url_query, headers=headers, verify=True)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code in (200, 204):
            self._logger.info(msg="Request successful")

        return self.Response(status_code=response.status_code, content=content)

    def rename_folder(self, drive_id: str, path: str, new_name: str, save_as: str | None = None) -> Response:
        """
        Rename a folder in a specified drive ID.

        This method sends a PATCH request to the Microsoft Graph API to rename a folder.

        Args:
            drive_id (str): The ID of the drive containing the folder to be renamed.
            path (str): The full path of the folder to be renamed.
            new_name (str): The new name for the folder.
            save_as (str, optional): The file path where the response will be saved in JSON format.

        Returns:
            Response: A Response dataclass instance with the status code and content.
        """
        self._logger.info(msg="Renames a folder in a specified drive")
        self._logger.info(msg=drive_id)
        self._logger.info(msg=path)
        self._logger.info(msg=new_name)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        path_quote = quote(string=path)
        url_query = rf"https://{api_domain}/{api_version}/drives/{drive_id}/root:/{path_quote}"

        # Request body
        data = {"name": new_name}

        alias_list = [field.alias for field in RenameFolder.__fields__.values() if field.field_info.alias is not None]
        params = {"$select": ",".join(alias_list)}

        # Request
        response = self._session.patch(url=url_query, headers=headers, params=params, json=data, verify=True)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code == 200:
            self._logger.info(msg="Request successful")

            # Export response to json file
            self._export_to_json(content=response.content, save_as=save_as)

            # Deserialize json (scalar values)
            content = self._handle_response(response=response, model=RenameFolder, rtype="scalar")

        return self.Response(status_code=response.status_code, content=content)

    def get_file_info(self, drive_id: str, filename: str, save_as: str | None = None) -> Response:
        """
        Retrieve information about a specific file in a drive ID.

        This method sends a request to the Microsoft Graph API to obtain details about a file located at the specified
        path within the given drive ID. If the request is successful, it will return the file information along with the
        HTTP status code. Optionally, the response can be saved to a JSON file.

        Args:
            drive_id (str): The ID of the drive containing the file.
            filename (str): The full path of the file for which to retrieve information, including the filename.
            save_as (str, optional): The file path where the response will be saved in JSON format. If not provided, the
              response will not be saved.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and the content, which includes
              the file details such as ID, name, web URL, size, created date, and last modified date.
        """
        self._logger.info(msg="Retrieves information about a specific file")
        self._logger.info(msg=drive_id)
        self._logger.info(msg=filename)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        filename_quote = quote(string=filename)
        url_query = rf"https://{api_domain}/{api_version}/drives/{drive_id}/root:/{filename_quote}"

        # Query parameters
        # Pydantic v1
        alias_list = [field.alias for field in GetFileInfo.__fields__.values() if field.field_info.alias is not None]
        params = {"$select": ",".join(alias_list)}

        # Request
        response = self._session.get(url=url_query, headers=headers, params=params, verify=True)
        # print(response.content)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code in (200, 202):
            self._logger.info(msg="Request successful")

            # Export response to json file
            self._export_to_json(content=response.content, save_as=save_as)

            # Deserialize json (scalar values)
            content = self._handle_response(response=response, model=GetFileInfo, rtype="scalar")

        return self.Response(status_code=response.status_code, content=content)

    def copy_file(self, drive_id: str, filename: str, target_path: str, new_name: str | None = None) -> Response:
        """
        Copy a file from one folder to another within the same drive ID.

        This method sends a request to the Microsoft Graph API to copy a file from the specified source path to the
        destination path within the given drive ID. It works only on the same drive. If the request is successful, it
        will return the HTTP status code and the details of the moved file.

        Args:
            drive_id (str): The ID of the drive containing the file to be copied.
            filename (str): The full path of the file to be copied, including the filename.
            target_path (str): The path of the destination folder where the file will be copied.
            new_name (str, optional): The new name for the copied file. If not provided, the file keeps its original
              name.

        Returns:
            Response: An instance of the Response class containing the HTTP status code.
        """
        self._logger.info(msg="Copy a file from one folder to another within the same drive")
        self._logger.info(msg=drive_id)
        self._logger.info(msg=filename)
        self._logger.info(msg=target_path)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        filename_quote = quote(string=filename)
        url_query = rf"https://{api_domain}/{api_version}/drives/{drive_id}/root:/{filename_quote}:/copy"

        # Request body
        data = {
            "parentReference": {
                "driveId": drive_id,
                "driveType": "documentLibrary",
                "path": f"/drives/{drive_id}/root:/{target_path}",
            }
        }
        # Add to the request body if new_name is provided
        if new_name is not None:
            data["name"] = new_name  # type: ignore

        # Request
        response = self._session.post(url=url_query, headers=headers, json=data, verify=True)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code in (200, 202):
            self._logger.info(msg="Request successful")

        return self.Response(status_code=response.status_code, content=content)

    def move_file(
        self, drive_id: str, filename: str, target_path: str, new_name: str | None = None, save_as: str | None = None
    ) -> Response:
        """
        Move a file from one folder to another within the same drive ID.

        This method sends a request to the Microsoft Graph API to move a file from the specified source path to the
        destination path within the given drive ID. It works only on the same drive. If the request is successful, it
        will return the HTTP status code and the details of the moved file. Optionally, the response can be saved to a
        JSON file.

        Args:
            drive_id (str): The ID of the drive containing the file to be moved.
            filename (str): The full path of the file to be moved, including the filename.
            target_path (str): The path of the destination folder where the file will be moved.
            new_name (str, optional): The new name for the file after moving. If not provided, the file keeps its
              original name.
            save_as (str, optional): The file path where the response will be saved in JSON format. If not provided, the
              response will not be saved.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and the content, which includes
              the details of the moved file.
        """
        self._logger.info(msg="Moves a file from one folder to another within the same drive")
        self._logger.info(msg=drive_id)
        self._logger.info(msg=filename)
        self._logger.info(msg=target_path)

        # Source file: Uses the get_file_info function to obtain the source file_id
        file_info_response = self.get_file_info(drive_id=drive_id, filename=filename, save_as=None)

        if file_info_response.status_code != 200:
            content = None
            return self.Response(status_code=file_info_response.status_code, content=content)

        # Destination folder: Uses the get_dir_info function to obtain the source folder_id
        dir_info_response = self.get_dir_info(drive_id=drive_id, path=target_path, save_as=None)

        if dir_info_response.status_code != 200:
            content = None
            return self.Response(status_code=dir_info_response.status_code, content=content)

        # Do the move
        file_id = file_info_response.content["id"]
        folder_id = dir_info_response.content["id"]

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        url_query = rf"https://{api_domain}/{api_version}/drives/{drive_id}/items/{file_id}"

        # Request body
        data = {"parentReference": {"id": folder_id}}
        # Add to the request body if new_name is provided
        if new_name is not None:
            data["name"] = new_name  # type: ignore

        # Query parameters
        # Pydantic v1
        alias_list = [field.alias for field in MoveFile.__fields__.values() if field.field_info.alias is not None]
        params = {"$select": ",".join(alias_list)}

        # Request
        response = self._session.patch(url=url_query, headers=headers, params=params, json=data, verify=True)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code == 200:
            self._logger.info(msg="Request successful")

            # Export response to json file
            self._export_to_json(content=response.content, save_as=save_as)

            # Deserialize json (scalar values)
            content = self._handle_response(response=response, model=MoveFile, rtype="scalar")

        return self.Response(status_code=response.status_code, content=content)

    def delete_file(self, drive_id: str, filename: str) -> Response:
        """
        Delete a file from a specified drive ID.

        This method sends a request to the Microsoft Graph API to delete a file located at the specified path within
        the given drive ID. If the request is successful, it will return the HTTP status code and the details of the
        deleted file. Optionally, the response can be saved to a JSON file.

        Args:
            drive_id (str): The ID of the drive containing the file to be deleted.
            filename (str): The full path of the file to be deleted, including the filename.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and the content, which includes
              the details of the deleted file.
        """
        self._logger.info(msg="Deletes a file from a specified drive")
        self._logger.info(msg=drive_id)
        self._logger.info(msg=filename)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        filename_quote = quote(string=filename)
        url_query = rf"https://{api_domain}/{api_version}/drives/{drive_id}/root:/{filename_quote}"

        # Request
        response = self._session.delete(url=url_query, headers=headers, verify=True)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code in (200, 204):
            self._logger.info(msg="Request successful")

        return self.Response(status_code=response.status_code, content=content)

    def rename_file(self, drive_id: str, filename: str, new_name: str, save_as: str | None = None) -> Response:
        """
        Rename a file in a specified drive ID.

        This method sends a request to the Microsoft Graph API to rename a file located at the specified path within the
        given drive ID. If the request is successful, it will return the HTTP status code and the details of the renamed
        file. Optionally, the response can be saved to a JSON file.

        Args:
            drive_id (str): The ID of the drive containing the file to be renamed.
            filename (str): The full path of the file to be renamed, including the filename.
            new_name (str): The new name for the file.
            save_as (str, optional): The file path where the response will be saved in JSON format. If not provided, the
              response will not be saved.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and the content, which includes
              the details of the renamed file.
        """
        self._logger.info(msg="Renames a file in a specified drive")
        self._logger.info(msg=drive_id)
        self._logger.info(msg=filename)
        self._logger.info(msg=new_name)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        filename_quote = quote(string=filename)
        url_query = rf"https://{api_domain}/{api_version}/drives/{drive_id}/root:/{filename_quote}"

        # Request body
        data = {"name": new_name}

        # Query parameters
        # Pydantic v1
        alias_list = [field.alias for field in RenameFile.__fields__.values() if field.field_info.alias is not None]
        params = {"$select": ",".join(alias_list)}

        # Request
        response = self._session.patch(url=url_query, headers=headers, params=params, json=data, verify=True)
        # print(response.content)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code == 200:
            self._logger.info(msg="Request successful")

            # Export response to json file
            self._export_to_json(content=response.content, save_as=save_as)

            # Deserialize json (scalar values)
            content = self._handle_response(response=response, model=RenameFile, rtype="scalar")

        return self.Response(status_code=response.status_code, content=content)

    def download_file(self, drive_id: str, remote_path: str, local_path: str) -> Response:
        """
        Download a file from a specified remote path in a drive ID to a local path.

        This method sends a request to the Microsoft Graph API to download a file located at the specified remote path
        within the given drive ID. The file will be saved to the specified local path on the machine running the code.
        If the request is successful, it will return the HTTP status code and a response indicating the result of the
        operation.

        Args:
            drive_id (str): The ID of the drive containing the file.
            remote_path (str): The path of the file in the SharePoint drive, including the filename.
            local_path (str): The local file path where the downloaded file will be saved.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and content indicating the
              result of the download operation.
        """
        self._logger.info(msg="Downloads a file from a specified remote path in a drive to a local path")
        self._logger.info(msg=drive_id)
        self._logger.info(msg=remote_path)
        self._logger.info(msg=local_path)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {"Authorization": f"Bearer {token}"}

        # Request query
        remote_path_quote = quote(string=remote_path)
        url_query = rf"https://{api_domain}/{api_version}/drives/{drive_id}/root:/{remote_path_quote}:/content"

        # Request
        response = self._session.get(url=url_query, headers=headers, stream=True, verify=True)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code == 200:
            self._logger.info(msg="Request successful")

            # Create file
            with open(file=local_path, mode="wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)

        return self.Response(status_code=response.status_code, content=content)

    def download_file_to_memory(self, drive_id: str, remote_path: str) -> Response:
        """
        Download a file from a specified remote path in a drive ID to memory.

        Note that large files will require a significant amount of memory!
        This method sends a request to the Microsoft Graph API to download a file located at the specified remote path
        within the given drive ID. The file content is stored in a variable and returned as part of the Response object.
        If the request is successful, it will return the HTTP status code and the file content.

        Args:
            drive_id (str): The ID of the drive containing the file.
            remote_path (str): The path of the file in the SharePoint drive, including the filename.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and the content, which includes
              the file data as bytes.
        """
        self._logger.info(msg="Downloads a file from a specified remote path in a drive to a variable")
        self._logger.info(msg=drive_id)
        self._logger.info(msg=remote_path)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {"Authorization": f"Bearer {token}"}

        # Request query
        remote_path_quote = quote(string=remote_path)
        url_query = rf"https://{api_domain}/{api_version}/drives/{drive_id}/root:/{remote_path_quote}:/content"

        # Request
        response = self._session.get(url=url_query, headers=headers, stream=True, verify=True)
        # print(response.content)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code == 200:
            self._logger.info(msg="Request successful")
            content = b"".join(response.iter_content(chunk_size=1024))
            file_size = len(content)
            self._logger.info(msg=f"{file_size} bytes downloaded")

        return self.Response(status_code=response.status_code, content=content)

    def download_all_files(self, drive_id: str, remote_path: str, local_path: str) -> Response:
        """
        Download all files from a specified folder to a local folder.

        Args:
            drive_id (str): The ID of the SharePoint drive.
            remote_path (str): The path of the folder in SharePoint.
            local_path (str): The local folder path where files will be saved.

        Returns:
            Response: A Response object containing the status code and a list with download results.
        """
        self._logger.info(msg="Downloading all files from folder")
        self._logger.info(msg=drive_id)
        self._logger.info(msg=remote_path)
        self._logger.info(msg=local_path)

        # List all items in the folder
        response = self.list_dir(drive_id=drive_id, path=remote_path)
        if response.status_code != 200:
            self._logger.error(msg="Failed to list folder contents")
            return self.Response(status_code=response.status_code, content=None)

        # Output
        items = response.content
        content = []
        if response.status_code == 200:
            for item in items:
                # Only files with extension
                if item.get("extension") is None:
                    continue

                filename = item.get("name")
                self._logger.info(msg=f"File {filename}")

                # Download file
                sub_response = self.download_file(
                    drive_id=drive_id,
                    remote_path=rf"{remote_path}/{filename}",
                    local_path=rf"{local_path}/{filename}",
                )

                # Status
                status = "pass" if sub_response.status_code == 200 else "fail"
                if status == "pass":
                    self._logger.info(msg="File downloaded successfully")
                else:
                    self._logger.warning(msg=f"Failed to download {filename}")

                content.append(
                    {
                        "id": item.get("id"),
                        "name": filename,
                        "extension": item.get("extension"),
                        "size": item.get("size"),
                        "path": item.get("path"),
                        "created_date_time": item.get("created_date_time"),
                        "last_modified_date_time": item.get("last_modified_date_time"),
                        "last_modified_by_name": item.get("last_modified_by_name"),
                        "last_modified_by_email": item.get("last_modified_by_email"),
                        "status": status,
                    }
                )

        return self.Response(status_code=response.status_code, content=content)

    def upload_file(self, drive_id: str, local_path: str, remote_path: str, save_as: str | None = None) -> Response:
        """
        Upload a file to a specified remote path in a SharePoint drive ID.

        This method sends a request to the Microsoft Graph API to upload a file from the local path to the specified
        remote path within the given drive ID. If the folder does not exist in SharePoint, it will be created. If the
        request is successful, it will return the HTTP status code and a response indicating the result of the
        operation.

        Args:
            drive_id (str): The ID of the drive where the file will be uploaded.
            local_path (str): The local file path of the file to be uploaded.
            remote_path (str): The path in the SharePoint drive where the file will be uploaded, including the filename.
            save_as (str, optional): If provided, the results will be saved to a JSON file at the specified path.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and content indicating the
              result of the upload operation.
        """
        self._logger.info(msg="Uploads a file to a specified remote path in a drive")
        self._logger.info(msg=drive_id)
        self._logger.info(msg=local_path)
        self._logger.info(msg=remote_path)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
        }

        # Request query
        remote_path_quote = quote(string=remote_path)
        url_query = rf"https://{api_domain}/{api_version}/drives/{drive_id}/root:/{remote_path_quote}:/content"

        # Query parameters
        # Pydantic v1
        alias_list = [field.alias for field in UploadFile.__fields__.values() if field.field_info.alias is not None]
        params = {"$select": ",".join(alias_list)}

        # Request body
        data = open(file=local_path, mode="rb").read()

        # Request
        response = self._session.put(url=url_query, headers=headers, params=params, data=data, verify=True)
        # print(response.content)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code in (200, 201):
            self._logger.info(msg="Request successful")

            # Export response to json file
            self._export_to_json(content=response.content, save_as=save_as)

            # Deserialize json (scalar values)
            content = self._handle_response(response=response, model=UploadFile, rtype="scalar")

        return self.Response(status_code=response.status_code, content=content)

    # LISTS
    def list_lists(self, site_id: str, save_as: str | None = None) -> Response:
        """
        Retrieve a list of SharePoint lists for a specified site.

        This method sends a request to the Microsoft Graph API to obtain details about the lists within the given site
        ID. If the request is successful, it will return the list information along with the HTTP status code.
        Optionally, the response can be saved to a JSON file.

        Example: list_lists(site_id="companygroup.sharepoint.com,1111a11e-...,...-ed11bff1baf1")

        Args:
            site_id (str): The ID of the site containing the lists.
            save_as (str, optional): The file path where the response will be saved in JSON format. If not provided, the
              response will not be saved.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and the content, which includes
              the list details such as ID, name, display name, description, web URL, created date, and last modified
              date.
        """
        self._logger.info(msg="Retrieves a list of lists for a specified site")
        self._logger.info(msg=site_id)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        url_query = rf"https://{api_domain}/{api_version}/sites/{site_id}/lists"

        # Query parameters
        # Pydantic v1
        alias_list = [field.alias for field in ListLists.__fields__.values() if field.field_info.alias is not None]
        params = {"$select": ",".join(alias_list)}

        # Request
        response = self._session.get(url=url_query, headers=headers, params=params, verify=True)
        # print(response.content)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code == 200:
            self._logger.info(msg="Request successful")

            # Export response to json file
            self._export_to_json(content=response.content, save_as=save_as)

            # Deserialize json
            content = self._handle_response(response=response, model=ListLists, rtype="list")

        return self.Response(status_code=response.status_code, content=content)

    def list_list_columns(self, site_id: str, list_id: str, save_as: str | None = None) -> Response:
        """
        Retrieve the columns from a specified list in SharePoint.

        This method sends a request to the Microsoft Graph API to retrieve the columns associated with the specified
        list ID within a site. If the request is successful, it will return the column details along with the HTTP
        status code. Optionally, the response can be saved to a JSON file.

        Example: list_list_columns(site_id="companygroup.sharepoint.com,1111a11e-...,...-ed11bff1baf1",
                                   list_id="e11f111b-1111-11a1-1111-11f11d1a11f1")

        Args:
            site_id (str): The ID of the site containing the list.
            list_id (str): The ID of the list for which to retrieve the columns.
            save_as (str, optional): The file path where the response will be saved in JSON format. If not provided, the
              response will not be saved.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and the content, which includes
              the column details such as ID, name, display name, description, column group, enforce unique values,
              hidden, indexed, read-only, and required.
        """
        self._logger.info(msg="Retrieves the columns from a specified list")
        self._logger.info(msg=site_id)
        self._logger.info(msg=list_id)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        url_query = rf"https://{api_domain}/{api_version}/sites/{site_id}/lists/{list_id}/columns"

        # Query parameters
        # Pydantic v1
        alias_list = [
            field.alias for field in ListListColumns.__fields__.values() if field.field_info.alias is not None
        ]
        params = {"$select": ",".join(alias_list)}

        # Request
        response = self._session.get(url=url_query, headers=headers, params=params, verify=True)
        # print(response.content)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code == 200:
            self._logger.info(msg="Request successful")

            # Export response to json file
            self._export_to_json(content=response.content, save_as=save_as)

            # Deserialize json
            content = self._handle_response(response=response, model=ListListColumns, rtype="list")

        return self.Response(status_code=response.status_code, content=content)

    def list_list_items(self, site_id: str, list_id: str, fields: dict, save_as: str | None = None) -> Response:
        """
        Retrieve the items from a specified list in SharePoint.

        This method sends a request to the Microsoft Graph API to retrieve the items associated with the specified list
        ID within a site. If the request is successful, it will return the item details along with the HTTP status code.
        Optionally, the response can be saved to a JSON file.

        Example: list_list_items(site_id="companygroup.sharepoint.com,1111a11e-...,...-ed11bff1baf1",
                                 list_id="e11f111b-1111-11a1-1111-11f11d1a11f1",
                                 fields="fields/Id,fields/Title,fields/Description")

        Args:
            site_id (str): The ID of the site containing the list.
            list_id (str): The ID of the list for which to retrieve the items.
            fields (dict): The fields to be retrieved for each item in the list.
            save_as (str, optional): The file path where the response will be saved in JSON format. If not provided, the
              response will not be saved.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and the content, which includes
              the item details such as ID, title, description, etc.
        """
        self._logger.info(msg="Retrieves the items from a specified list")
        self._logger.info(msg=site_id)
        self._logger.info(msg=list_id)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json;odata.metadata=none",
        }

        # Request query
        url_query = rf"https://{api_domain}/{api_version}/sites/{site_id}/lists/{list_id}/items"

        # Query parameters
        params = {"select": fields, "expand": "fields"}

        # Request
        response = self._session.get(url=url_query, headers=headers, params=params, verify=True)
        # print(response.content)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code == 200:
            self._logger.info(msg="Request successful")

            # Export response to json file
            self._export_to_json(content=response.content, save_as=save_as)

            # Deserialize json
            content = [item["fields"] for item in response.json()["value"]]

        return self.Response(status_code=response.status_code, content=content)

    def delete_list_item(self, site_id: str, list_id: str, item_id: str) -> Response:
        """
        Delete a specified item from a list in SharePoint.

        This method sends a request to the Microsoft Graph API to delete the item associated with the specified item ID
        within a list. If the request is successful, it will return the HTTP status code.

        Example: delete_list_item(site_id="companygroup.sharepoint.com,1111a11e-...,...-ed11bff1baf1",
                                  list_id="e11f111b-1111-11a1-1111-11f11d1a11f1",
                                  item_id="1")

        Args:
            site_id (str): The ID of the site containing the list.
            list_id (str): The ID of the list containing the item.
            item_id (str): The ID of the item to be deleted.

        Returns:
            Response: An instance of the Response class containing the HTTP status code.
        """
        self._logger.info(msg="Deletes a specified item from a list")
        self._logger.info(msg=site_id)
        self._logger.info(msg=list_id)
        self._logger.info(msg=item_id)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        url_query = rf"https://{api_domain}/{api_version}/sites/{site_id}/lists/{list_id}/items/{item_id}"

        # Request
        response = self._session.delete(url=url_query, headers=headers, verify=True)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code == 204:
            self._logger.info(msg="Request successful")

        return self.Response(status_code=response.status_code, content=content)

    def add_list_item(self, site_id: str, list_id: str, item: dict, save_as: str | None = None) -> Response:
        """
        Add a new item to a specified list in SharePoint.

        This method sends a request to the Microsoft Graph API to add a new item to the specified list ID within a site.
        If the request is successful, it will return the item details along with the HTTP status code. Optionally, the
        response can be saved to a JSON file.

        Example: add_list_item(site_id="companygroup.sharepoint.com,1111a11e-...,...-ed11bff1baf1",
                               list_id="e11f111b-1111-11a1-1111-11f11d1a11f1",
                               item={"Title": "Hello World"})

        Args:
            site_id (str): The ID of the site containing the list.
            list_id (str): The ID of the list to which the item will be added.
            item (dict): The item data to be added to the list. Example: {"Title": "Hello World"}
            save_as (str, optional): The file path where the response will be saved in JSON format. If not provided, the
              response will not be saved.

        Returns:
            Response: An instance of the Response class containing the HTTP status code and the content, which includes
              the details of the added list item.
        """
        self._logger.info(msg="Adds a new item to a specified list")
        self._logger.info(msg=site_id)
        self._logger.info(msg=list_id)

        # Configuration
        token = self._configuration.token
        api_domain = self._configuration.api_domain
        api_version = self._configuration.api_version

        # Request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Request query
        url_query = rf"https://{api_domain}/{api_version}/sites/{site_id}/lists/{list_id}/items"

        # Query parameters
        # Pydantic v1
        alias_list = [field.alias for field in AddListItem.__fields__.values() if field.field_info.alias is not None]
        params = {"$select": ",".join(alias_list)}

        # Request body
        # @microsoft.graph.conflictBehavior: fail, rename, replace
        data = {"fields": item}

        # Request
        response = self._session.post(url=url_query, headers=headers, json=data, params=params, verify=True)
        # print(response.content)

        # Log response code
        self._logger.info(msg=f"HTTP Status Code {response.status_code}")

        # Output
        content = None
        if response.status_code == 201:
            self._logger.info(msg="Request successful")

            # Export response to json file
            self._export_to_json(content=response.content, save_as=save_as)

            # Deserialize json (scalar values)
            content = self._handle_response(response=response, model=AddListItem, rtype="scalar")

        return self.Response(status_code=response.status_code, content=content)

# eom
