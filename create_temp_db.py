import sqlite3
conn = sqlite3.connect("./temp.db") # or use :memory: to put it in RAM
cursor = conn.cursor()
# create a table
cursor.execute("""CREATE TABLE tempdata
                  (temperature int, humidity int, timestamp int) 
               """)

cursor.execute("""CREATE TABLE tempdata_outside
                  (temperature int, humidity int, wind int, timestamp int) 
               """)