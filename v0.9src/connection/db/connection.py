import pymysql

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="dbid253",
        password="dbpass253",
        database="db25322",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )



#### langCahin_v3 db.py와 동일함, 나중에 통일할 것