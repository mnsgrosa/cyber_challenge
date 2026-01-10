from contextlib import contextmanager
from typing import Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor, RealDictRow


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

    def is_injection(self, items):
        if all(guard in items for guard in self.guard_list):
            return True
        return False

    def list_devices(self):
        query = """
            SELECT DISTINC(name) FROM devices
        """
        with self.get_cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()
        data = [row["name"] for row in data]
        return data

    def get_devices_vulnerabilities(self, device_name: List[str]) -> List[RealDictRow]:
        """
        Method that outputs all devices and vulnerabilities or from specific devices
        returns a dicitionary with columns id, name, description, cve and discovery_date
        """
        if self.is_injection(device_name):
            raise ValueError("SQL injection detected")

        if device_name:
            device_name = [f"{name}%" for name in device_name]

        query = """
        SELECT
            d.name as device_name,
            dc.name as category_name,
            v.description,
            v.cve,
            v.discovery_date
        FROM devices as d
        INNER JOIN device_vulnerabilities i ON d.id = i.device_id
        INNER JOIN vulnerabilities v ON i.vulnerability_id = v.id
        INNER JOIN device_categories dc ON d.category_id = dc.id
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
