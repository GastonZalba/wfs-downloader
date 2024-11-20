import os
import json
import time
import geojson
import argparse
import tempfile
import traceback
from colorama import init, Fore, Style
from owslib.wfs import WebFeatureService

from databaseConnection import DatabaseConnection

# fix colorama colors in windows console
init(convert=True)


def main():

    try:

        config = "configuration"
        sleep = 0
        database = "dev"

        parser = argparse.ArgumentParser(
            description="Script to download images from a WMTS service"
        )
        parser.add_argument(
            "config",
            type=str,
            metavar="Configuration file name",
            default=config,
            help="Layer name (default: %(default)s)",
        )
        parser.add_argument(
            "--dbconfig",
            type=str,
            metavar="Db config",
            default=database,
            help="Database configuration section inside the database.ini (default: %(default)s)",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite if already exists the file or the table (default: %(default)s)",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            metavar="Sleep time",
            default=sleep,
            help="Sleep time (in seconds) between each reques to avoid overloading the server (default: %(default)s)",
        )
  
        args = parser.parse_args()

        config = args.config
        overwrite = args.overwrite
        sleep = args.sleep
        database = args.database

        print("--> PROCESS STARTED <--")
        print("\t")

        db = DatabaseConnection(database)

        # Open and read the JSON file
        with open(f"{config}.json", "r") as file:
            data = json.load(file)

        output_format = data["output_format"] or "application/json"
        srs = data["srs"] or "urn:x-ogc:def:crs:EPSG:4326"
        bbox = data["bbox"]
        layers_group = data["group"]

        for group in layers_group:

            version = group["version"] or "1.1.0"
            wfs = WebFeatureService(url=group["url"], version=version)

            print(f"Downloading layers from {wfs.identification.title}")

            print(list(wfs.contents))

            for layer in group["layers"]:
                layer_name = layer["name"]
                print("\t")
                print(f"-> Downloading layer {layer_name}")

                response = wfs.getfeature(
                    typename=layer_name,
                    outputFormat=output_format,
                    bbox=(*bbox,),
                    srsname=srs,
                )
                geojson_data = response.read()

                if layer["target"]:
                    for target in layer["target"]:
                        if "file" in target:
                            filename = target["file"]

                            # Create folder if not exists
                            os.makedirs(os.path.dirname(filename), exist_ok=True)

                            file_already_exists = os.path.exists(filename)

                            if file_already_exists:
                                if overwrite:
                                    print(f"--> Overwriting file {filename}")
                                else:
                                    print(f"--> Skiping existing file {filename}")
                                    continue
                            else:
                                print(f"--> Saving to file {filename}")

                            with open(filename, "wb") as f:
                                f.write(geojson_data)

                        if "table" in target:
                            table = target["table"]
                            schema = target["schema"] or "public"

                            sql = """
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables 
                                    WHERE  table_schema = %s
                                    AND    table_name   = %s
                                )"""
                            
                            db.cur.execute(sql, (schema, table))                         
                            table_exists = db.cur.fetchone()[0]
                            
                            if table_exists:
                                if overwrite:
                                    db.cur.execute(
                                        f"DROP TABLE IF EXISTS {schema}.{table} CASCADE;"
                                    )
                                    print(f"--> Removing old table {schema}.{table}")
                                else:
                                    print(
                                        f"--> Skiping existing table {schema}.{table}"
                                    )
                                    continue

                            print(f"--> Saving to table {schema}.{table}")

                            db.cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

                            data = geojson.loads(geojson_data)

                            sample_feature = data["features"][0]
                            properties = sample_feature["properties"]

                            columns = []
                            for key, value in properties.items():
                                if isinstance(value, int):
                                    column_type = "INTEGER"
                                elif isinstance(value, float):
                                    column_type = "FLOAT"
                                elif isinstance(value, bool):
                                    column_type = "BOOLEAN"
                                else:
                                    column_type = "TEXT"
                                columns.append(f'"{key}" {column_type}')

                            create_table_query = f"""
                            CREATE TABLE {schema}.{table} (
                                id SERIAL PRIMARY KEY,
                                geom GEOMETRY(Geometry, 4326),
                                {", ".join(columns)}
                            )
                            """
                            db.cur.execute(create_table_query)
                            print(f"Table created {schema}{table}.")

                            insert_query = f"""
                                INSERT INTO {schema}.{table} (geom, {", ".join(f'"{key}"' for key in properties.keys())})
                                VALUES (ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326), {", ".join(["%s"] * len(properties))})
                            """

                            for feature in data["features"]:
                                geom = geojson.dumps(feature["geometry"])
                                values = tuple(properties.values())
                                db.cur.execute(insert_query, (geom, *values))
                            
                            print(f"Inserted entries in {schema}{table}.")
                            db.conn.commit()

                if sleep:
                    time.sleep(sleep)

    except Exception as error:
        print(f"{Fore.RED}{error}{Style.RESET_ALL}")
        print(traceback.format_exc())


if __name__ == "__main__":
    main()
