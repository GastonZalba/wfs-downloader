import os
import re
import json
import time
import argparse
import traceback

import geojson
import requests
from colorama import init, Fore, Style
from owslib.wfs import WebFeatureService

from databaseConnection import DatabaseConnection

# fix colorama colors in windows console
init(convert=True)

config = "configuration"
database = None
sleep = 0

parser = argparse.ArgumentParser(
    description="Script to download features from WFS services"
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
    help="Overwrite if already exists the file or the table",
)
parser.add_argument(
    "--droptables",
    action="store_true",
    help="Delete the existing tables instead of only cleaning/adding the values. Only used if `overwrite` is active and store to table is configured",
)
parser.add_argument(
    "--styles",
    action="store_true",
    help="Download the sld styles",
)
parser.add_argument(
    "--metadata",
    action="store_true",
    help="Request and store the layer's abstract, title and keywords",
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
drop_tables = args.droptables
sleep = args.sleep
database = args.dbconfig
download_styles = args.styles
download_metadata = args.metadata


def get_valid_filename(name):
    s = str(name).strip().replace(" ", "_").replace(":", "--")
    s = re.sub(r"(?u)[^-\w.]", "", s)
    if s in {"", ".", ".."}:
        raise NameError("Could not derive file name from '%s'" % name)
    return s


def export_file(output, data):

    if os.path.exists(output):
        if overwrite:
            print(f"--> Overwriting file '{output}'")
        else:
            print(f"--> Skiping existing file '{output}'")
            return
    else:
        print(f"--> Saving to file '{output}'")

    with open(output, "wb") as f:
        f.write(data)


def export_to_table(db, schema, table, geojson_data):

    if not table:
        print("---> Table name is not specified, skipping...")
        return

    table = table.lower()

    print(f"--> Working on table '{schema}.{table}'")

    if not hasattr(db, "cur"):
        print(
            f"{Fore.RED}---> Invalid database configuration, skipping database operations'{Style.RESET_ALL}"
        )
        return

    sql = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE  table_schema = %s
            AND    table_name   = %s
        )"""

    db.cur.execute(sql, (schema, table))
    table_exists = db.cur.fetchone()[0]

    create_table = True

    if table_exists:

        if overwrite:
            if drop_tables:
                print("---> Removing previous table...")
                db.cur.execute(f"DROP TABLE IF EXISTS {schema}.{table} CASCADE;")
            else:
                create_table = False
                print("---> Removing previous values...")
                db.cur.execute(f"DELETE FROM {schema}.{table};")

        else:
            print("---> Skiping table, already exists and overwrite is disabled")
            return

    db.cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    data = geojson.loads(geojson_data)
    sample_feature = data["features"][0]
    properties = sample_feature["properties"]

    if create_table:
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
        print("---> Table created")

    print("---> Saving values...")

    insert_query = f"""
        INSERT INTO {schema}.{table} (geom, {", ".join(f'"{key}"' for key in properties.keys())})
        VALUES (ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326), {", ".join(["%s"] * len(properties))})
    """

    for feature in data["features"]:
        geom = geojson.dumps(feature["geometry"])
        values = tuple(feature["properties"].values())
        db.cur.execute(insert_query, (geom, *values))

    print(f"{Fore.GREEN}---> {len(data['features'])} entries inserted{Style.RESET_ALL}")
    db.conn.commit()


def main():

    try:

        print("--> PROCESS STARTED <--")
        print("\t")

        # Open and read the JSON file
        with open(f"{config}.json", "r") as file:
            data = json.load(file)

        output_format = "application/json"
        srs = data["srs"] or "urn:x-ogc:def:crs:EPSG:4326"
        bbox = data["bbox"]
        layers_groups = data["groups"]

        for group in layers_groups:
            geoserver_url = group["url"]

            print(f"-> Connecting to the server {geoserver_url}...")

            version = group["version"] or "1.1.0"

            try:
                wfs = WebFeatureService(url=geoserver_url, version=version)
            except Exception as error:
                print(error)
                print(f"{Fore.RED}-> Can't connect to server{Style.RESET_ALL}")
                print(
                    f"{Fore.RED}--> PROCESS WAS ABORTED WITH ERRORS <--{Style.RESET_ALL}"
                )
                return

            print(f"-> Connected to '{wfs.identification.title}'")
            print("-> Downloading layers...")

            for layer_name in group["layers"]:
                print("\t")
                print(f"-> Downloading layer '{layer_name}'")

                response = wfs.getfeature(
                    typename=layer_name,
                    outputFormat=output_format,
                    bbox=(*bbox,),
                    srsname=srs,
                )

                geojson_data = response.read()

                # global output folder configuration
                output_folder = os.path.abspath(data["output_folder"])

                # create folder if not exists
                os.makedirs(output_folder, exist_ok=True)

                if download_styles:
                    r = requests.get(
                        f"{geoserver_url}?service=WMS&version=1.1.1&request=GetStyles&layers={layer_name}",
                        timeout=30,
                    )

                    output = os.path.join(
                        output_folder, f"{get_valid_filename(layer_name)}.sld"
                    )

                    export_file(output, r.text.encode())

                if download_metadata:
                    if layer_name in wfs.contents:

                        layer_metadata = wfs.contents[layer_name]
                        text = ""
                        text += f"Title: {layer_metadata.title}\n"
                        text += f"Abstract: {layer_metadata.abstract}\n"
                        text += f"Keywords: {', '.join(layer_metadata.keywords)}\n"

                        output = os.path.join(
                            output_folder, f"{get_valid_filename(layer_name)}.txt"
                        )

                        export_file(output, text.encode())

                if output_folder:
                    output = os.path.join(
                        output_folder, f"{get_valid_filename(layer_name)}.geojson"
                    )

                    export_file(output, geojson_data)

                if database:
                    schema = data["table_schema"] or "public"

                    # maybe remove the workspace from the layername
                    layer_split_arr = layer_name.split(":")

                    table = (
                        layer_split_arr[1]
                        if len(layer_split_arr) > 1
                        else layer_split_arr[0]
                    )

                    db = DatabaseConnection(database)
                    export_to_table(db, schema, table, geojson_data)

                if sleep:
                    time.sleep(sleep)

        print("\t")
        print("--> PROCESS FINISHED <--")

    except Exception as error:
        print(f"{Fore.RED}{error}{Style.RESET_ALL}")
        print(traceback.format_exc())


if __name__ == "__main__":
    main()
