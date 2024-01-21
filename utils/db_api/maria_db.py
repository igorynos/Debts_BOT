import pymysql
from data import config


class Database:
    def __init__(self, path_to_db=(config.IP, config.PGUSER, config.PGPASSWORD, config.DATABASE, config.PORT)):
        self.path_to_db = path_to_db

    @property
    def connection(self):
        return pymysql.connect(host=self.path_to_db[0],
                               user=self.path_to_db[1],
                               password=self.path_to_db[2],
                               database=self.path_to_db[3],
                               port=self.path_to_db[4])

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):

        if not parameters:
            parameters = tuple()

        connection = self.connection
        cursor = connection.cursor()
        cursor.execute(sql, parameters)

        data = None

        if commit:
            connection.commit()

        if fetchone:
            data = cursor.fetchone()

        if fetchall:
            data = cursor.fetchall()

        connection.close()

        return data
