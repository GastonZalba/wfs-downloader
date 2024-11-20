# wfs-downloader
Script to download vector layers from WFS services. The process downloads all the features and createas a file/table backup.

## Installation
- Create a local enviroment running `python -m venv .venv` (install [virtualenv](https://virtualenv.pypa.io/en/latest/) if you don't have it)
- Load the local enviroment: `.venv\Scripts\activate`
- Install using `pip install -r requirements.txt`

## Instructions
- Load local enviroment `.venv\Scripts\activate`
- Modify the file `configuration-example.json` according to your needs
- Rename the `database-example.ini` to `database.ini` and modify it
- Run `python wfs-downloader.py --help` to show all available options and arguments
- Run the script with something like this `python wfs-downloader.py configuration-example --dbconfig dev`
- You can use the `sleep` arguments to avoid overloading the target server

## @TODO
- Add pagination for incomplete wfs requests
- Add vector support to allow clipping features outside a polygon area
- Support more WFS versions (only 1.1.0 supported)
- Support others EPSG (only 4326 supported)