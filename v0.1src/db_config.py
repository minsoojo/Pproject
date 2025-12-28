# db_config.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymysql

def get_conn():
 
    return pymysql.connect(
        host="localhost",          # ceprj2 안에서 실행된다고 가정
        user="dbid253",
        password="dbpass253",
        database="db25322",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )