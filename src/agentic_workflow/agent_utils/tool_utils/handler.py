import logging
import os
from contextlib import contextmanager
from typing import List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor, RealDictRow

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class PsqlHandler:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.database = os.getenv("DB_NAME", "postgres")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASS", "postgres")
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

    def get_devices(self, device_names: Optional[List[str]] = None):
        where_statement = ""

        if device_names:
            device_names = [f"{name}%" for name in device_names]
            where_statement = "WHERE " + " OR ".join(
                ["d.name LIKE %s" for _ in device_names]
            )

        query = f"""
            SELECT
                d.name AS device_name,
                a.name AS asset_name,
                dc.name AS category,
                string_agg(v.title, ';') AS vulnerabilities,
                string_agg(v.cve, ';') AS cves
            FROM devices AS d
            INNER JOIN device_vulnerabilities i ON d.id = i.device_id
            INNER JOIN vulnerabilities v ON i.vulnerability_id = v.id
            INNER JOIN assets a ON d.asset_id = a.id
            INNER JOIN device_categories dc ON d.category_id = dc.id
            {where_statement}
            GROUP BY d.id, d.name, a.name, dc.name;
            """
        with self.get_cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()
        return data

    def get_devices_vulnerabilities(self, device_name: List[str]) -> List[RealDictRow]:
        if self.is_injection(device_name):
            logging.error("SQL injection detected")
            raise ValueError("SQL injection detected")

        where_statement = ""

        if device_name:
            device_name = [f"{name}%" for name in device_name]
            where_statement = "WHERE " + " OR ".join(
                ["d.name LIKE %s" for _ in device_name]
            )

        query = f"""
        SELECT
            d.name AS device_name,
            dc.name AS category_name,
            v.description,
            v.cve,
            v.discovery_date
        FROM devices AS d
        INNER JOIN device_vulnerabilities i ON d.id = i.device_id
        INNER JOIN vulnerabilities v ON i.vulnerability_id = v.id
        INNER JOIN device_categories dc ON d.category_id = dc.id
        {where_statement}
        """

        with self.get_cursor() as cursor:
            if device_name:
                cursor.execute(query, device_name)
            else:
                cursor.execute(query)
            data = cursor.fetchall()

        return data

    def get_assets(
        self,
        asset_names: Optional[List[str]] = None,
        device_names: Optional[List[str]] = None,
    ):
        where_statement = ""
        assets = ""
        devices = ""

        if asset_names:
            assets = " OR ".join(["a.name LIKE %s" for _ in asset_names])

        if device_names:
            devices = " OR ".join(["at.name LIKE %s" for _ in device_names])

        if assets or devices:
            where_statement = "WHERE " + assets + " AND " + devices

        query = f"""
        SELECT
            a.name,
            a.created_at,
            STRING_AGG(d.name, ', ' ORDER BY d.name) AS device_names,
            at.name AS asset_type
        FROM assets AS a
        INNER JOIN asset_types AS at ON a.type_id = at.id
        LEFT JOIN devices AS d ON a.id = d.asset_id
        {where_statement}
        GROUP BY a.id, a.name, at.name
        ORDER BY a.name;
        """

        with self.get_cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()

        return data

    def get_vulnerabilities(self):
        query = """
        SELECT
            v.title,
            v.description,
            v.cve,
            v.discovery_date,
            STRING_AGG(d.name, ', ' ORDER BY d.name) AS device_name
        FROM vulnerabilities AS v
        INNER JOIN device_vulnerabilities i ON v.id = i.vulnerability_id
        INNER JOIN devices d ON i.device_id = d.id
        GROUP BY v.title, v.description, v.cve, v.discovery_date;
        """

        with self.get_cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()

        return data

    def insert_asset_types(self, type_names: List[str]):
        names = list(set(type_names))

        data = [(name.lower().replace(" ", "_"), name) for name in names]

        query = """
        INSERT INTO asset_types (id, slug, name)
        VALUES (gen_random_uuid(), %s, %s)
        ON CONFLICT (slug) DO NOTHING;
        """

        logging.info(f"{data}")

        try:
            with self.get_cursor() as cursor:
                cursor.executemany(query, data)
            return True
        except Exception as e:
            logging.info(f"Couldn't add items to asset_types: {e}")
            return False

    def verify_asset_e_category(self, column: str, infos: List[str]):
        logging.info(f"Column: {column} and Infos:{infos}")
        verification_query_dict = {
            "asset_types": "SELECT name, id FROM asset_types WHERE name = ANY(%s)",
            "device_categories": "SELECT name FROM device_categories WHERE name = ANY(%s)",
        }

        verification_query = verification_query_dict[column]
        with self.get_cursor() as cursor:
            cursor.execute(verification_query, (infos,))
            existing_types = cursor.fetchall()
        logging.info(f"Existing types at db:{existing_types}")
        return existing_types

    def insert_assets(self, assets: List[Tuple[str, str]]):
        insertion_query = """
            INSERT INTO assets (id, name, type_id)
            VALUES (gen_random_uuid(), %s, %s);
        """

        type_names = [value[1] for value in assets]
        existing_types = self.verify_asset_e_category("asset_types", type_names)

        logging.info(f"Existing types at db:{existing_types}")

        type_name_to_id = {row["name"]: row["id"] for row in existing_types}

        logging.info(f"Type name to id:{type_name_to_id}")

        asset_names_ins = [
            (asset_name, type_name_to_id[type_name])
            for asset_name, type_name in assets
            if type_name in type_name_to_id
        ]

        if asset_names_ins:
            with self.get_cursor() as cursor:
                cursor.executemany(insertion_query, asset_names_ins)

        valid_type_names = set(type_name_to_id.keys())
        requested_type_names = set(type_names)
        return list(requested_type_names - valid_type_names)

    def update_asset(self, assets: List[Tuple[str, str]]):
        update_query = """
        UPDATE assets
        SET type_id = (SELECT id FROM asset_types WHERE name = %s)
        WHERE name = %s;
        """

        existing_types = self.verify_asset_e_category(
            "asset_types", [value[0] for value in assets]
        )
        total_assets_names = [value[1] for value in assets]

        with self.get_cursor() as cursor:
            if existing_types:
                asset_names_ins = [
                    (value[1], asset_type["id"])
                    if asset_type["name"] == value[0]
                    else None
                    for asset_type, value in zip(existing_types, assets)
                ]
                logging.info(f"Asset names ins: {asset_names_ins}")
                cursor.executemany(update_query, asset_names_ins)
        logging.info(f"Existing types: {existing_types}")

        return (
            list(
                set(total_assets_names)
                - set([value["name"] for value in existing_types])
            )
            if existing_types
            else total_assets_names
        )

    def possible_device(self, info: List[Tuple[str, str]]):
        verification_assets = "SELECT name, id FROM assets WHERE name = ANY(%s)"
        verification_categories = (
            "SELECT name, id FROM device_categories WHERE name = ANY(%s)"
        )

        asset_names = list(set(asset_name for asset_name, _ in info))
        category_names = list(set(category_name for _, category_name in info))

        with self.get_cursor() as cursor:
            cursor.execute(verification_assets, (asset_names,))
            assets = {row["name"]: row["id"] for row in cursor.fetchall()}

            cursor.execute(verification_categories, (category_names,))
            categories = {row["name"]: row["id"] for row in cursor.fetchall()}

        logging.info(f"Assets: {assets}")
        logging.info(f"Categories: {categories}")

        existing_devices = {}
        for asset_name, category_name in info:
            if asset_name in assets and category_name in categories:
                existing_devices[(asset_name, category_name)] = (
                    assets[asset_name],
                    categories[category_name],
                )

        return existing_devices

    def insert_device(self, devices: List[Tuple[str, str, str]]):
        insertion_query = """
            INSERT INTO devices (id, name, asset_id, category_id)
            VALUES (gen_random_uuid(), %s, %s, %s);
        """

        info = [(asset_name, category_name) for _, asset_name, category_name in devices]
        existing_devices = self.possible_device(info)

        device_insertion = []
        failed_devices = []

        logging.info(f"Existing devices: {existing_devices}")

        for device_name, asset_name, category_name in devices:
            lookup_key = (asset_name, category_name)
            logging.info(f"lookup_key: {lookup_key}")
            if lookup_key in existing_devices:
                asset_id, category_id = existing_devices[lookup_key]
                device_insertion.append((device_name, asset_id, category_id))
            else:
                failed_devices.append((device_name, asset_name, category_name))

        logging.info(
            f"Failed devices:{failed_devices}, Device insertion:{device_insertion}"
        )

        if device_insertion:
            with self.get_cursor() as cursor:
                cursor.executemany(insertion_query, device_insertion)

        return list(set(failed_devices))

    def update_devices_info(self, column: str, devices: List[Tuple[str, str]]):
        verificator_query_dict = {
            "devices_name": "SELECT name FROM devices WHERE name = ANY(%s)",
            "asset_name": "SELECT name, id FROM assets WHERE name = ANY(%s)",
            "category_name": "SELECT name, id FROM device_categories WHERE name = ANY(%s)",
        }

        update_query_dict = {
            "devices_name": "UPDATE devices SET name = %s WHERE name = %s;",
            "asset_name": "UPDATE devices SET asset_id = %s WHERE name = %s",
            "category_name": "UPDATE devices SET category_id = %s WHERE name = %s",
        }

        if column not in verificator_query_dict:
            logging.error(f"Invalid column name: {column}")
            raise ValueError(f"Invalid column: {column}")

        verificator_query = verificator_query_dict[column]
        update_query = update_query_dict[column]

        if column != "devices_name":
            verify_info = [new for _, new in devices]
        else:
            verify_info = [old_name for old_name, _ in devices]

        logging.info(f"Verify info:{verify_info}")

        with self.get_cursor() as cursor:
            cursor.execute(verificator_query, (verify_info,))
            existent_info = cursor.fetchall()

            logging.info(f"existent info:{existent_info}")

            if column != "devices_name":
                name_to_id = {row["name"]: row["id"] for row in existent_info}
                logging.info(f"name_to_id:{name_to_id}")
                info_set = set(row["name"] for row in existent_info)
                logging.info(f"info_set:{info_set}")
                updated_info = [
                    (name_to_id[info_name], device)
                    for device, info_name in devices
                    if info_name in info_set
                ]
                logging.info(f"updated_info:{updated_info}")
            else:
                existent_info = [device["name"] for device in existent_info]
                existent_set = set(existent_info)

                updated_info = [
                    (new_name, old_name)
                    for (old_name, new_name) in devices
                    if old_name in existent_set
                ]

            logging.info(f"Updated info:{updated_info}")

            cursor.executemany(update_query, updated_info)
        return (
            list(set(old_devices for old_devices, _ in devices))
            if column == "devices_name"
            else list(set(verify_info))
        )

    def insert_device_category(self, categories: List[str]):
        insertion_query = """
            INSERT INTO device_categories (id, slug, name)
            VALUES (gen_random_uuid(), %s, %s);
        """
        try:
            with self.get_cursor() as cursor:
                cursor.executemany(
                    insertion_query,
                    [
                        (category_name.lower().replace(" ", "_"), category_name)
                        for category_name in categories
                    ],
                )
                return True
        except Exception as e:
            logging.error(f"Error inserting device categories: {e}")
            return False

    def update_device_category_name(self, names: List[Tuple[str, str]]):
        update_query = """
            UPDATE device_categories
            SET name = %s,
                slug = %s
            WHERE name = %s;
        """

        old_names = [name[0] for name in names]
        existent_device_categories = self.verify_asset_e_category(
            "device_categories", old_names
        )

        if existent_device_categories is None:
            logging.info("No name found")
            return [name[0] for name in names]

        existent_device_categories = [
            category["name"] for category in existent_device_categories
        ]

        logging.info(f"Existing device categories: {existent_device_categories}")

        existent_set = set(existent_device_categories)

        to_update = [
            (old_name, new_name)
            for old_name, new_name in names
            if old_name in existent_set
        ]

        new_slugs = [new_name.lower().replace(" ", "_") for _, new_name in to_update]
        new_data = [
            (new_name, slug) for (_, new_name), slug in zip(to_update, new_slugs)
        ]

        replacer = [
            (new_name, new_slug, old_name)
            for old_name, (new_name, new_slug) in zip(
                existent_device_categories, new_data
            )
        ]
        logging.info(f"Replacer: {replacer}")

        with self.get_cursor() as cursor:
            cursor.executemany(update_query, replacer)

        old_set = set(old_names)
        return list(old_set - existent_set)

    def is_cve(self, code: str):
        if "CVE" not in code.upper():
            return False

        cve_parts = code.split("-")

        if len(cve_parts) != 3:
            return False
        if not cve_parts[1].isdigit() and len(cve_parts[1]) != 4:
            return False
        if not cve_parts[2].isdigit():
            return False
        return True

    def insert_vulnerabilities(
        self, vulnerabilities: List[Tuple[str, str, str, Optional[str]]]
    ):
        insert_query = """
            INSERT INTO vulnerabilities (id, title, description, cve, discovery_date)
            VALUES (gen_random_uuid(), %s, %s, %s, %s)
        """

        vulnerabilities_insertion = [
            (
                title,
                description,
                cve if (cve and self.is_cve(cve)) else None,
                discovery_date,
            )
            for (title, description, discovery_date, cve) in vulnerabilities
        ]

        logging.info(f"Inserting vulnerabilities: {vulnerabilities_insertion}")

        try:
            with self.get_cursor() as cursor:
                cursor.executemany(insert_query, vulnerabilities_insertion)
            return True
        except Exception as e:
            logging.error(f"Couldn't insert due to:{e}")
            return False

    def update_vulnerability_name(self, vulnerabilities_names: List[Tuple[str, str]]):
        update_query = """
            UPDATE vulnerabilities
            SET title = %s
            WHERE title = %s
        """
        old_vulnerabilities = [old for old, _ in vulnerabilities_names]
        verificator_query = "SELECT title FROM vulnerabilities WHERE title = ANY(%s)"

        with self.get_cursor() as cursor:
            cursor.execute(verificator_query, (old_vulnerabilities,))
            existent_vulnerabilities = cursor.fetchall()

            existent_set = set(vul["title"] for vul in existent_vulnerabilities)

            updated_data = [
                (new_title, old_title)
                for new_title, old_title in vulnerabilities_names
                if old_title not in existent_set
            ]

            cursor.executemany(update_query, updated_data)

        old_set = set(old_vulnerabilities)
        return list(old_set - existent_set) if existent_set else list(old_set)
