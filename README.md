# wfs-downloader
Script to download vector layers from WFS services. The process downloads all the features and creates a file or store it in a SQL table.

Allows you to:
    - Manage multiples database enviroments (and switch between local/production easily or different databases)
    - Store multiples process configurations (and run only what you want each time)
    - Store the downloaded features in .geojson files and/or SQL tables
    - Control if you want to overwrite existing files
    - Control if you want to remove old tables, or only clean/add the new values (this can be useful if you have views attached to the table, but will fail if the columns changed between process)

## Installation
- Create a local enviroment running `python -m venv .venv` (install [virtualenv](https://virtualenv.pypa.io/en/latest/) if you don't have it)
- Load the local enviroment: `.venv\Scripts\activate`
- Install using `pip install -r requirements.txt`

## Instructions
- Load the enviroment `.venv\Scripts\activate`
- Modify the file `configuration-example.json` according to your needs
- Rename the `database-example.ini` to `database.ini` and modify it
- Run `python wfs-downloader.py --help` to show all available options and arguments
- Run the script with something like this `python wfs-downloader.py configuration-example --dbconfig dev`

## @TODO
- Add pagination for partial WFS requests
- Add vector support to allow clipping features outside a polygon area
- Support more WFS versions (only 1.1.0 supported)
- Support others EPSG (only 4326 supported)