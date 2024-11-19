import os
import json
import time
import argparse
import tempfile
import traceback
from colorama import init, Fore, Style
from owslib.wfs import WebFeatureService

# fix colorama colors in windows console
init(convert=True)

tmp_folder = f'{tempfile.gettempdir()}\\wfs-downloader'
config = 'configuration'
sleep = 0

parser = argparse.ArgumentParser(description='Script to download images from a WMTS service')
parser.add_argument('config', type=str, metavar='Configuration file name', default=config, help='Layer name (default: %(default)s)')
parser.add_argument('--overwrite', action='store_true', help='Overwrite if already exists the file or the table (default: %(default)s)')
parser.add_argument('--sleep', type=float, metavar='Sleep time', default=sleep, help='Sleep time (in seconds) betweeen each reques to avoid overloading the server (default: %(default)s)')

args = parser.parse_args()

def main():

    global output_folder, config

    try:

        print('--> PROCESS STARTED <--')
        print('\t')
        
        config = args.config
        overwrite = args.overwrite

        # Open and read the JSON file
        with open(f'{config}.json', 'r') as file:
            data = json.load(file)
            
        output_format = data['output_format'] or 'application/json'
        srs = data['srs'] or 'urn:x-ogc:def:crs:EPSG:4326'
        bbox = data['bbox']   
        layers_group = data['group']
        
        for group in layers_group:
                    
            wfs = WebFeatureService(url=group['url'], version=group['version'])
            
            print(f'Downloading layers from {wfs.identification.title}')
            
            print(list(wfs.contents))

            for layer in group['layers']:
                layer_name = layer["name"]
                print('\t')
                print(f'-> Downloading layer {layer_name}')

                response = wfs.getfeature(typename=layer_name, outputFormat=output_format, bbox=(*bbox, ), srsname=srs)                

                if layer['target']:
                    for target in layer['target']:
                        if 'file' in target:
                            filename = target["file"]

                            # Create folder if not exists
                            os.makedirs(os.path.dirname(filename), exist_ok=True)

                            file_already_exists = os.path.exists(filename)

                            if (file_already_exists):
                                if (overwrite):
                                    print(f'--> Overwriting file {filename}')
                                else:
                                    print(f'--> Skiping existing file {filename}')
                                    continue 
                            else:
                                print(f'--> Exporting to file {filename}')

                            with open(filename, 'wb') as f:
                                f.write(response.read())
                        
                        if 'table' in target:
                            table = target["table"]
                            print(f'--> Exporting to table {table}')


                if sleep:
                    time.sleep(sleep)
        
    except Exception as error:
        print(f'{Fore.RED}{error}{Style.RESET_ALL}')
        print(traceback.format_exc())
        
if __name__ == "__main__":
    main()