# despacho/sqlserver_connector.py

import pyodbc

def get_sqlserver_connection():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=10.0.0.4;'
        'DATABASE=Indupal;'
        'UID=Sa;'
        'PWD=Shell20xx22;',
        timeout=5
    )
