from importlib import import_module
from typing import List
from robot.api.deco import library, keyword


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
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
import time


@library
class DeviceProvisioningLib:
    def __init__(
        self,
        ms_device_instance_name,
        environment,
        hmd_region,
        customer_code,
        account_number=None,
        okta_secret_name=None,
    ):
        self.instance_name = ms_device_instance_name
        self.repo_name = "hmd-ms-device"
        self.deployment_id = "aaa"
        self.environment = environment
        self.hmd_region = hmd_region
        self.customer_code = customer_code
        self.account_number = account_number
        self.okta_secret_name = okta_secret_name
        self.standard_name = make_standard_name(
            self.instance_name,
            self.repo_name,
            self.deployment_id,
            environment,
            hmd_region,
            customer_code,
        )

        self.client = self._make_client(
            self.instance_name,
            self.repo_name,
            self.deployment_id,
            self.hmd_region,
            ["hmd-lang-device"],
        )

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
        try:
            session = get_deployer_target_session(
                hmd_region, profile=None, account=self.account_number
            )

            apigw = session.client("apigateway")
            results = apigw.get_api_keys(
                nameQuery=f"{instance_name}_{repo_name}_{deployment_id}_{self.environment}_{hmd_region}_{self.customer_code}",
                includeValues=True,
            )

            return results["items"][0]["value"] if len(results["items"]) == 1 else None
        except Exception as e:
            return None

    @keyword
    def register_device(self, serial_number: str):
        return self.client.invoke_custom_operation(
            "register_device", {"serial_number": serial_number}
        )

    @keyword
    def provision_device_certs(
        self, serial_number: str, cert_key_filename: str, cert_filename: str
    ):
        # Generate private key and CSR
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Write private key to file
        with open(cert_key_filename, "wb") as key_file:
            key_file.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        # Create CSR
        csr = (
            x509.CertificateSigningRequestBuilder()
            .subject_name(
                x509.Name(
                    [
                        x509.NameAttribute(NameOID.COMMON_NAME, serial_number),
                    ]
                )
            )
            .sign(private_key, hashes.SHA256())
        )

        # Write CSR to file
        with open(cert_filename, "wb") as csr_file:
            csr_file.write(csr.public_bytes(serialization.Encoding.PEM))

        with open(cert_filename, "rb") as csr_file:
            csr_pem = csr_file.read().decode("utf-8")
        resp = self.client.invoke_custom_operation(
            "provisioning/csr", {"device_sn": serial_number, "csr_pem": csr_pem}
        )

        max_attempts = 10  # 5 minutes / 30 seconds = 10 attempts
        attempts = 0
        while (
            resp.get("device_certificate", {}).get("status") != "active"
            and attempts < max_attempts
        ):
            time.sleep(30)
            resp = self.client.invoke_custom_operation(
                f"provisioning/certificate_status/{resp.get('device_certificate', {}).get('identifier')}",
                http_method="GET",
            )
            attempts += 1

        if resp.get("device_certificate", {}).get("status") == "active":
            cert_pem = resp.get("certificate_pem")
            if cert_pem:
                with open(cert_filename, "w") as cert_file:
                    cert_file.write(cert_pem)
            else:
                raise RuntimeError("Certificate PEM not found in response.")
        else:
            raise RuntimeError("Device certificate did not become active.")
