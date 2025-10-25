from importlib import import_module
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
from hmd_entity_storage.engines.postgres_engine import PostgresEngine
from hmd_meta_types import Entity, Noun
from hmd_schema_loader import DefaultLoader


def get_db_info(
    session,
    config: Dict,
    dp_config: DeploymentConfig,
    environment: str,
    hmd_region: str,
    customer_code: str,
):
    db_info = {
        "host": config.get("host", "db"),
        "user": config.get("user", "hmdroot"),
        "password": config.get("password", ""),
        "db_name": config.get("db_name", "hmd_entities"),
    }

    if session is None:
        return db_info

    if "db_secret_name" in config["engine_config"]:
        if config["engine_config"]["db_secret_name"].startswith("dependency:"):
            dependency_name = config["engine_config"]["db_secret_name"].split(
                ":", maxsplit=1
            )[1]
            config["engine_config"][
                "db_secret_name"
            ] = db_secret_name_from_dependencies(
                dp_config[dependency_name],
                environment,
                hmd_region,
                customer_code,
            )
            config["engine_config"]["db_name"] = dp_config[f"{dependency_name}.db_name"]

    db_secret_name = config.get("engine_config", {}).get("db_secret_name")
    if db_secret_name:
        sm_client = session.client("secretsmanager")
        try:
            secret = sm_client.get_secret_value(SecretId=db_secret_name)["SecretString"]
        except sm_client.exceptions.ResourceNotFoundException as ex:
            raise Exception(f"Unable to read secret name: {db_secret_name}") from ex
        secret = loads(secret)
        db_info["host"] = secret["host"]
        db_info["user"] = secret["username"]
        db_info["password"] = secret["password"]
    return db_info


@library
class PostgresClientLib:
    def __init__(
        self, db_name, environment, hmd_region, customer_code, account_number
    ) -> None:
        self.environment = environment
        self.hmd_region = hmd_region
        self.account_number = account_number
        # Bender writes the instance configuration out here...
        with open("instance_configuration.yaml", "r") as fl:
            instance_config = yaml.safe_load(fl)

        dp_config = DeploymentConfig(instance_config)

        self.dp_config = dp_config

        postgres_config = (
            dp_config.get("service_config", {})
            .get("hmd_db_engines", {})
            .get(db_name, {})
        )

        session = None

        if self.environment != "local":
            session = get_deployer_target_session(
                self.hmd_region, profile=None, account=self.account_number
            )

        dbinfo = get_db_info(
            session,
            postgres_config,
            dp_config,
            environment,
            hmd_region,
            customer_code,
        )
        engine = PostgresEngine(
            dbinfo["host"], dbinfo["user"], dbinfo["password"], dbinfo["db_name"]
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
