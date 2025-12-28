# DB 로더
import pymysql

def get_connection():
    """
    MariaDB 연결 객체 반환
    """
    return pymysql.connect(
        host="localhost",
        user="dbid253",
        password="dbpass253",
        database="db25322",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )