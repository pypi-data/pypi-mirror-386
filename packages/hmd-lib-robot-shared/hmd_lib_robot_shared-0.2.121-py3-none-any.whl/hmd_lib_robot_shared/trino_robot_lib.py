import os

from robot.api.deco import library, keyword
import trino
import yaml
from hmd_cli_tools.cdktf_tools import DeploymentConfig, make_standard_name
from hmd_cli_tools.hmd_cli_tools import (
    get_secret,
    get_deployer_target_session,
)


@library
class TrinoRobotLib:
    def __init__(self, instance_name: str):
        if os.environ["HMD_ENVIRONMENT"] == "local":
            conn = trino.dbapi.connect(
                host="trino", port=8081, user="user", catalog="hive"
            )

            self.cur = conn.cursor()
        else:
            with open("instance_configuration.yaml", "r") as ic:
                dp_config = DeploymentConfig(yaml.safe_load(ic))

            users = dp_config.get("users")
            if not isinstance(users, list):
                users = [users]

            secret_name = make_standard_name(
                users[0]["instance_name"],
                users[0]["repo_name"],
                users[0]["deployment_id"],
                os.environ["HMD_ENVIRONMENT"],
                os.environ["HMD_REGION"],
                os.environ["HMD_CUSTOMER_CODE"],
            )

            session = get_deployer_target_session(
                os.environ["HMD_REGION"],
                profile=None,
                account=os.environ["HMD_ACCOUNT"],
            )
            creds_secret = get_secret(session, secret_name=secret_name)
            auth = trino.auth.BasicAuthentication(
                creds_secret["username"], creds_secret["password"]
            )
            conn = trino.dbapi.connect(
                host=f"{instance_name}.{os.environ['HMD_CUSTOMER_CODE']}-{os.environ['HMD_ENVIRONMENT']}-neuronsphere.io",
                port=443,
                user=creds_secret["username"],
                catalog="hive",
                auth=auth,
                http_scheme=trino.constants.HTTPS,
            )

            self.cur = conn.cursor()

    @keyword
    def execute_query(self, query_str: str):
        results = self.cur.execute(query_str).fetchall()

        return results
