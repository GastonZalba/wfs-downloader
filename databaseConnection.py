import psycopg2

from config import config

class DatabaseConnection:

    def __init__(self, env='dev'):

        paramsDb = config(
            filename='database.ini',
            section='postgresql',
            env=env
        )
        
        self.conn = psycopg2.connect(**paramsDb)
        self.cur = self.conn.cursor()
   
