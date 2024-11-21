import os.path
from colorama import init, Fore, Style

import psycopg2

from config import config


DATABASE_FILE = 'database.ini'

class DatabaseConnection:

    def __init__(self, env='dev'):

        if (not os.path.exists(DATABASE_FILE)):
            print(f"{Fore.YELLOW}{'WARNING: Database configuration do not exists and all table operations will be skipped'}{Style.RESET_ALL}")
            return

        paramsDb = config(
            filename=DATABASE_FILE,
            section='postgresql',
            env=env
        )
        
        self.conn = psycopg2.connect(**paramsDb)
        self.cur = self.conn.cursor()
   
