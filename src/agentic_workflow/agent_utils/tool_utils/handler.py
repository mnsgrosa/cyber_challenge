from contextlib import contextmanager
from typing import Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor


class PsqlHandler:
    def __init__(self):
        self.host = "localhost"
        self.port = "5432"
        self.database = "postgres"
        self.user = "postgres"
        self.password = "postgres"
        self.tables = [
            "asset_types",
            "device_categories",
            "assets",
            "devices",
            "vulnerabilities",
            "device_vulnerabilities",
        ]

        self.columns = {
            "asset_types": ["id", "slug", "name", "created_at"],
            "device_categories": ["id", "slug", "name", "created_at"],
            "assets": ["id", "name", "type_id", "created_at"],
            "devices": ["id", "name", "asset_id", "category_id", "created_at"],
            "vulnerabilities": [
                "id",
                "title",
                "description",
                "cve",
                "discovery_date",
                "created_at",
            ],
            "device_vulnerabilities": ["device_id", "vulnerability_id"],
        }

        self.guard_list = ['"or""="', "1=1", "DROP"]

    @contextmanager
    def get_cursor(self):
        self.connection = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )
        try:
            yield self.connection.cursor(cursor_factory=RealDictCursor)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            self.connection.close()
            self.connection = None

    def generic_get(
        self, table_name: Optional[str], columns_and_values: Optional[Dict[str, str]]
    ):
        if table_name is None:
            raise ValueError("Table name cannot be empty")

        if table_name not in self.tables:
            raise ValueError("Table not found")

        if columns_and_values and columns_and_values.keys() in self.columns[table_name]:
            raise ValueError("Column not found at selected table")

        values = []

        if columns_and_values is None:
            selection = "*"
        else:
            selection = ", ".join(columns_and_values.keys())
            values = [
                value if value is not None else None
                for value in columns_and_values.values()
            ]
            for value in values:
                if value in self.guard_list:
                    raise ValueError("SQL injection detected")

        query = f"SELECT {selection} FROM {table_name}"

        if values and columns_and_values:
            query += " WHERE "
            query += " AND ".join([f"{key} = %s" for key in columns_and_values.keys()])

        with self.get_cursor() as cursor:
            if values:
                cursor.execute(query, values)
            else:
                cursor.execute(query)
            raw_data = cursor.fetchall()
        data = [data for data in raw_data]
        return data

    def get_devices_vulnerabilities(self, device_name: Optional[List[str]] = None):
        """
        Method that outputs all devices and vulnerabilities or from specific devices
        returns a dicitionary with columns id, name, description, cve and discovery_date
        """
        if device_name and all(guard in device_name for guard in self.guard_list):
            raise ValueError("SQL injection detected")

        if device_name:
            device_name = [f"{name}%" for name in device_name]

        query = """
        SELECT
            d.id,
            d.name,
            v.id as detail_id,
            v.description,
            v.cve,
            v.discovery_date
            FROM devices as d
            INNER JOIN device_vulnerabilities i ON d.id = i.device_id
            INNER JOIN vulnerabilities v ON i.vulnerability_id = v.id
        """

        if device_name:
            query += "\n WHERE " + " OR ".join(["d.name LIKE %s" for _ in device_name])

        with self.get_cursor() as cursor:
            if device_name:
                cursor.execute(query, device_name)
            else:
                cursor.execute(query)
            data = cursor.fetchall()

        return data
