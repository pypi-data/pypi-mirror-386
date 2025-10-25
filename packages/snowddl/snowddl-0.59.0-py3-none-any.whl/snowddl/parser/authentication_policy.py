from snowddl.blueprint import AuthenticationPolicyBlueprint, SchemaObjectIdent
from snowddl.parser.abc_parser import AbstractParser, ParsedFile


# fmt: off
authentication_policy_json_schema = {
    "type": "object",
    "properties": {
        "authentication_methods": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "mfa_authentication_methods": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "mfa_enrollment": {
            "type": "string"
        },
        "mfa_policy": {
            "type": "object",
            "additionalProperties": {
                "type": ["array", "boolean", "number", "string"]
            }
        },
        "client_types": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "security_integrations": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1
        },
        "pat_policy": {
            "type": "object",
            "additionalProperties": {
                "type": ["array", "boolean", "number", "string"]
            }
        },
        "workload_identity_policy": {
            "type": "object",
            "additionalProperties": {
                "type": ["array", "boolean", "number", "string"]
            }
        },
        "comment": {
            "type": "string"
        }
    },
    "additionalProperties": False,
}
# fmt: on


class AuthenticationPolicyParser(AbstractParser):
    def load_blueprints(self):
        self.parse_schema_object_files(
            "authentication_policy", authentication_policy_json_schema, self.process_authentication_policy
        )

    def process_authentication_policy(self, f: ParsedFile):
        bp = AuthenticationPolicyBlueprint(
            full_name=SchemaObjectIdent(self.env_prefix, f.database, f.schema, f.name),
            authentication_methods=self.normalise_params_list(f.params.get("authentication_methods")),
            mfa_authentication_methods=self.normalise_params_list(f.params.get("mfa_authentication_methods")),
            mfa_enrollment=f.params.get("mfa_enrollment").upper(),
            mfa_policy=self.normalise_params_dict(f.params.get("mfa_policy")),
            client_types=self.normalise_params_list(f.params.get("client_types")),
            security_integrations=self.normalise_params_list(f.params.get("security_integrations")),
            pat_policy=self.normalise_params_dict(f.params.get("pat_policy")),
            workload_identity_policy=self.normalise_params_dict(f.params.get("workload_identity_policy")),
            comment=f.params.get("comment"),
        )

        self.config.add_blueprint(bp)
