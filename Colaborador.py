import os
import shutil
import sys
import psycopg2
from psycopg2 import Error
from datetime import date
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
from PIL import Image, ImageTk
from cargo import VentanaCargo  # importa la clase de cargo.py

# ------ CONFIGURACIÓN BASE DE DATOS -----
DB_CONFIG = {
    "host": "localhost",
    "database": "database_umap",
    "user": "postgres",
    "password": "umap",
    "port": "5432"
}

UPLOADS_DIR = "uploads"
CONTRACT_TYPES = ["Permanente", "Especial", "Jornal"]

# ---------- NUEVAS FUNCIONES PARA CARGAR LISTAS DESDE LA BD ----------
def obtener_lista(tabla):
    """Obtiene los nombres desde la tabla especificada."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(f"SELECT nombre FROM {tabla} ORDER BY nombre;")
        resultados = cur.fetchall()
        lista = [fila[0] for fila in resultados]
        cur.close()
        conn.close()
        return lista if lista else ["Sin datos"]
    except Exception as e:
        print(f"Error al obtener datos de {tabla}: {e}")
        return ["Sin datos"]

DEPENDENCIAS = obtener_lista("dependencias")
CARGOS = obtener_lista("cargos")

# ------------------------------------------------------

os.makedirs(UPLOADS_DIR, exist_ok=True)

# --- Conexión a la BD ---
def conectar_bd():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Error as e:
        messagebox.showerror("Error", f"No se pudo conectar a la base de datos:\n{e}")
        return None

# --- Inicializar tabla si no existe ---
def init_db():
    conn = conectar_bd()
    if conn is None:
        return
    c = conn.cursor()
    c.execute("""
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
    conn.close()

# --- Copiar archivos ---
def copy_file_to_uploads(src_path, prefix):
    if not src_path or not os.path.isfile(src_path):
        return None
    filename = os.path.basename(src_path)
    name = f"{prefix}_{date.today().isoformat()}_{filename}"
    dest = os.path.join(UPLOADS_DIR, name)
    shutil.copy2(src_path, dest)
    return dest

# --- Guardar empleado ---
def guardar_empleado(*args):
    (
        identidad, nombre1, nombre2, apellido1, apellido2, telefono, profesion,
        tipo_contrato, direccion, dependencia, cargo, usuario, contrasena, rol, unidad,
        cv_src, fecha_inicio, fecha_finalizacion, contrato_src, solvencia_src, id_src, foto_src,
        sueldo, anioss, diasg, fecha_nac
    ) = args

    if not identidad.strip():
        messagebox.showwarning("Validación", "La identidad es obligatoria.")
        return
    if not nombre1.strip() or not apellido1.strip():
        messagebox.showwarning("Validación", "Ingrese al menos primer nombre y primer apellido.")
        return
    if not usuario.strip() or not contrasena.strip():
        messagebox.showwarning("Validación", "Usuario y contraseña son obligatorios.")
        return

    try:
        sueldo_val = float(sueldo) if sueldo.strip() else 0.0
    except ValueError:
        messagebox.showwarning("Validación", "El sueldo debe ser un número válido.")
        return

    fi, ff = fecha_inicio, fecha_finalizacion
    if ff and fi > ff:
        messagebox.showwarning("Validación", "La fecha final no puede ser anterior a la inicial.")
        return

    cv_path = copy_file_to_uploads(cv_src, "CV") if cv_src else None
    contrato_path = copy_file_to_uploads(contrato_src, "CONTRATO") if contrato_src else None
    solvencia_path = copy_file_to_uploads(solvencia_src, "SOLVENCIA") if solvencia_src else None
    id_path = copy_file_to_uploads(id_src, "IDENTIDAD") if id_src else None
    foto_path = copy_file_to_uploads(foto_src, "FOTO") if foto_src else None

    conn = conectar_bd()
    if conn is None:
        return
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO empleados (
                identidad, nombre1, nombre2, apellido1, apellido2,
                telefono, profesion, tipo_contrato, direccion, dependencia,
                cargo, usuario, contrasena, rol, unidad, cv_path, fecha_inicio, fecha_finalizacion, contrato_path,
                solvencia_path, id_path, foto_path, sueldo, anioss, diasg, fecha_nacimiento
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            identidad.strip(), nombre1.strip(), nombre2.strip(), apellido1.strip(), apellido2.strip(),
            telefono.strip(), profesion.strip(), tipo_contrato.strip(), direccion.strip(), dependencia.strip(),
            cargo.strip(), usuario.strip(), contrasena.strip(), rol.strip(), unidad.strip(), cv_path, fi.isoformat(), ff.isoformat() if ff else None, contrato_path,
            solvencia_path, id_path, foto_path, sueldo_val, anioss.strip(), diasg.strip(), fecha_nac.isoformat() if fecha_nac else None
        ))
        conn.commit()
        messagebox.showinfo("Éxito", "Empleado guardado correctamente.")
    except Error as e:
        conn.rollback()
        messagebox.showerror("Error", f"No se pudo guardar el empleado:\n{e}")
    finally:
        conn.close()


