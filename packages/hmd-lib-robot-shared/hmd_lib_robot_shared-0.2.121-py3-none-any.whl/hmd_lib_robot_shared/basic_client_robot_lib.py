from importlib import import_module
from typing import List, Dict

import yaml
from robot.api.deco import keyword, library
from robot.api.logger import console

from hmd_cli_tools.cdktf_tools import DeploymentConfig
from hmd_cli_tools.hmd_cli_tools import (
    make_standard_name,
    get_deployer_target_session,
    get_session,
    get_cloud_region,
    get_account_session,
    get_neuronsphere_domain,
    get_secret,
)
from hmd_cli_tools.okta_tools import get_auth_token
from hmd_graphql_client import BaseClient
from hmd_graphql_client.hmd_rest_client import RestClient
from hmd_graphql_client.relationship_support import RelationshipSupport
from hmd_meta_types import Entity, Noun, Relationship
from hmd_schema_loader import DefaultLoader
from hmd_lib_auth.hmd_lib_auth import okta_service_account_token
from datetime import datetime


@library
class BasicClientLib:
    def __init__(
        self,
        instance_name,
        repo_name,
        deployment_id,
        environment,
        hmd_region,
        customer_code,
        account_number=None,
        okta_secret_name=None,
    ):
        self.instance_name = instance_name
        self.repo_name = repo_name
        self.deployment_id = deployment_id
        self.environment = environment
        self.hmd_region = hmd_region
        self.customer_code = customer_code
        self.account_number = account_number
        self.okta_secret_name = okta_secret_name
        self.standard_name = make_standard_name(
            instance_name,
            repo_name,
            deployment_id,
            environment,
            hmd_region,
            customer_code,
        )

        # Bender writes the instance configuration out here...
        with open("instance_configuration.yaml", "r") as fl:
            instance_config = yaml.safe_load(fl)

        dp_config = DeploymentConfig(instance_config)
        clients = self._make_clients(dp_config)
        self.rs = RelationshipSupport(clients=clients)
        self.local_client = clients[0]

    def _make_clients(self, dp_config):
        """Create a client for each loader specified in the loader configs. The must be
        a corresponding dependency that contains the information necessary to retrieve
        the api key.

        :param dp_config:
        :type dp_config:
        :return:
        :rtype:
        """

        service_loader = dp_config["service_config"]["service_loader"]
        loader_config = dp_config["service_config"]["loader_config"]
        language_packs = loader_config[service_loader]
        instance_name = dp_config["instance_name"]
        repo_name = dp_config["repo_name"]
        deployment_id = dp_config["deployment_id"]
        hmd_region = (
            dp_config["hmd_region"] if "hmd_region" in dp_config else self.hmd_region
        )
        local_client = self._make_client(
            instance_name, repo_name, deployment_id, hmd_region, language_packs
        )

        service_clients = [
            self._make_client(
                dp_config.get(f"{loader_name}.instance_name"),
                dp_config.get(f"{loader_name}.repo_name"),
                dp_config.get(f"{loader_name}.deployment_id"),
                self.hmd_region,
                loader_config[loader_name],
            )
            for loader_name in loader_config
            if loader_name != service_loader
        ]
        return [local_client] + service_clients

    def _make_client(
        self, instance_name, repo_name, deployment_id, hmd_region, language_packs
    ):
        def get_schema_base(package_names: List[str]) -> List[str]:
            schema_bases = []
            for package_name in package_names:
                package_name = package_name.replace("-", "_")
                module = import_module(f"{package_name}.{package_name}_client")
                get_schema_root_method = getattr(module, "get_client_schema_root")
                schema_bases.append(get_schema_root_method())
            return schema_bases

        return RestClient(
            base_url=self._generate_url(instance_name, deployment_id, hmd_region),
            loader=DefaultLoader(get_schema_base(language_packs)),
            api_key=self._get_api_key(
                instance_name, repo_name, deployment_id, hmd_region
            ),
            auth_token=self._get_auth_token(),
        )

    def _generate_url(self, instance_name, deployment_id, hmd_region):
        if self.environment == "local":
            return f"http://hmd_proxy/{instance_name}/"
        return f"https://{instance_name}-{deployment_id}-{hmd_region}.{get_neuronsphere_domain(self.customer_code, self.environment)}"

    def _get_auth_token(self):
        if self.environment == "local":
            return get_auth_token()
        session = get_deployer_target_session(
            self.hmd_region, profile=None, account=self.account_number
        )

        client_secrets = get_secret(
            session, (self.okta_secret_name or "okta-cicd-service"), use_cache=True
        )

        return okta_service_account_token(
            client_secrets["client_id"], client_secrets["client_secret"], session
        )

    def _get_api_key(self, instance_name, repo_name, deployment_id, hmd_region):
        if self.environment == "local":
            return None

        session = get_deployer_target_session(
            hmd_region, profile=None, account=self.account_number
        )

        apigw = session.client("apigateway")
        results = apigw.get_api_keys(
            nameQuery=f"{instance_name}_{repo_name}_{deployment_id}_{self.environment}_{hmd_region}_{self.customer_code}",
            includeValues=True,
        )

        return results["items"][0]["value"] if len(results["items"]) == 1 else None

    def _get_gozer_client(self, instance_name: str) -> BaseClient:
        url = f"https://{instance_name}-{self.deployment_id}-{self.hmd_region}.{self.customer_code}-{self.environment}-neuronsphere.io"

        return RestClient(url, None, auth_token=self._get_auth_token())

    @keyword
    def clear_service_db(
        self,
        gozer_instance_name: str,
        pre_test_db_clear: Dict[str, List],
        dynamo_tables: List[str] = None,
    ):
        if self.environment == "local":
            # Gozer doesn't run locally so it is the dev's responsibility to clear out dbs
            return
        if dynamo_tables is None:
            dynamo_tables = []
        # clear the databases...
        gozer_client = self._get_gozer_client(gozer_instance_name)
        for neptune_db in pre_test_db_clear.get("neptune_dbs", []):
            gozer_client.invoke_custom_operation(f"clear_db/{neptune_db}", {})
        for rds_service in pre_test_db_clear.get("rds_services", []):
            gozer_client.invoke_custom_operation(f"clear_db/{rds_service}", {})
        for dynamo_table in dynamo_tables:
            gozer_client.invoke_custom_operation(
                f"clear_dynamo_table/{dynamo_table}", {}
            )

    @keyword
    def create_an_entity(self, entity_name, data):
        entity_data = {**data}
        if "_updated" in data:
            entity_data["_updated"] = datetime.fromisoformat(
                data["_updated"].replace("Z", "+00:00")
            )
        if "_created" in data:
            entity_data["_created"] = datetime.fromisoformat(
                data["_created"].replace("Z", "+00:00")
            )
        return self.rs._get_client_for_type(entity_name).loader.get_class(entity_name)(
            **entity_data
        )

    @keyword
    def upsert_an_entity(self, entity: Entity):
        return self.rs._get_client_for_type(entity.get_namespace_name()).upsert_entity(
            entity
        )

    @keyword
    def delete_an_entity(self, entity_name, id_):
        return self.rs._get_client_for_type(entity_name).delete_entity(entity_name, id_)

    @keyword
    def get_an_entity(self, entity_name, id_):
        return self.rs._get_client_for_type(entity_name).get_entity(entity_name, id_)

    @keyword
    def search_an_entity(self, entity_name, filter_={}):
        return self.rs._get_client_for_type(entity_name).search_entity(
            entity_name, filter_
        )

    @keyword
    def get_from_relationships(self, noun: Noun, relationship_type):
        relationships = self.rs._get_client_for_type(
            noun.get_namespace_name()
        ).get_relationships_from(noun, relationship_type)
        items = []
        for rel in relationships:
            client = self.rs._get_client_for_type(
                rel.ref_to_type().get_namespace_name()
            )
            items.append(
                client.get_entity(rel.ref_to_type().get_namespace_name(), rel.ref_to)
            )
        return items

    @keyword
    def get_to_relationships(self, noun, relationship_type):
        relationships = self.rs._get_client_for_type(
            noun.get_namespace_name()
        ).get_relationships_to(noun, relationship_type)

        items = []
        for rel in relationships:
            client = self.rs._get_client_for_type(
                rel.ref_from_type().get_namespace_name()
            )
            items.append(
                client.get_entity(
                    rel.ref_from_type().get_namespace_name(), rel.ref_from
                )
            )
        return items

    @keyword
    def invoke_custom_operation(self, path, data, method="POST"):
        return self.local_client.invoke_custom_operation(path, data, method)

    @keyword
    def upsert_entities(
        self, nouns: List[Noun] = [], relationships: List[Relationship] = []
    ):
        return self.local_client.upsert_entities(
            nouns=nouns, relationships=relationships
        )
