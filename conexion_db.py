import psycopg2
from psycopg2 import sql, Error
from tkinter import messagebox

# ---------- CONEXION A LA BASE DE DATOS EN PG ADMIN 4 -----------
def conectar_bd():
    try:
        conexion = psycopg2.connect(
            host="localhost",           
            database="database_umap",        
            user="postgres",            
            password="umap"    
        )
        print("✅ Conexión exitosa a PostgreSQL")
        return conexion

    except Error as e:
        messagebox.showerror("❌ Error de conexión", f"No se pudo conectar a la base de datos.\n\n{e}")
        return None