# === INTERFAZ MODERNA ===
class App:
    def __init__(self, root, usuario_actual=None):
        self.root = root
        self.usuario_actual = usuario_actual
        root.title("UMAP - Crear Empleado")
        root.state("zoomed")
        root.configure(bg="#f4f6f9")
        root.update_idletasks()  # --- evita pantalla en blanco al iniciar ---

        # --- Colores y estilos modernos ---
        self.BG = "#f4f6f9"
        self.FRAME_BG = "#ffffff"
        self.LABEL_BG = "#f4f6f9"
        self.LABEL_FG = "#2c3e50"
        self.ENTRY_BG = "#ecf0f1"
        self.BUTTON_BG = "#3498db"
        self.BUTTON_FG = "white"

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background=self.LABEL_BG, foreground=self.LABEL_FG, font=("Segoe UI", 9))
        style.configure("TFrame", background=self.BG)
        style.configure("TLabelFrame", background=self.FRAME_BG, foreground=self.LABEL_FG, font=("Segoe UI", 10, "bold"))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=4)
        style.map("TButton", background=[("active", "#2980b9")], foreground=[("active", "white")])
        style.configure("TEntry", padding=2)
        style.configure("TCombobox", padding=2)

        # Variables
        self.identidad = tk.StringVar()
        self.nombre1 = tk.StringVar()
        self.nombre2 = tk.StringVar()
        self.apellido1 = tk.StringVar()
        self.apellido2 = tk.StringVar()
        self.profesion = tk.StringVar()
        self.telefono = tk.StringVar()
        self.direccion = tk.StringVar()
        self.dependencia = tk.StringVar(value=DEPENDENCIAS[0])
        self.cargo = tk.StringVar(value=CARGOS[0])
        self.tipo_contrato = tk.StringVar(value=CONTRACT_TYPES[0])
        self.usuario = tk.StringVar()
        self.contrasena = tk.StringVar()
        self.contrasena2 = tk.StringVar()
        self.rol = tk.StringVar()
        self.unidad = tk.StringVar()
        self.sueldo = tk.StringVar()
        self.anioss = tk.StringVar()
        self.diasg = tk.StringVar()
        self.fecha_nacimiento = tk.StringVar()

        self.cv_src = self.contrato_src = self.solvencia_src = self.id_src = self.foto_src = None
        self.foto_path = None

        # --- Título centrado ---
        ttk.Label(root, text="Registro de Nuevo Empleado", font=("Segoe UI", 14, "bold"), background=self.BG).pack(pady=10)

        container = ttk.Frame(root, padding=10, style="TFrame")
        container.pack(fill="both", expand=True)

        # --- Datos Personales ---
        datos = ttk.LabelFrame(container, text="Datos Personales", padding=10, style="TLabelFrame")
        datos.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

        # Foto
        self.foto_frame = tk.Frame(datos, width=150, height=150, bg="#ecf0f1", relief="ridge", bd=2)
        self.foto_frame.grid(row=0, column=0, rowspan=5, padx=5, pady=5)
        self.foto_frame.grid_propagate(False)
        self.foto_label = tk.Label(self.foto_frame, text="📷 Seleccionar Foto", bg="#ecf0f1", fg="gray")
        self.foto_label.place(relx=0.5, rely=0.5, anchor="center")
        self.foto_label.bind("<Button-1>", self.seleccionar_foto)
        self.foto_frame.bind("<Button-1>", self.seleccionar_foto)

        # --- Dependencias y cargos con datos desde BD ---
        contrato = ttk.LabelFrame(container, text="Información del Contrato", padding=10, style="TLabelFrame")
        contrato.grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        
        ttk.Label(contrato, text="Tipo de Contrato").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        tipo_cb = ttk.Combobox(contrato, values=CONTRACT_TYPES, textvariable=self.tipo_contrato, width=20, state="readonly")
        tipo_cb.grid(row=0, column=1, sticky="w", padx=5, pady=3)
        tipo_cb.bind("<<ComboboxSelected>>", self.tipo_cambio)

        ttk.Label(contrato, text="Dependencia").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        ttk.Combobox(contrato, values=DEPENDENCIAS, textvariable=self.dependencia, width=20, state="readonly").grid(row=1, column=1, sticky="w", padx=5, pady=3)

        ttk.Label(contrato, text="Cargo").grid(row=1, column=2, sticky="w", padx=5, pady=3)
        ttk.Combobox(contrato, values=CARGOS, textvariable=self.cargo, width=20, state="readonly").grid(row=1, column=3, sticky="w", padx=5, pady=3)

        init_db()  # asegúrate de crear tabla empleados al iniciar

    # --- Funciones de interfaz ---
    def seleccionar_foto(self, event=None):
        path = filedialog.askopenfilename(filetypes=[("Imagen", "*.png *.jpg *.jpeg")])
        if path:
            self.foto_src = path
            img = Image.open(path)
            img = img.resize((150, 150))
            self.foto_img = ImageTk.PhotoImage(img)
            self.foto_label.configure(image=self.foto_img, text="")

    def select_cv(self): self.cv_src = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
    def select_contrato(self): self.contrato_src = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
    def select_solvencia(self): self.solvencia_src = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
    def select_identidad(self): self.id_src = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])

    def validar_pass(self, *args):
        if self.contrasena2.get() != self.contrasena.get():
            self.pass_error.configure(text="Las contraseñas no coinciden")
        else:
            self.pass_error.configure(text="")

    def tipo_cambio(self, event=None):
        if self.tipo_contrato.get() == "Jornal":
            self.anios_entry.configure(state="disabled")
            self.dias_entry.configure(state="disabled")
        else:
            self.anios_entry.configure(state="normal")
            self.dias_entry.configure(state="normal")

    def actualizar_dias(self, event=None):
        pass

    def limpiar(self):
        for var in [self.identidad, self.nombre1, self.nombre2, self.apellido1, self.apellido2,
                    self.telefono, self.profesion, self.direccion, self.usuario, self.contrasena, self.contrasena2,
                    self.sueldo, self.anioss, self.diasg, self.tipo_contrato, self.dependencia, self.cargo]:
            var.set("")
        self.foto_label.configure(image="", text="📷 Seleccionar Foto")
        self.cv_src = self.contrato_src = self.solvencia_src = self.id_src = self.foto_src = None

    def cancelar(self):
        self.root.destroy()
        import Main
        os.execl(sys.executable, sys.executable, "Main.py")

    def guardar(self):
        guardar_empleado(
            self.identidad.get(), self.nombre1.get(), self.nombre2.get(),
            self.apellido1.get(), self.apellido2.get(), self.telefono.get(), self.profesion.get(),
            self.tipo_contrato.get(), self.direccion.get(), self.dependencia.get(), self.cargo.get(),
            self.usuario.get(), self.contrasena.get(), self.rol.get(), self.unidad.get(),
            self.cv_src, self.fecha_inicio.get_date(), self.fecha_fin.get_date(),
            self.contrato_src, self.solvencia_src, self.id_src, self.foto_src,
            self.sueldo.get(), self.anioss.get(), self.diasg.get(), self.fecha_nac_entry.get_date()
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()