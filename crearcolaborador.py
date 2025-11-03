import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
from PIL import Image, ImageTk
import psycopg2
import os
import shutil
from datetime import date

# ---------------- CONFIGURACIÓN BASE DE DATOS ----------------
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

UPLOADS_DIR = "uploads"
CONTRACT_TYPES = ["Permanente", "Especial", "Jornal"]
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ---------------- FUNCIONES AUXILIARES ----------------
def conectar_bd():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        messagebox.showerror("Error BD", f"No se pudo conectar a la base de datos:\n{e}")
        return None

def init_db():
    conn = conectar_bd()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS empleados (
                id SERIAL PRIMARY KEY,
                identidad TEXT,
                nombre1 TEXT,
                nombre2 TEXT,
                apellido1 TEXT,
                apellido2 TEXT,
                telefono TEXT,
                profesion TEXT,
                tipo_contrato TEXT,
                direccion TEXT,
                dependencia TEXT,
                cargo TEXT,
                usuario TEXT,
                contrasena TEXT,
                rol TEXT,
                unidad TEXT,
                cv_path TEXT,
                fecha_inicio DATE,
                fecha_finalizacion DATE,
                contrato_path TEXT,
                solvencia_path TEXT,
                id_path TEXT,
                foto_path TEXT,
                sueldo REAL,
                anioss TEXT,
                diasg TEXT,
                fecha_nacimiento DATE
            )
        """)
        conn.commit()
    except Exception as e:
        messagebox.showerror("Error BD", f"No se pudo inicializar la tabla de empleados:\n{e}")
    finally:
        conn.close()

def copy_file_to_uploads(src_path, prefix):
    if not src_path or not os.path.isfile(src_path):
        return None
    filename = os.path.basename(src_path)
    name = f"{prefix}_{date.today().isoformat()}_{filename}"
    dest = os.path.join(UPLOADS_DIR, name)
    shutil.copy2(src_path, dest)
    return dest

# ---------------- VENTANA CREAR COLABORADOR ----------------
class CrearColaborador(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.usuario_actual = usuario_actual
        self.title("UMAP - Crear Colaborador")
        self.geometry("900x700")
        self.configure(bg="#ecf0f1")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.centrar_ventana()

        # --- Variables ---
        self.vars = {}
        for v in ["identidad","nombre1","nombre2","apellido1","apellido2","telefono","profesion",
                  "tipo_contrato","direccion","dependencia","cargo","usuario","contrasena",
                  "rol","unidad","sueldo","anioss","diasg"]:
            self.vars[v] = tk.StringVar()
        self.fecha_inicio = tk.StringVar()
        self.fecha_fin = tk.StringVar()
        self.fecha_nac = tk.StringVar()

        self.cv_src = self.contrato_src = self.solvencia_src = self.id_src = self.foto_src = None

        # --- Frame principal ---
        self.frame = tk.Frame(self, bg="#ffffff", bd=2, relief="flat")
        self.frame.pack(padx=20, pady=20, fill="both", expand=True)

        # --- Título ---
        tk.Label(self.frame, text="Registrar Nuevo Colaborador", font=("Segoe UI", 16, "bold"),
                 bg="#ffffff", fg="#2c3e50").pack(pady=(10,20))

        # --- Scrollable Canvas ---
        canvas = tk.Canvas(self.frame, bg="#ffffff", highlightthickness=0)
        scroll_y = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        self.inner_frame = tk.Frame(canvas, bg="#ffffff")

        self.inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0,0), window=self.inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # --- Campos principales ---
        row = 0
        # Identidad
        tk.Label(self.inner_frame, text="Identidad:", bg="#ffffff").grid(row=row, column=0, sticky="w", padx=5, pady=3)
        tk.Entry(self.inner_frame, textvariable=self.vars["identidad"]).grid(row=row, column=1, sticky="ew", padx=5, pady=3)
        row += 1
        # Nombres
        tk.Label(self.inner_frame, text="Primer Nombre:", bg="#ffffff").grid(row=row, column=0, sticky="w", padx=5, pady=3)
        tk.Entry(self.inner_frame, textvariable=self.vars["nombre1"]).grid(row=row, column=1, sticky="ew", padx=5, pady=3)
        tk.Label(self.inner_frame, text="Segundo Nombre:", bg="#ffffff").grid(row=row, column=2, sticky="w", padx=5, pady=3)
        tk.Entry(self.inner_frame, textvariable=self.vars["nombre2"]).grid(row=row, column=3, sticky="ew", padx=5, pady=3)
        row += 1
        # Apellidos
        tk.Label(self.inner_frame, text="Primer Apellido:", bg="#ffffff").grid(row=row, column=0, sticky="w", padx=5, pady=3)
        tk.Entry(self.inner_frame, textvariable=self.vars["apellido1"]).grid(row=row, column=1, sticky="ew", padx=5, pady=3)
        tk.Label(self.inner_frame, text="Segundo Apellido:", bg="#ffffff").grid(row=row, column=2, sticky="w", padx=5, pady=3)
        tk.Entry(self.inner_frame, textvariable=self.vars["apellido2"]).grid(row=row, column=3, sticky="ew", padx=5, pady=3)
        row += 1
        # Teléfono y Profesión
        tk.Label(self.inner_frame, text="Teléfono:", bg="#ffffff").grid(row=row, column=0, sticky="w", padx=5, pady=3)
        tk.Entry(self.inner_frame, textvariable=self.vars["telefono"]).grid(row=row, column=1, sticky="ew", padx=5, pady=3)
        tk.Label(self.inner_frame, text="Profesión:", bg="#ffffff").grid(row=row, column=2, sticky="w", padx=5, pady=3)
        tk.Entry(self.inner_frame, textvariable=self.vars["profesion"]).grid(row=row, column=3, sticky="ew", padx=5, pady=3)
        row += 1
        # Dirección
        tk.Label(self.inner_frame, text="Dirección:", bg="#ffffff").grid(row=row, column=0, sticky="w", padx=5, pady=3)
        tk.Entry(self.inner_frame, textvariable=self.vars["direccion"], width=50).grid(row=row, column=1, columnspan=3, sticky="ew", padx=5, pady=3)
        row +=1
        # Tipo Contrato
        tk.Label(self.inner_frame, text="Tipo de Contrato:", bg="#ffffff").grid(row=row, column=0, sticky="w", padx=5, pady=3)
        ttk.Combobox(self.inner_frame, values=CONTRACT_TYPES, textvariable=self.vars["tipo_contrato"], state="readonly").grid(row=row, column=1, sticky="w", padx=5, pady=3)
        row += 1
        # Fechas
        tk.Label(self.inner_frame, text="Fecha Inicio:", bg="#ffffff").grid(row=row, column=0, sticky="w", padx=5, pady=3)
        DateEntry(self.inner_frame, textvariable=self.fecha_inicio, date_pattern="yyyy-mm-dd").grid(row=row, column=1, sticky="w", padx=5, pady=3)
        tk.Label(self.inner_frame, text="Fecha Finalización:", bg="#ffffff").grid(row=row, column=2, sticky="w", padx=5, pady=3)
        DateEntry(self.inner_frame, textvariable=self.fecha_fin, date_pattern="yyyy-mm-dd").grid(row=row, column=3, sticky="w", padx=5, pady=3)
        row += 1
        # Fecha nacimiento
        tk.Label(self.inner_frame, text="Fecha Nacimiento:", bg="#ffffff").grid(row=row, column=0, sticky="w", padx=5, pady=3)
        DateEntry(self.inner_frame, textvariable=self.fecha_nac, date_pattern="yyyy-mm-dd").grid(row=row, column=1, sticky="w", padx=5, pady=3)
        row += 1
        # Usuario y contraseña
        tk.Label(self.inner_frame, text="Usuario:", bg="#ffffff").grid(row=row, column=0, sticky="w", padx=5, pady=3)
        tk.Entry(self.inner_frame, textvariable=self.vars["usuario"]).grid(row=row, column=1, sticky="w", padx=5, pady=3)
        tk.Label(self.inner_frame, text="Contraseña:", bg="#ffffff").grid(row=row, column=2, sticky="w", padx=5, pady=3)
        tk.Entry(self.inner_frame, textvariable=self.vars["contrasena"], show="*").grid(row=row, column=3, sticky="w", padx=5, pady=3)
        row += 1
        # Sueldo
        tk.Label(self.inner_frame, text="Sueldo:", bg="#ffffff").grid(row=row, column=0, sticky="w", padx=5, pady=3)
        tk.Entry(self.inner_frame, textvariable=self.vars["sueldo"]).grid(row=row, column=1, sticky="w", padx=5, pady=3)
        row +=1
        # Botones principales
        btn_frame = tk.Frame(self.inner_frame, bg="#ffffff")
        btn_frame.grid(row=row, column=0, columnspan=4, pady=20, sticky="ew")
        tk.Button(btn_frame, text="💾 Guardar", bg="#1abc9c", fg="white", command=self.guardar).pack(side="left", expand=True, fill="x", padx=5)
        tk.Button(btn_frame, text="🧹 Limpiar", bg="#3498db", fg="white", command=self.limpiar).pack(side="left", expand=True, fill="x", padx=5)
        tk.Button(btn_frame, text="❌ Cerrar", bg="#e74c3c", fg="white", command=self.destroy).pack(side="left", expand=True, fill="x", padx=5)

        init_db()

    # --- FUNCIONES AUXILIARES ---
    def centrar_ventana(self):
        self.update_idletasks()
        w = 800
        h = 600
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws//2) - (w//2)
        y = (hs//2) - (h//2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def limpiar(self):
        for v in self.vars.values():
            v.set("")
        self.fecha_inicio.set("")
        self.fecha_fin.set("")
        self.fecha_nac.set("")
        self.cv_src = self.contrato_src = self.solvencia_src = self.id_src = self.foto_src = None

    def guardar(self):
        # Aquí iría la lógica de guardado completa, similar al guardar_empleado de tu ejemplo
        messagebox.showinfo("Guardar", "Aquí se guardaría el empleado en la base de datos.")

# ---------------- EJEMPLO DE USO ----------------
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x200")
    root.title("Main Simulado")

    def abrir_colab():
        CrearColaborador(root)

    ttk.Button(root, text="Agregar Colaborador", command=abrir_colab).pack(pady=50)
    root.mainloop()