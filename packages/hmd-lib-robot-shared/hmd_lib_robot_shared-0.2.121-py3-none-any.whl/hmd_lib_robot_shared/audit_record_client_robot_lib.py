from hmd_lib_robot_shared.dynamodb_client_robot_lib import DynamoDbClientLib

from robot.api.deco import keyword, library
from robot.api.logger import console


@library
class AuditRecordClientLib(DynamoDbClientLib):
    """Client library for validating AuditRecord are stored in Dynamo properly"""

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
        super().__init__(
            db_name,
            instance_name,
            repo_name,
            deployment_id,
            environment,
            hmd_region,
            customer_code,
            account_number,
        )

        self.excluded_entities = []

        entity_config = self.dp_config.get("hmd_entity_config", {})

        for key, value in entity_config.items():
            if key == "__default__":
                continue

            if not value.get("audit", True):
                self.excluded_entities.append(key)

    def _make_client(
        self,
        engine,
        language_packs,
    ):

        return super()._make_client(engine, ["hmd-lang-audit"] + language_packs)

    @keyword
    def search_audit_records(self, filter_):
        """Search for AuditRecords

        Args:
            filter_ (Dict): filter dictionary

        Returns:
            List[AuditRecord]: list of AuditRecords
        """
        return self.search_an_entity("hmd_lang_audit.audit_record", filter_)

    @keyword
    def get_audit_records_for_entity(self, noun):
        """Get list of AuditRecords for given Entity

        Args:
            noun (Entity): Entity to search against

        Returns:
            List[AuditRecords]: list of AuditRecords
        """
        return self.get_to_relationships(
            noun, "hmd_lang_audit.audit_record_audits_entity"
        )

    @keyword
    def entity_has_audit_record(self, noun, action: str, count: int = 1):
        records = self.get_audit_records_for_entity(noun)

        assert action is not None, "Must provide valid action"

        record = [record for record in records if record.action == action]

        assert len(record) == count, f"Found {len(record)} records expected {count}"

    @keyword
    def get_excluded_entities(self):
        return self.excluded_entities
