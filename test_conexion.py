from conexion_db import conectar_bd

conexion = conectar_bd()
if conexion:
    cursor = conexion.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print("Versión de PostgreSQL:", version)
    conexion.close()