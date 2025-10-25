from pathlib import Path
from re import compile, DOTALL

from snowddl.blueprint import ObjectType
from snowddl.converter.abc_converter import ConvertResult
from snowddl.converter.abc_schema_object_converter import AbstractSchemaObjectConverter
from snowddl.converter._yaml import YamlLiteralStr, YamlIncludeStr
from snowddl.parser.view import view_json_schema


view_text_re = compile(r"^.*?\sas(\n|\s)+(.*)$", DOTALL)


class ViewConverter(AbstractSchemaObjectConverter):
    def get_object_type(self) -> ObjectType:
        return ObjectType.VIEW

    def get_existing_objects_in_schema(self, schema: dict):
        existing_objects = {}

        cur = self.engine.execute_meta(
            "SHOW VIEWS IN SCHEMA {database:i}.{schema:i}",
            {
                "database": schema["database"],
                "schema": schema["schema"],
            },
        )

        for r in cur:
            if r["is_materialized"] == "true":
                continue

            existing_objects[f"{r['database_name']}.{r['schema_name']}.{r['name']}"] = {
                "database": r["database_name"],
                "schema": r["schema_name"],
                "name": r["name"],
                "owner": r["owner"],
                "text": r["text"],
                "is_secure": r["is_secure"] == "true",
                "comment": r["comment"] if r["comment"] else None,
            }

        return existing_objects

    def dump_object(self, row):
        object_path = (
            self.base_path / self._normalise_name_with_prefix(row["database"]) / self._normalise_name(row["schema"]) / "view"
        )

        data = {
            "columns": self._get_columns(row),
            "text": self._get_text_or_include(object_path, row),
            "comment": row["comment"],
        }

        if data:
            self._dump_file(object_path / f"{self._normalise_name(row['name'])}.yaml", data, view_json_schema)
            return ConvertResult.DUMP

        return ConvertResult.EMPTY

    def _get_columns(self, row):
        cols = {}

        cur = self.engine.execute_meta(
            "DESC VIEW {database:i}.{schema:i}.{name:i}",
            {
                "database": row["database"],
                "schema": row["schema"],
                "name": row["name"],
            },
        )

        for c in cur:
            cols[self._normalise_name(c["name"])] = c["comment"] if c["comment"] else None

        return cols

    def _get_text_or_include(self, object_path: Path, row: dict):
        # TODO: replace with better implementation when available
        cur = self.engine.execute_meta(
            "SELECT GET_DDL('VIEW', {ident}) AS view_ddl", {"ident": f"{row['database']}.{row['schema']}.{row['name']}"}
        )

        view_ddl = cur.fetchone()["VIEW_DDL"]
        view_text = view_text_re.sub(r"\2", view_ddl).rstrip(";").strip(" \n\r\t")

        # Remove trailing spaces from each line to prevent output formatting issues
        # https://github.com/yaml/pyyaml/issues/411
        view_text = "\n".join(line.rstrip(" ") for line in view_text.split("\n"))

        if self.engine.settings.convert_view_text_to_file:
            file_name = f"{self._normalise_name(row['name'])}.sql"
            self._dump_code(object_path / "sql" / file_name, view_text)

            return YamlIncludeStr(f"sql/{file_name}")

        return YamlLiteralStr(view_text)
