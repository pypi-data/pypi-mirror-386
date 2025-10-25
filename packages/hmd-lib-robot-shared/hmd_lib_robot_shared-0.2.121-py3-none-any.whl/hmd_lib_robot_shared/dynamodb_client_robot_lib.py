from importlib import import_module
import logging
import os
from typing import Dict, List
from robot.api.deco import keyword, library
import yaml
from json import loads

from hmd_cli_tools.cdktf_tools import DeploymentConfig, db_secret_name_from_dependencies
from hmd_cli_tools.hmd_cli_tools import (
    make_standard_name,
    get_deployer_target_session,
    get_session,
    get_cloud_region,
    get_account_session,
    get_neuronsphere_domain,
    get_secret,
)
from hmd_graphql_client import BaseClient
from hmd_graphql_client.hmd_db_engine_client import DbEngineClient
from hmd_graphql_client.relationship_support import RelationshipSupport
from hmd_entity_storage.engines.dynamodb_engine import DynamoDbEngine
from hmd_meta_types import Entity, Noun
from hmd_schema_loader import DefaultLoader

logger = logging.getLogger()


@library
class DynamoDbClientLib:
    """Creates standard client for interacting with NeuronSphere deployed DynamoDB"""

    def __init__(
        self,
        db_name,
        instance_name,
        repo_name,
        deployment_id,
        environment,
        hmd_region,
        customer_code,
        account_number,
    ) -> None:
        self.environment = environment
        self.hmd_region = hmd_region
        self.account_number = account_number
        # Bender writes the instance configuration out here...
        with open("instance_configuration.yaml", "r") as fl:
            instance_config = yaml.safe_load(fl)

        dp_config = DeploymentConfig(instance_config)

        self.dp_config = dp_config

        config = (
            self.dp_config.get("service_config", {})
            .get("hmd_db_engines", {})
            .get(db_name, {})
            .get("engine_config", {})
        )
        default_name = None

        if "dynamo_table" not in config:
            audit_svc = self.dp_config.get("internal-audit-svc", {})
            default_name = make_standard_name(
                instance_name=audit_svc.get("instance_name"),
                repo_name=audit_svc.get("repo_name"),
                deployment_id=audit_svc.get("deployment_id"),
                environment=environment,
                hmd_region=hmd_region,
                customer_code=customer_code,
            )

        table_name = config.get("dynamo_table", default_name)

        logger.info(f"Dynamo table {table_name}")

        dynamo_url = config.get("dynamo_url")
        pitr = config.get("point_in_time_recovery")

        session = None
        if environment != "local":
            session = get_deployer_target_session(
                self.hmd_region, profile=None, account=account_number
            )

        engine = DynamoDbEngine(
            table_name=table_name, dynamo_url=dynamo_url, pitr=pitr, session=session
        )

        service_loader = dp_config["service_config"]["service_loader"]
        loader_config = dp_config["service_config"]["loader_config"]
        language_packs = loader_config[service_loader]

        self.client = self._make_client(engine, language_packs)
        self.rs = RelationshipSupport(clients=[self.client])

    def _make_client(
        self,
        engine,
        language_packs,
    ):
        def get_schema_base(package_names: List[str]) -> List[str]:
            schema_bases = []
            for package_name in package_names:
                package_name = package_name.replace("-", "_")
                module = import_module(f"{package_name}.{package_name}_client")
                get_schema_root_method = getattr(module, "get_client_schema_root")
                schema_bases.append(get_schema_root_method())
            return schema_bases

        return DbEngineClient(
            db_engine=engine, loader=DefaultLoader(get_schema_base(language_packs))
        )

    @keyword
    def search_an_entity(self, entity_name, filter_):
        """Search for specific entity

        Args:
            entity_name (str): class name of entity
            filter_ (dict): filter dictionary

        Returns:
            [Entity]: list of entity_name instances
        """
        return self.rs._get_client_for_type(entity_name).search_entity(
            entity_name, filter_
        )

    @keyword
    def get_from_relationships(self, noun: Noun, relationship_type: str):
        """Gets relationships where noun is the ref_from object

        Args:
            noun (Noun): Noun in the ref_from property on the Relationship
            relationship_type (str): class name of Relationship to search

        Returns:
            List[Relationship]: list of Relationships
        """
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
        """Gets relationships where noun is the ref_to object

        Args:
            noun (Noun): Noun in the ref_to property on the Relationship
            relationship_type (str): class name of Relationship to search

        Returns:
            List[Relationship]: list of Relationships
        """
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
