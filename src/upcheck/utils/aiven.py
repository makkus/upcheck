# -*- coding: utf-8 -*-
import copy
import os
from typing import Any, Mapping, Optional

import aiopg
from aiopg import Connection
from aiven.client import AivenClient
from upcheck.exceptions import UpcheckException
from upcheck.utils import create_temp_dir_with_text_files
from upcheck.utils.kafka import UpcheckKafkaClient


API_URL = "https://api.aiven.io"


class UpcheckAivenClient(object):
    def __init__(self, token_or_account_password: str, email: Optional[str] = None):
        """Aiven client wrapper class.

        This class only exposes and consolidates the minimal necessary functions of the underlying Aiven client, which is needed for
         'upcheck's functionality.

        If only the 'token_or_access_password' arg is specified, token authentication will be used, if also 'email' is
        provided, the first argument will be interpreted as the account password, and a 'full' authentication will be done.

        Args:

            token_or_account_password (str): the account token or password
            email (Optional[str]): the email address
        """

        self._token_or_account_password: Optional[str] = token_or_account_password
        self._email: Optional[str] = email

        self._client = AivenClient(base_url=API_URL, show_http=False)
        if self._email:
            result = self._client.authenticate_user(
                email=email, password=token_or_account_password
            )
            # TODO: save to filesystem for subsequent logins
            self._auth_token = result["token"]
        else:
            self._auth_token = self._token_or_account_password

        self._client.set_auth_token(self._auth_token)

    def get_project_details(
        self, project_name: Optional[str] = None
    ) -> Mapping[str, Any]:

        if project_name is None:
            projects = self._client.get_projects()
            if len(projects) != 1:
                raise UpcheckException(
                    msg="Can't retrieve details for default project.",
                    reason="More than one projects exists, and no project name specified.",
                    solution="Please specify a project name.",
                )

            return projects[0]

        for details in self._client.get_projects():

            if details["project_name"] == project_name:
                return details

        raise UpcheckException(
            msg=f"Can't retrieve details for project '{project_name}'",
            reason="No project with that name exists.",
            solution="Check whether the project name is correct, and whether the project actually exists.",
        )

    def get_raw_service_details(
        self,
        service_type: Optional[str] = None,
        project_name: Optional[str] = None,
        service_name: Optional[str] = None,
    ):

        project_details = self.get_project_details(project_name=project_name)
        project_name = project_details["project_name"]

        if service_name is not None:

            try:
                service_details = self._client.get_service(project_name, service_name)

                if service_type:
                    if service_details["service_type"] != service_type:
                        raise UpcheckException(
                            msg=f"Can't retrieve service details for service '{service_name}'.",
                            reason=f"Invalid service type '{service_details['service_type']}' (requested: {service_type})",
                        )

                service_details["project"] = project_details
                return service_details
            except Exception as e:
                raise UpcheckException(
                    msg=f"Can't retrieve details for service '{service_name}'.",
                    reason=str(e),
                )
        else:

            services = self._client.get_services(project_name)

            if not service_type and len(services) != 1:
                raise UpcheckException(
                    msg="Can't retrieve details for service.",
                    reason="Neither 'service_type' nor 'service_name' specified, and more than one services exist.",
                )
            elif not service_type:
                return services[0]

            service_list = []
            for service in services:

                if service["service_type"] == service_type:
                    service_list.append(service)

            if not service_list:
                raise UpcheckException(
                    msg=f"Can't retrieve details for default {service_type} service.",
                    reason=f"No {service_type} service exist in project {project_name}.",
                    solution=f"Create a {service_type} service in your project.",
                )

            if len(service_list) == 1:
                service_details = service_list[0]
                service_details["project"] = project_details
                return service_details

            raise UpcheckException(
                msg=f"Can't retrieve details for default {service_type} service.",
                reason=f"More than one {service_type} services exist in project {project_name}, and no service name specified.",
                solution="Please specify a service name.",
            )

    def get_kafka_service_details(
        self,
        project_name: Optional[str] = None,
        service_name: Optional[str] = None,
        kafka_username: Optional[str] = None,
    ):

        kafka_service = self.get_raw_service_details(
            project_name=project_name, service_name=service_name, service_type="kafka"
        )

        project_name = kafka_service["project"]["project_name"]
        project_ca_pem: str = self._client.get_project_ca(project_name)["certificate"]

        host = kafka_service["service_uri_params"]["host"]
        port = int(kafka_service["service_uri_params"]["port"])

        users = kafka_service["users"]
        if not users:
            raise UpcheckException(
                msg="Can't create kafka service configuration.",
                reason="No users configured for service '{}'",
            )
        if kafka_username is None:
            kafka_username = users[0]["username"]

        user_details: Optional[Mapping[str, Any]] = None
        for _user in kafka_service["users"]:
            if _user["username"] == kafka_username:
                user_details = _user
                break

        if user_details is None:
            raise UpcheckException(
                msg="Can't create kafka service configuration.",
                reason=f"No service user '{kafka_username}'.",
            )

        access_key = user_details["access_key"]
        access_cert = user_details["access_cert"]

        return {
            "host": host,
            "port": port,
            "access_key": access_key,
            "access_cert": access_cert,
            "ca_cert": project_ca_pem,
        }

    def get_postgres_service_details(
        self,
        project_name: Optional[str] = None,
        service_name: Optional[str] = None,
        postgres_username: Optional[str] = None,
    ):

        postgres_service = self.get_raw_service_details(
            project_name=project_name, service_name=service_name, service_type="pg"
        )
        project_name = postgres_service["project"]["project_name"]

        project_ca_pem: str = self._client.get_project_ca(project_name)["certificate"]

        details = copy.copy(postgres_service["service_uri_params"])
        details["ca_cert"] = project_ca_pem
        if postgres_username:
            _u = None
            for user in postgres_service["users"]:
                if user["username"] == postgres_username:
                    _u = user
                    break

            if _u is None:
                raise UpcheckException(
                    "Can't create postgres service details.",
                    reason=f"No user '{postgres_username}' exists for postgres service '{postgres_service['service_name']}'.",
                )

            details["user"] = postgres_username
            details["password"] = _u["password"]

        return details

    def create_kafka_client(
        self,
        topic: str,
        group_id: Optional[str] = None,
        project_name: Optional[str] = None,
        service_name: Optional[str] = None,
    ) -> UpcheckKafkaClient:

        kafka_service_details: Mapping[str, Any] = self.get_kafka_service_details(
            project_name=project_name, service_name=service_name
        )

        ca_cert = kafka_service_details["ca_cert"]
        access_cert = kafka_service_details["access_cert"]
        access_key = kafka_service_details["access_key"]

        temp_dir = create_temp_dir_with_text_files(
            {"ca.pem": ca_cert, "service.cert": access_cert, "service.key": access_key}
        )

        kafka_client_config = {
            "host": kafka_service_details["host"],
            "port": kafka_service_details["port"],
            "topic": topic,
            "group_id": group_id,
            "cafile": os.path.join(temp_dir, "ca.pem"),
            "certfile": os.path.join(temp_dir, "service.cert"),
            "keyfile": os.path.join(temp_dir, "service.key"),
        }

        kafka_client = UpcheckKafkaClient(**kafka_client_config)
        return kafka_client

    async def create_postgres_connection(
        self,
        dbname: str,
        user: Optional[str] = None,
        project_name: Optional[str] = None,
        service_name: Optional[str] = None,
    ) -> Connection:

        postgres_service_details: Mapping[str, Any] = self.get_postgres_service_details(
            postgres_username=user, project_name=project_name, service_name=service_name
        )

        ca_cert = postgres_service_details["ca_cert"]
        temp_dir = create_temp_dir_with_text_files({"ca.pem": ca_cert})

        postgres_config = {
            "user": postgres_service_details["user"],
            "password": postgres_service_details["password"],
            "host": postgres_service_details["host"],
            "port": postgres_service_details["port"],
            "dbname": dbname,
            "sslmode": "verify-ca",
            "sslrootcert": os.path.join(temp_dir, "ca.pem"),
        }

        connection: Connection = await aiopg.connect(**postgres_config)
        return connection
