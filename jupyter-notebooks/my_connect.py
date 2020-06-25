# © Copyright 2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT

import psycopg2
import configparser

CONFIG_FILE = r'c:\keys\sales.properties'

def my_connect():
    config = configparser.RawConfigParser()
    config.read(CONFIG_FILE)
    db_username=config.get('database', 'login')
    db_password=config.get('database', 'password')

    connection = psycopg2.connect(user=db_username, password=db_password, host='localhost', port=5432, database='sales')
    return connection
