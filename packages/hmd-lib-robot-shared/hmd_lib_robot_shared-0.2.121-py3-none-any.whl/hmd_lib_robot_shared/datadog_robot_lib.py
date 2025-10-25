import os
import time
from robot.api.deco import keyword, library
from robot.api.logger import console

from datadog_api_client.v1 import ApiClient, ApiException, Configuration
from datadog_api_client.v1.api import events_api, metrics_api
from pprint import pprint

from hmd_cli_tools.hmd_cli_tools import (
    get_secret,
    get_session,
    get_cloud_region,
    get_account_session,
    get_datadog_api_url,
)


@library
class DatadogLib:
    def __init__(
        self,
        instance_name,
        repo_name,
        deployment_id,
        environment,
        hmd_region,
        customer_code,
        account_number=None,
    ):
        self.instance_name = instance_name
        self.repo_name = repo_name
        self.deployment_id = deployment_id
        self.environment = environment
        self.hmd_region = hmd_region
        self.customer_code = customer_code
        self.account_number = account_number

        self.datadog_tags = f"env:{self.environment}_{self.hmd_region}_{self.customer_code},service:{self.instance_name}_{self.repo_name}"

        self.session = get_session(aws_region=get_cloud_region(self.hmd_region))
        if self.account_number:
            self.session = get_account_session(
                self.session,
                self.account_number,
                "hmd.neuronsphere.deploy",
                get_cloud_region(self.hmd_region),
            )

        self.configuration = Configuration()
        self.configuration.api_key["apiKeyAuth"] = self._get_datadog_key("api")
        self.configuration.api_key["appKeyAuth"] = self._get_datadog_key("app")
        self.configuration.host = get_datadog_api_url(hmd_region, True)

    def _get_datadog_key(self, key_type):
        os_var_name = f"dd_{key_type}_key".upper()
        secret_name = f"datadog-{key_type}-key"

        return os.environ.get(os_var_name) or get_secret(self.session, secret_name)

    @keyword
    def get_datadog_events(self, start):
        with ApiClient(self.configuration) as api_client:
            api_instance = events_api.EventsApi(api_client)
            try:
                api_response = api_instance.list_events(
                    start=int(start),
                    end=int(time.time()),
                    tags=self.datadog_tags,
                    sources="my_apps",
                )
                pprint(api_response)
                return api_response.get("events", [])
            except ApiException as e:
                print("Exception when calling EventsApi->list_events: %s\n" % e)
                return []

    @keyword
    def get_datadog_metrics(self):
        with ApiClient(self.configuration) as api_client:
            api_instance = metrics_api.MetricsApi(api_client)
            try:
                api_response = api_instance.list_active_metrics(
                    0, tag_filter=self.datadog_tags
                )
                pprint(api_response)
                return api_response.get("metrics", [])
            except ApiException as e:
                print(
                    "Exception when calling MetricsApi->list_active_metrics: %s\n" % e
                )
                return []
