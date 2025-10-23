import logging
from urllib.parse import quote_plus
from typing import Union, Optional, Type, List, Dict

from influxdb_client import InfluxDBClient
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text, inspect, Engine
from codemie_tools.base.codemie_tool import CodeMieTool, logger
from codemie_tools.data_management.sql.models import SQLConfig, SQLDialect
from codemie_tools.data_management.sql.tools_vars import SQL_TOOL

class SQLToolInput(BaseModel):
    sql_query: str = Field(
        title="SQL Query",
        description="The SQL query to execute. For InfluxDB, use Flux query language.",
    )


class SQLTool(CodeMieTool):
    name: str = SQL_TOOL.name
    description: str = SQL_TOOL.description
    args_schema: Type[BaseModel] = SQLToolInput
    sql_config: Optional[SQLConfig] = Field(exclude=True, default=None)

    def execute(self, sql_query: str):
        if self.sql_config is None:
            return "SQL configuration is not provided. Please provide in 'Integrations'."

        try:
            engine = self.create_db_connection()
            if self.sql_config.dialect == SQLDialect.INFLUXDB:
                data = self._execute_influxdb_query(engine, sql_query)
                return data

            data = self.execute_sql(engine, sql_query)
            return data

        except Exception as exc:
            logging.error(f"Error executing SQL query: {str(exc)}")
            try:
                if self.sql_config.dialect == SQLDialect.INFLUXDB:
                    data = f"""
                    There is an error: {exc}.\n
                    Try to change your Flux query to get the desired result.\n
                    Make sure you're using correct bucket name: {self.sql_config.bucket}\n
                    """
                else:
                    engine = self.create_db_connection()
                    init_data = self.list_tables_and_columns(engine)
                    data = f"""
                    There is an error: {exc}.\n
                    Try to change your query to get the desired result according available details. \n
                    Available tables with columns: {init_data}. \n
                    """
                return data.strip()
            except Exception as exc:
                return f"Error during executing SQL: {str(exc)}"

    def execute_sql(self, engine: Engine, sql_query: str) -> Union[list, str]:
        with engine.connect() as connection:
            try:
                # Start transaction
                with connection.begin():
                    # Execute the query
                    result = connection.execute(text(sql_query))

                    # Process the results
                    if result.returns_rows:
                        columns = result.keys()
                        data = [dict(zip(columns, row)) for row in result]
                        return data
                    else:
                        affected_rows = result.rowcount if hasattr(result, 'rowcount') else 'unknown'
                        return f"Query executed successfully. Rows affected: {affected_rows}"

            except Exception as e:
                logger.error(f"SQL error: {str(e)} in query: {sql_query[:100]}...")
                raise e

    def _execute_influxdb_query(self, influx_db_client: InfluxDBClient, query: str) -> Union[List[Dict], str]:
        query_api = influx_db_client.query_api()
        result = query_api.query(query=query, org=self.sql_config.org)
        # Convert result to list of dictionaries
        records = []
        for table in result:
            for record in table.records:
                records.append(record.values)
        return records

    def list_tables_and_columns(self, engine):
        if self.sql_config.dialect == SQLDialect.INFLUXDB:
            return self.list_influxdb_measurements_and_fields(engine)

        # Default SQL behavior
        inspector = inspect(engine)
        data = {}
        tables = inspector.get_table_names()
        for table in tables:
            columns = inspector.get_columns(table)
            columns_list = []
            for column in columns:
                columns_list.append({"name": column["name"], "type": column["type"]})
            data[table] = {"table_name": table, "table_columns": columns_list}
        return data

    def list_influxdb_measurements_and_fields(self, influx_db_client: InfluxDBClient):
        query_api = influx_db_client.query_api()
        # Get measurements (similar to tables in SQL)
        measurements_query = f"""
            import "influxdata/influxdb/schema"
            schema.measurements(bucket: "{self.sql_config.bucket}")
            """
        measurements = query_api.query(query=measurements_query, org=self.sql_config.org)

        data = {}
        for table in measurements:
            for record in table.records:
                measurement = record.values.get("_value")
                # Get fields for each measurement
                fields_query = f"""
                    import "influxdata/influxdb/schema"
                    schema.measurementFieldKeys(
                        bucket: "{self.sql_config.bucket}",
                        measurement: "{measurement}"
                    )
                    """
                fields = query_api.query(query=fields_query, org=self.sql_config.org)
                fields_list = []
                for field_table in fields:
                    for field_record in field_table.records:
                        fields_list.append(
                            {"name": field_record.values.get("_value"), "type": "field"}
                        )

                data[measurement] = {"measurement_name": measurement, "fields": fields_list}
        return data

    def create_db_connection(self):
        if self.sql_config.dialect == SQLDialect.INFLUXDB:
            return self.sql_config.get_influxdb_client()

        host = self.sql_config.host
        username = quote_plus(self.sql_config.username)
        password = quote_plus(self.sql_config.password)
        database_name = self.sql_config.database_name
        port = self.sql_config.port
        dialect = self.sql_config.dialect

        if dialect == SQLDialect.POSTGRES:
            connection_string = (
                f"postgresql+psycopg://{username}:{password}@{host}:{port}/{database_name}"
            )
        elif dialect == SQLDialect.MYSQL:
            connection_string = (
                f"mysql+pymysql://{username}:{password}@{host}:{port}/{database_name}"
            )
        elif dialect == SQLDialect.MSSQL:
            connection_string = (
                f"mssql+pymssql://{username}:{password}@{host}:{port}/{database_name}"
            )
        else:
            raise ValueError(
                f"Unsupported database type. Supported types are: {[e.value for e in SQLDialect]}"
            )

        return create_engine(connection_string)
