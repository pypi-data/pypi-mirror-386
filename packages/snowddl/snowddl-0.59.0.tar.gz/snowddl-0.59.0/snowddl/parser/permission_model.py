from snowddl.blueprint import (
    ObjectType,
    PermissionModel,
    PermissionModelCreateGrant,
    PermissionModelFutureGrant,
    PermissionModelRuleset,
)
from snowddl.parser.abc_parser import AbstractParser


# fmt: off
permission_model_json_schema = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
            "inherit_from": {
                "type": "string",
            },
            "ruleset": {
                "type": "string",
            },
            "owner_create_grants": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "owner_future_grants": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1
                }
            },
            "write_future_grants": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1
                }
            },
            "read_future_grants": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1
                }
            },
        },
        "additionalProperties": False,
    },
}


class PermissionModelParser(AbstractParser):
    def load_blueprints(self):
        # This is a special parser that does not load any blueprints, but it loads permission models instead
        pass

    def load_permission_models(self):
        self.parse_multi_entity_file("permission_model", permission_model_json_schema, self.process_permission_model)

    def process_permission_model(self, name, params):
        # Possibly inherit model from another model to reduce code repetition
        if params.get("inherit_from"):
            model = self.config.get_permission_model(params.get("inherit_from").upper()).model_copy(deep=True)
        else:
            model = PermissionModel()

        # Ruleset
        if params.get("ruleset"):
            model.ruleset = PermissionModelRuleset[params.get("ruleset").upper()]

        # Owner create grants
        for object_type in params.get("owner_create_grants", []):
            grant = PermissionModelCreateGrant(on=ObjectType[str(object_type).upper()])

            if grant not in model.owner_future_grants:
                model.owner_create_grants.append(grant)

        # Owner future grants
        for object_type, privileges in params.get("owner_future_grants", {}).items():
            for p in privileges:
                grant = PermissionModelFutureGrant(privilege=p.upper(), on=ObjectType[str(object_type).upper()])

                if grant not in model.owner_future_grants:
                    model.owner_future_grants.append(grant)

        # Write future grants
        for object_type, privileges in params.get("write_future_grants", {}).items():
            for p in privileges:
                if p.upper() == "OWNERSHIP":
                    raise ValueError(
                        f"Cannot assign OWNERSHIP future grant to WRITE role while defining permission model [{name}]"
                    )

                grant = PermissionModelFutureGrant(privilege=p.upper(), on=ObjectType[str(object_type).upper()])

                if grant not in model.write_future_grants:
                    model.write_future_grants.append(grant)

        # Read future grants
        for object_type, privileges in params.get("read_future_grants", {}).items():
            for p in privileges:
                if p.upper() == "OWNERSHIP":
                    raise ValueError(
                        f"Cannot assign OWNERSHIP future grant to READ role while defining permission model [{name}]"
                    )

                grant = PermissionModelFutureGrant(privilege=p.upper(), on=ObjectType[str(object_type).upper()])

                if grant not in model.read_future_grants:
                    model.read_future_grants.append(grant)

        self.config.add_permission_model(name.upper(), model)
