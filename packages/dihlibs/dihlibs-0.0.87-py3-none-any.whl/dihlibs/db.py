from sqlalchemy import create_engine, text
from enum import auto, Enum
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import re, os, json
import dihlibs.functions as fn
from pathlib import Path
from importlib import resources
from dihlibs.node import Node
from dihlibs.graph import Graph
from dihlibs.jsonq import JsonQ
from sqlalchemy.dialects import registry
import yaml
import tempfile
from dihlibs.fs_secret import encrypt_secret

pd.options.display.max_columns = None
pd.options.display.max_rows = None



class ResultFormat(Enum):
    LIST = lambda cols, rows: [dict(zip(cols, r)) for r in rows]
    PANDAS = lambda cols, rows: pd.DataFrame(columns=cols, data=rows)
    RAW = lambda cols, rows: {"columns": list(cols), "data": rows}

    def __init__(self, formatter):
        self._formatter = formatter

    def format(self, cols, rows):
        return self._formatter(cols, rows)

class DB:
    def __init__(
        self,
        connection_url="",
        ssh_command: str = None,
        conf: dict = None,
        connection_file: str = None,
        rc: str = "",
    ):
        self.connection_string = connection_url
        self.ssh_command = ssh_command
        self._set_connection_parameters(conf, connection_file, rc)
        self.engine = create_engine(self.connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self._ssh_connection = None
        self._conn = None

    def connect(
        self,
        key_file=f"{Path.home()}/.ssh",
        with_ssh=True,
    ):
        if (
            with_ssh
            and not self._ssh_connection
            and self.ssh_command 
        ):
            self._ssh_connection = self.open_ssh(key_file)
            self._ssh_connection.wait(25)

        self._conn = self.engine.connect()
        self._conn.execution_options(isolation_level="AUTOCOMMIT")
        return (self._ssh_connection, self._conn)

    def close(self):
        self._ssh_connection.__exit__()

    def testCipher(self):
        engine = create_engine(self.connection_string)
        connection = engine.connect()
        connection.close()

    def _set_connection_parameters(self, conf, filename=None, resource=""):
        if filename or resource:
            conf=fn.load_secret_file(filename or 'db_connections')
        jq=JsonQ(conf)
        self.ssh_command = jq.str(f'..{resource}.db.ssh').replace('[]','') or self.ssh_command 
        self.connection_string = jq.str(f'..{resource}.db.url').replace('[]','') or self.connection_string
        

    def open_ssh(self, key_file):
        if os.path.isfile(key_file):
            return fn.run_cmd(f"{self.ssh_command} -i {key_file}")
        elif os.path.isdir(key_file):
            key_files = os.listdir(key_file)
            opt = " ".join(
                f" -i {key_file}/{f}"
                for f in key_files
                if not re.match(r"(.*(\Wpub|known|config).*)", f)
            )
            return fn.run_cmd(self.ssh_command + " " + opt)
        else:
            raise FileNotFoundError(f"Key file or directory not found: {key_file}")

    def ssh_run(
        self, sql_func, *args, key_file=f"{Path.home()}/.ssh", ssh_wait=25, **kwargs
    ):
        func = sql_func if sql_func is not None else self.tables
        if self.ssh_command is None or self.ssh_command.lower() == "no":
            return func(*args, **kwargs)
        with self.open_ssh(key_file) as con:
            try:
                con.wait(ssh_wait)
                results = func(*args, **kwargs)
            except Exception as e:
                print(f"Error executing query: {e}")
                results = None
        self.engine.dispose()
        return results

    def exec(self, query, params=None):
        query = self._bind(query)
        with self.Session() as session:
            try:
                rs = session.execute(text(query), params)
                session.commit()
                return rs.rowcount
            except Exception as e:
                session.rollback()
                print(f"Error executing query: {e}")

    def _bind(self, sql, params=None):
        if params is None:
            return sql
        for key in params:
            sql = re.sub(rf"\[\s*{key}\s*]", f" :{key}", sql)
        return sql

    def query(
        self, sql, params=None, format: ResultFormat = ResultFormat.LIST
    ):
        if self._conn is None:
            self.connect()
        try:
            sql = self._bind(sql, params)
            result = self._conn.execute(text(sql), params or {})
            cols = result.keys()
            rows = result.fetchall()
            return format(cols,rows)
        except SQLAlchemyError:
            self._conn.rollback()
            raise

    def file(self, filename, params=None, exec=False, *args, **kwargs):
        func = self.query if not exec else self.exec
        with open(filename, "r") as file:
            return func(file.read(), params, *args, **kwargs)

    def tables(
        self,
        schema="public",
        *args,
        **kwargs
    ):
        query = f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema}'"
        return self.query(query)

    def views(self, schema="public"):
        query = f"SELECT table_name FROM information_schema.views WHERE table_schema = '{schema}'"
        return self.query(query)

    def table(self, table_name, schema="public", *args, **kwargs):
        with resources.as_file(resources.files("dihlibs").joinpath("data/describe_table.sql")) as sql_path:
            return self.file(str(sql_path), {"table": table_name, "schema": schema})

    def view(self, view_name,*args, **kwargs):
        return self.query(
            f"SELECT definition FROM pg_views WHERE viewname = '{view_name}'"
        )

    def select_part_matview(self, sql_file):
        sql = fn.text(sql_file)
        regex = r"create mater[^\(]*\(([^;]+)\)"
        select = re.findall(regex, sql, re.MULTILINE | re.IGNORECASE)
        return select[0] if select else sql

    def quote_columns_names(self, names):
        return [f'"{n}"' if " " in n else n for n in names]

    def ssh_upate_table_df(self, df, tablename, id_column="id", on_conflict=""):
        return self.ssh_run(self.upate_table_df, df, tablename, id_column, on_conflict)

    def _format_value(self, value, dtype):
        if pd.isna(value):  # Handle NaN or None values
            if pd.api.types.is_numeric_dtype(dtype):
                return "NULL::NUMERIC"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                return "NULL::TIMESTAMP"
            elif isinstance(dtype, str) and dtype.lower() == "jsonb":
                return "NULL::JSONB"
            else:
                return "NULL"
        elif pd.api.types.is_numeric_dtype(dtype):
            return str(value)
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'::TIMESTAMP"
        elif isinstance(value, (list, dict)):
            return f"""'{json.dumps(value).replace("'","''")}'::JSONB"""
        else:  # Default to string
            v = str(value).replace("'", "''")
            return f"'{v}'"

    def to_cte(self, df, cte_name):
        df = df.copy()
        db_columns = self.quote_columns_names(df.columns)
        columns = ",".join(db_columns)
        # Format values properly
        for c, dtype in zip(df.columns, df.dtypes):
            df[c] = df[c].apply(lambda v: self._format_value(v, dtype))
        values = df.apply(lambda r: f"({','.join(map(str, r.values))})", axis=1)
        valuesx = ',  '.join(values)
        return f"""{cte_name}({columns}) AS ( VALUES {valuesx})
        """

    def update_table_df(self, df, tablename, id_columns, on_conflict=""):
        df = df.copy()
        db_columns = self.quote_columns_names(df.columns)
        columns = ",".join(db_columns)
        update_columns = ",".join([f"temp.{c}" for c in db_columns])
        set_columns = ",\n".join([f"{c}=temp.{c}" for c in db_columns])

        # Ensure id_columns is a list
        if isinstance(id_columns, str):
            id_columns = [id_columns]

        # Create SQL condition for multiple ID columns
        id_condition = " AND ".join([f"u_table.{col}=temp.{col}" for col in id_columns])
        where_clause = " AND ".join([f"u_table.{col} IS NULL" for col in id_columns])

        # Format values properly
        for c, dtype in zip(df.columns, df.dtypes):
            df[c] = df[c].apply(lambda v: self._format_value(v, dtype))
        values = df.apply(lambda r: f"({','.join(map(str, r.values))})", axis=1)

        sql = resources.files("dihlibs").joinpath("data/df_update_table.sql").read_text()
        sql = sql.format(
            tablename=tablename,
            columns=columns,
            set_columns=set_columns,
            update_columns=update_columns,
            id_condition=id_condition,
            where_clause=where_clause,
            values=",\n".join(values),
            on_conflict=on_conflict,
        )
        return self.exec(sql)

    def refresh_matviews(self, schema=["public"]):
        sql = resources.files("dihlibs").joinpath("data/matview_dependencies.sql").read_text()
        sql = sql.format(schema="','".join(schema))
        df = self.secure.query(sql)
        df.loc[df.matview_name == df.depends_on, "depends_on"] = None
        dc = df[df.view_schema.isin(schema)]
        dt = dc[["matview_name", "depends_on"]].copy()

        graph = Graph(dt.values.tolist(), lambda x: x)
        x = graph.topological_sort()
        x = [y.value for y in x]

        def refresh_matview():
            for m in x:
                schema = df[df.matview_name == m].view_schema.unique()[0]
                self.exec(f"refresh materialized view {schema}.{m}")
                print(f"refreshed materialized view {schema}.{m}")
                if m == "chw_p4p":
                    return

        self.ssh_run(refresh_matview)

    @property
    def secure(self) -> "DB":
        class SecureProxy:
            def __init__(self, instance):
                self._instance = instance

            def __getattr__(self, name):
                method = getattr(self._instance, name)
                if callable(method):
                    # Wrap the method to pass through ssh_run
                    def wrapped(*args, **kwargs):
                        return self._instance.ssh_run(method, *args, **kwargs)

                    return wrapped
                return method

            def __dir__(self):
                return dir(self._instance)

        return SecureProxy(self)

    def save_connection(
        self, name, ssh_cmd, connection_url, secret_path="db_connections"
    ):
        conf = fn.load_secret_file(secret_path)
        conf[name] = {"db": {"ssh": ssh_cmd, "url": connection_url}}
        file = tempfile.gettempdir() + "/db_connections"
        with open(file, "wb") as sfile:
            sfile.write(yaml.dump(conf).encode("utf-8"))
        encrypt_secret(file, overwite=True)
        if os.path.isfile(file):
            os.remove(file)

    # registry.register("sqlcipher", "dihlibs.SQLCipherDialect", "SQLCipherDialect")
