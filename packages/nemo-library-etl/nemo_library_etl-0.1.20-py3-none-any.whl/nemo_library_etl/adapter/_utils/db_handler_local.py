# All comments and code identifiers in English (as per your preference)
import os
import re
import tempfile
import duckdb
from duckdb import DuckDBPyConnection
from pathlib import Path
from typing import Optional, Iterable, Any, Tuple, Union
import logging

from nemo_library import NemoLibrary
from enum import Enum


from nemo_library_etl.adapter._utils.config import ConfigBase
from nemo_library_etl.adapter._utils.dbandfileutils import (
    _output_path,
)
from nemo_library.features.import_configuration import ImportConfigurations
import sqlglot


def _safe_table_name(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        s = "table"
    if s[0].isdigit():
        s = "_" + s
    return s


def _quote_ident(name: str) -> str:
    """Safely quote a SQL identifier for DuckDB (double-quote escaping)."""
    return '"' + name.replace('"', '""') + '"'


class ETLDuckDBHandler:
    """
    DuckDB helper for ingesting ETL JSONL/JSONL.GZ outputs efficiently.
    """

    def __init__(
        self,
        nl: NemoLibrary,
        cfg: ConfigBase,
        logger: Union[logging.Logger, object],
        database: Optional[str | Path] = None,
        read_only: bool = False,
        threads: Optional[int] = None,
        memory_limit: Optional[str] = None,
    ):
        """
        Args:
            database: DuckDB file path. If None, use in-memory (':memory:').
            read_only: Open the DuckDB database in read-only mode.
            threads: Optional PRAGMA threads=N.
            memory_limit: Optional PRAGMA memory_limit='XGB' (e.g., '4GB').
        """
        self.nl = nl
        self.cfg = cfg
        self.logger = logger
        db = ":memory:" if database is None else str(database)
        if db != ":memory:":
            db = Path(db)
            db.parent.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Opening DuckDB database at: {db} (read_only={read_only})")
        self.con: DuckDBPyConnection = duckdb.connect(database=db, read_only=read_only)
        # Optional performance pragmas
        if not threads:
            threads = os.cpu_count()
        if threads:
            self.con.execute(f"PRAGMA threads={int(threads)};")
        if memory_limit:
            self.con.execute(f"PRAGMA memory_limit='{memory_limit}';")

    def close(self) -> None:
        try:
            self.con.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    # --------------------------- path resolution ---------------------------

    def _resolve_jsonl_path(
        self,
        step: str | Enum,
        entity: str | Enum | None,
        filename: str | None,
        substep: Optional[str | Enum],
    ) -> Optional[Path]:
        """
        Resolve the output file path for the given ETL object.
        Tries <stem>.jsonl then <stem>.jsonl.gz and returns the first that exists.
        """
        base = _output_path(self.cfg.etl_directory, step, substep, entity, filename, "")
        candidates = [base.with_suffix(".jsonl"), base.with_suffix(".jsonl.gz")]
        for c in candidates:
            if c.exists():
                return c
        return None

    # --------------------------- public API --------------------------------

    def export_table(
        self,
        table_name: str,
        fh,  # ETLFileHandler instance
        step: str | Enum,
        entity: str | Enum | None,
        filename: str | None = None,
        substep: Optional[str | Enum] = None,
        gzip_enabled: bool = False,
        order_by: Optional[str] = None,
        chunk_rows: int = 50_000,
        newline: str = "\n",
    ) -> Tuple[Path, int]:
        """
        Export a DuckDB table to JSONL (optionally .gz) using ETLFileHandler in streaming mode.

        Args:
            table_name: Source DuckDB table to export.
            fh: ETLFileHandler instance to manage JSONL streaming and path resolution.
            adapter, step, entity, filename, substep: Passed through to ETLFileHandler to build the output path.
            gzip_enabled: If True, write .jsonl.gz, otherwise .jsonl.
            order_by: Optional ORDER BY clause (e.g. "id" or "id, created_at DESC") for deterministic output.
            chunk_rows: Number of rows to fetch per batch from DuckDB.
            newline: Newline separator (defaults to '\n').

        Returns:
            (output_path, total_rows)
        """
        if not self.table_exists(
            _safe_table_name(table_name)
        ) and not self.table_exists(table_name):
            raise ValueError(f'DuckDB table does not exist: "{table_name}"')

        # Build SELECT
        ident = (
            table_name
            if self.table_exists(table_name)
            else _safe_table_name(table_name)
        )
        sql = f"SELECT * FROM {_quote_ident(ident)}"
        if order_by:
            sql += f" ORDER BY {order_by}"

        # Prepare execution and column mapping
        res = self.con.execute(sql)
        # DuckDB exposes column names via description
        if not hasattr(res, "description") or res.description is None:
            # Force a zero-row fetch to populate description if needed
            res = self.con.execute(sql + " LIMIT 0")
        res = self.con.execute(sql)
        col_names = [
            d[0] for d in res.description
        ]  # tuples like (name, type_code, ...)

        total = 0
        # Stream writer from your ETLFileHandler determines the final path and handles gzip
        with fh.streamJSONL(
            step=step,
            entity=entity,
            filename=filename,
            gzip_enabled=gzip_enabled,
            substep=substep,
            newline=newline,
        ) as writer:
            # Fetch and write in chunks
            while True:
                rows = res.fetchmany(chunk_rows)
                if not rows:
                    break
                for row in rows:
                    # Map row tuple -> dict with column names
                    rec = {col_names[i]: row[i] for i in range(len(col_names))}
                    writer.write_one(rec, chunk_size=chunk_rows)
                    total += 1
            out_path = writer.path

        self.logger.info(
            f'Exported table "{table_name}" to JSONL at {out_path} with {total:,} records.'
        )

        # If you want the exact total without recounting during the loop (for speed),
        # you can compute it via DuckDB afterwards:
        try:
            total = int(
                self.con.execute(
                    f"SELECT COUNT(*) FROM {_quote_ident(ident)};"
                ).fetchone()[0]
            )
        except Exception:
            # Fallback: total remains as counted (0 if loop avoided counting)
            pass

        return out_path, total

    # --------------------------- helpers -----------------------------------

    def table_exists(self, name: str) -> bool:
        q = self.con.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?;",
            [name],
        ).fetchone()[0]
        return q > 0

    def count_rows(self, name: str) -> int:
        return int(self.con.execute(f'SELECT COUNT(*) FROM "{name}";').fetchone()[0])

    # Optional convenience wrappers
    def query(self, sql: str, params: Optional[Iterable[Any]] = None):
        return self.con.execute(sql, params or [])

    def latest_table_name(
        self, steps: type[Enum], maxstep: Enum | None, entity: str
    ) -> str | None:

        step_list = list(steps)
        max_index = (step_list.index(maxstep) if maxstep else len(step_list)) - 1

        # iterate backwards up to that index (inclusive)
        for step in reversed(step_list[: max_index + 1]):
            table_name = f"{step.value}_{entity}"
            if self.table_exists(table_name):
                return table_name
        return None

    def upload_table_to_nemo(
        self, table_name: str, project_name: str, delete_temp_files: bool
    ) -> None:
        with tempfile.TemporaryDirectory(delete=delete_temp_files) as tmpdir:
            csv_path = Path(tmpdir) / f"{_safe_table_name(table_name)}.csv"

            text_cols = [
                r[0]
                for r in self.con.execute(
                    f"SELECT name FROM pragma_table_info('{table_name}') WHERE type ILIKE '%CHAR%' OR type ILIKE '%TEXT%'"
                ).fetchall()
            ]
            force_quote_cols = ", ".join([f'"{col}"' for col in text_cols])

            query = f"""
                COPY "{table_name}" TO '{csv_path.as_posix()}'
                (HEADER, DELIMITER ';', QUOTE '"', ESCAPE '\\', FORCE_QUOTE ({force_quote_cols}));
            """
            self.con.execute(query)
            self.logger.info(
                f"Uploading table {table_name} to Nemo project {project_name} from {csv_path}"
            )
            try:
                self.nl.ReUploadFile(
                    projectname=project_name,
                    filename=csv_path.absolute().as_posix(),
                    update_project_settings=False,
                    format_data=False,
                    import_configuration=ImportConfigurations(
                        field_delimiter=";",
                        escape_character="\\",
                    ),
                )
            except Exception as e:
                self.logger.error(f"Failed to upload table {table_name} to Nemo: {e}")
                raise

    def extract_tables(self, sql: str) -> list[str]:
        """Extract unique table names from SQL using sqlglot."""
        parsed = sqlglot.parse_one(sql)
        tables = {table.name for table in parsed.find_all(sqlglot.expressions.Table)}
        return sorted(tables)

    def extract_fields(self, sql: str) -> dict[str, list[str]]:
        """Extract selected fields per table from an SQL SELECT statement using sqlglot."""
        parsed = sqlglot.parse_one(sql)
        table_fields: dict[str, set[str]] = {}

        # Iterate through all column references in the query
        for column in parsed.find_all(sqlglot.expressions.Column):
            table = column.table or "__unknown__"  # In case of missing table alias
            field = column.name
            table_fields.setdefault(table, set()).add(field)

        # Convert sets to sorted lists
        return {table: sorted(fields) for table, fields in table_fields.items()}

    def extract_fields_by_base_table(self, sql: str) -> dict[str, list[str]]:
        """
        Parse SQL and return {base_table_name: [sorted list of fields]}.
        Table aliases (e.g., RELKOMM_PHONE) are resolved to their base table (e.g., RELKOMM).
        """
        parsed = sqlglot.parse_one(sql)

        # 1) Build alias->base_table map from all table references in FROM/JOIN
        alias_to_base: dict[str, str] = {}
        base_tables: set[str] = set()

        for t in parsed.find_all(sqlglot.expressions.Table):
            base = t.name  # base table name as written in SQL (without alias)
            base_tables.add(base)
            alias_expr = t.args.get("alias")
            if (
                isinstance(alias_expr, sqlglot.expressions.TableAlias)
                and alias_expr.this
            ):
                # alias like: "RELKOMM AS RELKOMM_PHONE"  -> this == Identifier("RELKOMM_PHONE")
                alias = alias_expr.this.name
                alias_to_base[alias] = base

        # 2) Collect columns, resolving through alias_to_base (or leaving as base when unaliased)
        fields_per_base: dict[str, set[str]] = {tbl: set() for tbl in base_tables}

        for col in parsed.find_all(sqlglot.expressions.Column):
            tbl_alias = col.table  # may be alias, real table, or None
            col_name = col.name

            if tbl_alias:
                base = alias_to_base.get(
                    tbl_alias, tbl_alias
                )  # map alias -> base, else assume already base
                fields_per_base.setdefault(base, set()).add(col_name)
            else:
                # Unqualified column: we can't know the table for sure without full lineage analysis.
                # Put it under a special bucket (optional) or skip. Here we keep it, but annotate unknown.
                fields_per_base.setdefault("__unknown__", set()).add(col_name)

        # 3) Return lists sorted for stability
        return {tbl: sorted(cols) for tbl, cols in fields_per_base.items() if cols}

    def ingest_jsonl(
        self,
        step: str | Enum,
        entity: str | Enum | None,
        filename: str | None = None,
        label: str | None = None,
        substep: Optional[str | Enum] = None,
        ignore_nonexistent: bool = False,
        create_mode: str = "replace",  # 'replace' or 'append'
        table_name: Optional[str] = None,
        add_metadata: bool = True,
        cast_map: Optional[dict[str, str]] = None,
    ) -> int:
        """
        Ingest a JSONL/JSONL.GZ file into DuckDB using read_ndjson(), with optional casts and metadata.
        """
        obj_label = (
            (entity.value if isinstance(entity, Enum) else entity)
            or label
            or "<unknown>"
        )
        src = self._resolve_jsonl_path(step, entity, filename, substep)

        if src is None:
            msg = f"No JSONL file found for entity {obj_label} (step={step})."
            if ignore_nonexistent:
                self.logger.warning(msg + " Skipping.")
                return 0
            raise FileNotFoundError(msg)

        tname = _safe_table_name(table_name or str(obj_label))
        self.logger.info(
            f"Ingesting JSONL into DuckDB: entity={obj_label} -> table={tname} (file={src})"
        )

        # --- Build layered SELECT + params in lockstep ---
        # Base select from read_ndjson
        select_sql = "SELECT * FROM read_ndjson(?);"
        params: list[Any] = [str(src)]

        # Optional: apply explicit casts by wrapping base select once
        if cast_map:
            cast_exprs = []
            for col, dtype in cast_map.items():
                safe_col = col.replace('"', '""')
                cast_exprs.append(f'CAST(sub."{safe_col}" AS {dtype}) AS "{safe_col}"')
            # Explicit casts first (override), then original columns
            cast_projection = (
                ", ".join(cast_exprs + ["sub.*"]) if cast_exprs else "sub.*"
            )
            select_sql = f"SELECT {cast_projection} FROM ({select_sql[:-1]}) AS sub;"  # drop trailing ';'

        # Optional: add metadata exactly once
        if add_metadata:
            # add one more placeholder for _source_path
            select_sql = (
                f"SELECT t.*, CAST(? AS VARCHAR) AS _source_path, NOW() AS _ingested_at "
                f"FROM ({select_sql[:-1]}) AS t;"
            )
            params.append(str(src))

        # --- Execute according to create_mode ---
        if create_mode == "replace":
            self.con.execute(f'DROP TABLE IF EXISTS "{tname}";')
            # CTAS from the select
            self.con.execute(f'CREATE TABLE "{tname}" AS {select_sql}', params)
            rowcount = self.count_rows(tname)
        elif create_mode == "append":
            # Create empty table on first run using LIMIT 0
            if not self.table_exists(tname):
                tmp_sql = f"SELECT * FROM ({select_sql[:-1]}) AS s LIMIT 0;"
                self.con.execute(f'CREATE TABLE "{tname}" AS {tmp_sql}', params)
            # Append rows
            self.con.execute(f'INSERT INTO "{tname}" {select_sql}', params)
            rowcount = self.count_rows(tname)
        else:
            raise ValueError("create_mode must be 'replace' or 'append'")

        self.logger.info(f"Ingested into {tname}. Row count: {rowcount:,}")
        return rowcount
