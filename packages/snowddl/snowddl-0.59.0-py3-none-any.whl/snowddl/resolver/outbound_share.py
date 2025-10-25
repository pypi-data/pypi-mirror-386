from json import loads as json_loads
from typing import List

from snowddl.blueprint import AccountIdent, OutboundShareBlueprint, Grant, GrantPattern, build_grant_name_ident
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType


class OutboundShareResolver(AbstractResolver):
    skip_on_empty_blueprints = True

    def get_object_type(self) -> ObjectType:
        return ObjectType.SHARE

    def get_existing_objects(self):
        existing_objects = {}

        cur = self.engine.execute_meta("SHOW SHARES")

        for r in cur:
            if r["kind"] != "OUTBOUND":
                continue

            if r["owner"] != self.engine.context.current_role:
                continue

            # Remove organization and account prefix, shares are referred in SQL by name only
            full_name = r["name"].split(".")[-1]

            existing_objects[full_name] = {
                "share": full_name,
                "database": r["database_name"],
                "accounts": r["to"].split(",") if r["to"] else [],
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(OutboundShareBlueprint)

    def create_object(self, bp: OutboundShareBlueprint):
        query = self.engine.query_builder()

        query.append(
            "CREATE SHARE {full_name:i}",
            {
                "full_name": bp.full_name,
            },
        )

        if bp.comment:
            query.append_nl(
                "COMMENT = {comment}",
                {
                    "comment": bp.comment,
                },
            )

        self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_outbound_share)

        for bp_grant in self.expand_grant_patterns_to_grants(bp.grant_patterns):
            self.create_grant(bp.full_name, bp_grant)

        self.compare_accounts(bp)

        return ResolveResult.CREATE

    def compare_object(self, bp: OutboundShareBlueprint, row: dict):
        result = ResolveResult.NOCHANGE

        bp_grants = self.expand_grant_patterns_to_grants(bp.grant_patterns)
        existing_grants = self.get_existing_share_grants(bp.full_name)

        for bp_grant in bp_grants:
            if bp_grant not in existing_grants:
                self.create_grant(bp.full_name, bp_grant)
                result = ResolveResult.GRANT

        for ex_grant in existing_grants:
            if not any(grant_pattern.is_matching_grant(ex_grant) for grant_pattern in bp.grant_patterns):
                self.drop_grant(bp.full_name, ex_grant)
                result = ResolveResult.GRANT

        if self.compare_accounts(bp, check_existing=True):
            result = ResolveResult.ALTER

        if bp.comment != row["comment"]:
            self.engine.execute_safe_ddl(
                "ALTER SHARE {full_name:i} SET COMMENT = {comment}",
                {
                    "full_name": bp.full_name,
                    "comment": bp.comment,
                },
                condition=self.engine.settings.execute_outbound_share,
            )

            result = ResolveResult.ALTER

        return result

    def drop_object(self, row: dict):
        self.engine.execute_unsafe_ddl(
            "DROP SHARE {share_name:i}",
            {
                "share_name": row["share"],
            },
            condition=self.engine.settings.execute_outbound_share,
        )

        return ResolveResult.DROP

    def compare_accounts(self, bp: OutboundShareBlueprint, check_existing=False):
        existing_accounts = []
        accounts_to_add = []
        accounts_to_remove = []

        if check_existing:
            cur = self.engine.execute_meta(
                "SELECT SYSTEM$LIST_OUTBOUND_SHARES_DETAILS({share_name}) AS details",
                {
                    "share_name": bp.full_name,
                },
            )

            row = cur.fetchone()

            if row:
                for r in json_loads(row["DETAILS"]):
                    if "TARGETED WITHIN ORGANIZATION" in r["account_name"]:
                        continue

                    existing_accounts.append(AccountIdent(*r["account_name"].split(".", 2)))

        for account in bp.accounts:
            if account not in existing_accounts:
                accounts_to_add.append(account)

        for account in existing_accounts:
            if account not in bp.accounts:
                accounts_to_remove.append(account)

        if accounts_to_add:
            query = self.engine.query_builder()

            query.append(
                "ALTER SHARE {full_name:i} ADD ACCOUNTS = {accounts:i}",
                {
                    "full_name": bp.full_name,
                    "accounts": accounts_to_add,
                },
            )

            if bp.share_restrictions is not None:
                query.append_nl("SHARE_RESTRICTIONS = {share_restrictions:b}", {"share_restrictions": bp.share_restrictions})

            self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_outbound_share)

        if accounts_to_remove:
            query = self.engine.query_builder()

            query.append(
                "ALTER SHARE {full_name:i} REMOVE ACCOUNTS = {accounts:i}",
                {
                    "full_name": bp.full_name,
                    "accounts": accounts_to_remove,
                },
            )

            self.engine.execute_unsafe_ddl(query, condition=self.engine.settings.execute_outbound_share)

        return len(accounts_to_add) > 0 or len(accounts_to_remove) > 0

    def create_grant(self, share_name, grant: Grant):
        if grant.privilege == "USAGE" and grant.on == ObjectType.DATABASE_ROLE:
            self.engine.execute_unsafe_ddl(
                "GRANT {on:r} {name:i} TO SHARE {share_name:i}",
                {
                    "on": grant.on.singular_for_grant,
                    "name": grant.name,
                    "share_name": share_name,
                },
                condition=self.engine.settings.execute_outbound_share,
            )
        else:
            self.engine.execute_unsafe_ddl(
                "GRANT {privilege:r} ON {on:r} {name:i} TO SHARE {share_name:i}",
                {
                    "privilege": grant.privilege,
                    "on": grant.on.singular,
                    "name": grant.name,
                    "share_name": share_name,
                },
                condition=self.engine.settings.execute_outbound_share,
            )

    def drop_grant(self, share_name, grant: Grant):
        if grant.privilege == "USAGE" and grant.on == ObjectType.DATABASE_ROLE:
            self.engine.execute_unsafe_ddl(
                "REVOKE {on:r} {name:i} FROM SHARE {share_name:i}",
                {
                    "privilege": grant.privilege,
                    "on": grant.on.singular,
                    "name": grant.name,
                    "share_name": share_name,
                },
                condition=self.engine.settings.execute_outbound_share,
            )
        else:
            self.engine.execute_unsafe_ddl(
                "REVOKE {privilege:r} ON {on:r} {name:i} FROM SHARE {share_name:i}",
                {
                    "privilege": grant.privilege,
                    "on": grant.on.singular,
                    "name": grant.name,
                    "share_name": share_name,
                },
                condition=self.engine.settings.execute_outbound_share,
            )

    def get_existing_share_grants(self, share_name):
        grants = []

        cur = self.engine.execute_meta(
            "SHOW GRANTS TO SHARE {share_name:i}",
            {
                "share_name": share_name,
            },
        )

        for r in cur:
            grants.append(
                Grant(
                    privilege=r["privilege"],
                    on=ObjectType[r["granted_on"]],
                    name=build_grant_name_ident(self.config.env_prefix, r["name"], ObjectType[r["granted_on"]]),
                )
            )

        return grants

    def expand_grant_patterns_to_grants(self, grant_patterns: List[GrantPattern]):
        grants = []

        for grant_pattern in grant_patterns:
            blueprints = self.config.get_blueprints_by_type_and_pattern(grant_pattern.on.blueprint_cls, grant_pattern.pattern)

            for obj_bp in blueprints.values():
                grants.append(
                    Grant(
                        privilege=grant_pattern.privilege,
                        on=grant_pattern.on,
                        name=obj_bp.full_name,
                    ),
                )

        return grants
