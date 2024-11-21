# wfs-downloader
Script to download vector layers from WFS services. The process downloads all the features and creates a file or store it in a PSQL table.

Allows you to:
    - Manage multiples database enviroments (and switch between local/production easily or different databases)
    - Store multiples process configurations (and run only what you want each time)
    - Store the downloaded features in .geojson files and/or SQL tables
    - Control if you want to overwrite existing files
    - Control if you want to remove old tables, or only clean/add the new values (this can be useful if you have views attached to the table, but will fail if the columns changed between process)
    - Download and save the .sld associated to each layer

## Installation (tested using python 3.9)
- Create a local enviroment running `python -m venv .venv` (install [virtualenv](https://virtualenv.pypa.io/en/latest/) if you don't have it)
- Load the local enviroment: `.venv\Scripts\activate`
- Install using `pip install -r requirements.txt`
- NOTE: to save in a PostgreSQL you need PostGis installed

## Instructions
- Load the enviroment `.venv\Scripts\activate`
- Modify the file `configuration-example.json` according to your needs
- Run `python wfs-downloader.py --help` to show all available options and arguments
- Run the script with something like this `python wfs-downloader.py configuration-example`
- To store in the database, rename the `database-example.ini` to `database.ini`, modify it, and pass the argument `--dbconfig` with the database configuration section. A table with the layername will be created

## @TODO
- Add pagination for partial WFS requests
- Add vector support to allow clipping features outside a polygon area
- Support more WFS versions (only 1.1.0 supported)
- Support others EPSG (only 4326 supported)
- Support to download all layers in the target geoserver
