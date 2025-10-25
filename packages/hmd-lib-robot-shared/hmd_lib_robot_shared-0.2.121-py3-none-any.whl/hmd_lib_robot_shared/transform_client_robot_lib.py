from time import sleep
from robot.api.deco import keyword, library
from robot.api import Failure
from hmd_lib_transform.hmd_lib_transform import HmdLibTransform
from hmd_lib_naming.hmd_lib_naming import HmdNamingClient
from hmd_cli_tools.hmd_cli_tools import (
    make_standard_name,
    get_session,
    get_cloud_region,
    get_account_session,
    get_deployer_target_session,
    get_secret,
)
from hmd_cli_tools.okta_tools import get_auth_token
from hmd_lib_auth.hmd_lib_auth import okta_service_account_token


@library
class TransformLib:
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

        base_url = "http://hmd_proxy/hmd_ms_transform/"
        auth_token = self._get_auth_token()

        if environment != "local":
            naming_client = HmdNamingClient(
                base_url=f"https://ms-naming-aaa-reg1.{customer_code}-admin-neuronsphere.io",
                auth_token=auth_token,
            )

            transform_service = naming_client.resolve_service(
                instance_name, environment
            )

            base_url = transform_service.httpEndpoint

        self.client = HmdLibTransform(base_url=base_url, auth_token=auth_token)

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

    @keyword
    def run_transform(self, transform_name: str, run_params: dict = None):
        result = self.client.run_provider_transform(transform_name, run_params)
        if result["status"] == "scheduling_failed":
            raise Failure(f"Failed scheduling: {transform_name}")

        status = "running"
        count = 0

        while status == "running" or count >= 300:
            sleep(10)
            count += 10
            attr = self.client.search_transform_instances(name=result["instance_name"])

            if len(attr) > 0:
                status = attr[0]["status"]

        if status != "complete_successful":
            raise Failure(f"Failed running transform: {transform_name}")
