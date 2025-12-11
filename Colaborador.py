import os
import shutil
import re
import psycopg2
import psycopg2.extras
from psycopg2 import Error
from datetime import date
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from Main import PantallaPrincipal
from tkcalendar import DateEntry
from PIL import Image, ImageTk
from datetime import datetime, timedelta
import tkinter.messagebox as messagebox
import webbrowser      # para abrir archivos
import platform        # para detectar el SO y abrir archivos localmente
import shutil          # para copiar/descargar archivos
import re

# ------ CONFIGURACIÓN BASE DE DATOS -----
DB_CONFIG = {
    "host": "localhost",
    "database": "database_umap",
    "user": "postgres",
    "password": "umap",
    "port": "5432"
}

UPLOADS_DIR = "uploads"

def cargar_lista(tabla):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        c = conn.cursor()
        c.execute(f"SELECT nombre FROM {tabla}")
        resultados = [row[0] for row in c.fetchall()]
        return resultados if resultados else ["-"]
    except Error as e:
        messagebox.showerror("Error BD", f"No se pudo cargar {tabla}:\n{e}")
        return ["-"]
    finally:
        if conn:
            conn.close()

# Cargar tipos de contrato desde la tabla 'contratos' (fallback si no hay datos)
_try_contracts = cargar_lista("contratos")
if _try_contracts and _try_contracts != ["-"]:
    CONTRACT_TYPES = _try_contracts
else:
    CONTRACT_TYPES = ["Permanente", "Especial", "Jornal"]

# Cargar dependencias y cargos (se hace después de definir cargar_lista)
DEPENDENCIAS = cargar_lista("dependencias")
CARGOS = cargar_lista("cargos")

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
        CREATE TABLE IF NOT EXISTS colaborador (
            id SERIAL PRIMARY KEY,
            foto_path TEXT,
            tipo_contrato TEXT,
            identidad TEXT,
            fecha_nacimiento DATE,
            nombre1 TEXT,
            nombre2 TEXT,
            apellido1 TEXT,
            apellido2 TEXT,
            telefono TEXT,
            profesion TEXT,
            direccion TEXT,
            dependencia TEXT,
            cargo TEXT,
            fecha_inicio DATE,
            fecha_finalizacion DATE,
            sueldo REAL,
            diasg TEXT,
            anioss TEXT,
            usuario TEXT,
            contrasena TEXT,
            confirmacion_contrasena TEXT,
            rol TEXT,
            unidad TEXT,
            cv_path TEXT,
            contrato_path TEXT,
            id_path TEXT,
            solvencia_path TEXT
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

def guardar_empleado(
    identidad, nombre1, nombre2, apellido1, apellido2, telefono, profesion,
    tipo_contrato, direccion, dependencia, cargo,
    usuario, contrasena, confirmacion_contrasena, rol, unidad,
    cv_src, fecha_inicio, fecha_finalizacion, contrato_src,
    solvencia_src, id_src, foto_src,
    sueldo, anioss, diasg, fecha_nac
):
    """
    Guarda un colaborador usando columnas que existen en la tabla 'colaborador'.
    Orden de parámetros diseñado para coincidir con la llamada en App.guardar().
    """
    # validaciones básicas
    if not identidad.strip():
        messagebox.showwarning("Validación", "La identidad es obligatoria.")
        return
    if not nombre1.strip() or not apellido1.strip():
        messagebox.showwarning("Validación", "Ingrese al menos primer nombre y primer apellido.")
        return
    # si contrato es permanente, usuario y contraseña son obligatorios
    if tipo_contrato == "Permanente" and (not usuario.strip() or not contrasena.strip()):
        messagebox.showwarning("Validación", "Usuario y contraseña son obligatorios para contratos permanentes.")
        return

    try:
        sueldo_val = float(sueldo) if str(sueldo).strip() else 0.0
    except ValueError:
        messagebox.showwarning("Validación", "El sueldo debe ser un número válido.")
        return

    fi, ff = fecha_inicio, fecha_finalizacion
    if ff and fi and fi > ff:
        messagebox.showwarning("Validación", "La fecha final no puede ser anterior a la inicial.")
        return

    # copiar adjuntos
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
        # Insertar usando las columnas que realmente existen en la tabla creada
        c.execute("""
            INSERT INTO colaborador (
                foto_path, tipo_contrato, identidad, fecha_nacimiento,
                nombre1, nombre2, apellido1, apellido2,
                telefono, profesion, direccion, dependencia, cargo,
                fecha_inicio, fecha_finalizacion, sueldo, diasg, anioss,
                usuario, contrasena, confirmacion_contrasena, rol, unidad,
                cv_path, contrato_path, id_path, solvencia_path
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """, (
            foto_path, tipo_contrato, identidad.strip(), fecha_nac.isoformat() if fecha_nac else None,
            nombre1.strip(), nombre2.strip(), apellido1.strip(), apellido2.strip(),
            telefono.strip(), profesion.strip(), direccion.strip(), dependencia.strip(), cargo.strip(),
            fi.isoformat() if fi else None, ff.isoformat() if ff else None, sueldo_val, diasg.strip(), anioss.strip(),
            usuario.strip(), contrasena.strip(), confirmacion_contrasena.strip(), rol.strip() if rol else None, unidad.strip(),
            cv_path, contrato_path, id_path, solvencia_path
        ))
        conn.commit()
        messagebox.showinfo("Éxito", "Empleado guardado correctamente.")
    except Error as e:
        conn.rollback()
        messagebox.showerror("Error", f"No se pudo guardar el empleado:\n{e}")
    finally:
        conn.close()

# --- INTERFAZ ---
class App:
    def __init__(self, root, usuario_actual=None):
        style = ttk.Style()
        style.theme_use("clam")

        # Estilos generales
        style.configure("TLabel", font=("Segoe UI", 11))
        style.configure("TEntry", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 11), padding=6)

        # Botones "folder" / generales de documentos: gris inicial
        style.configure(
            "Folder.TButton",
            font=("Segoe UI", 11),
            padding=8,
            foreground="black",
            background="#757575"  # gris
        )
        style.map(
            "Folder.TButton",
            foreground=[('active', 'black')],
            background=[('active', '#a0a0a0'), ('!active', '#757575')]
        )

        # Botones de estado "success" (verde)
        style.configure(
            "Success.TButton",
            font=("Segoe UI", 12, "bold"),
            foreground="white",
            background="#4CAF50"
        )
        style.map(
            "Success.TButton",
            foreground=[('active', 'white')],
            background=[('active', '#45a049'), ('!active', '#4CAF50')]
        )
        self.root = root
        self.usuario_actual = usuario_actual
        root.title("UMAP - Crear Colaborador")
        root.state("zoomed")
        root.configure(bg="#f4f6f9")

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
        self.confirmacion_contrasena = tk.StringVar()  # <- AGREGAR ESTO
        self.rol = tk.StringVar()
        self.unidad = tk.StringVar()
        self.sueldo = tk.StringVar()
        self.anioss = tk.StringVar()
        self.diasg = tk.StringVar()
        self.meses_calc = tk.StringVar()
        self.total_days_calc = tk.StringVar()
        self.fecha_nacimiento = tk.StringVar()

        self.cv_src = self.contrato_src = self.solvencia_src = self.id_src = self.foto_src = None
        self.foto_path = None
    
        # Estilo general (ajustado: labels y entries más juntos)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", font=("Segoe UI", 9), padding=0)     # labels más pegados a los campos
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=4)
        style.configure("TEntry", padding=0)                           # entradas sin padding extra

        # estilos específicos
        style.configure(
            "DocGray.TButton",
            font=("Segoe UI", 12, "bold"),
            foreground="white",
            background="#757575",  # gris
            padding=(12, 10),
            relief="flat"
        )
        style.configure(
            "Main.Small.TButton",  # botones principales un poco más pequeños
            font=("Segoe UI", 10, "bold"),
            foreground="white",
            background="#b0b0b0",
            padding=(6, 6)
        )

        style.map(
            "Main.Small.TButton",
            foreground=[('active', 'white')],
            background=[('active', '#1976D2'), ('!active', '#b0b0b0')]
        )

        style.configure("Success.TButton", font=("Segoe UI", 12, "bold"), foreground="white")
        style.map("Success.TButton",
                  foreground=[('active', 'white')],
                  background=[('active', '#45a049'), ('!active', '#4CAF50')])

        # Título centrado
        ttk.Label(root, text="Registro de Nuevo Colaborador", font=("Segoe UI", 14, "bold"), background="#f4f6f9").pack(pady=10)

        container = ttk.Frame(root, padding=10)
        container.pack(fill="both", expand=True)
        container.grid_columnconfigure(0, weight=1)

        # --- Datos Personales ---
        datos = ttk.LabelFrame(container, text="Datos Personales", padding=5)
        datos.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        for i in range(5):
            datos.grid_rowconfigure(i, weight=1)
        for j in range(5):
            datos.grid_columnconfigure(j, weight=1)

        # --- Foto ---
        self.foto_frame = tk.Frame(datos, width=5, height=150, bg="#e0e0e0", relief="ridge", bd=2)
        self.foto_frame.grid(row=0, column=0, rowspan=5, padx=5, pady=5, sticky="nsew")
        self.foto_frame.grid_propagate(False)

        self.foto_label = tk.Label(self.foto_frame, text="📷 Seleccionar Foto", bg="#e0e0e0", fg="gray")
        self.foto_label.place(relx=0.5, rely=0.5, anchor="center")

        self.foto_label.bind("<Button-1>", self.seleccionar_foto)
        self.foto_frame.bind("<Button-1>", self.seleccionar_foto)

        # Tipo contrato
        ttk.Label(datos, text="Tipo de Contrato").grid(row=0, column=1, sticky="ew", padx=5, pady=3)
        tipo_cb = ttk.Combobox(datos, values=CONTRACT_TYPES, textvariable=self.tipo_contrato, width=20, state="readonly")
        tipo_cb.grid(row=0, column=2, sticky="ew", padx=(5,30), pady=3)
        tipo_cb.bind("<<ComboboxSelected>>", self.tipo_cambio)

        # Identidad
        ttk.Label(datos, text="Identidad").grid(row=0, column=3, sticky="ew", padx=(0,5), pady=3)
        vcmd = (self.root.register(self.validar_identidad), '%P')
        self.identidad_entry = ttk.Entry(datos, textvariable=self.identidad, width=25,
                                         validate='key', validatecommand=vcmd)
        self.identidad_entry.grid(row=0, column=4, sticky="ew", padx=5, pady=3)
        self.identidad_entry.bind("<KeyRelease>", self.buscar_colaborador_por_identidad)

        # Fecha nacimiento
        ttk.Label(datos, text="Fecha Nacimiento").grid(row=1, column=1, sticky="ew", padx=5, pady=3)
        self.fecha_nac_entry = DateEntry(datos, date_pattern="yyyy-mm-dd", width=12)
        self.fecha_nac_entry.grid(row=1, column=2, sticky="ew", padx=5, pady=3)

        # Nombres y apellidos (validación: solo letras y espacios)
        ttk.Label(datos, text="Primer Nombre*").grid(row=1, column=3, sticky="ew", padx=(6,3), pady=3)
        name_vcmd = (self.root.register(self.validar_nombre), '%P')
        ttk.Entry(datos, textvariable=self.nombre1, width=20,
                  validate='key', validatecommand=name_vcmd).grid(row=1, column=4, sticky="ew", padx=(3,6), pady=3)
        ttk.Label(datos, text="Segundo Nombre").grid(row=2, column=1, sticky="ew", padx=(6,3), pady=3)
        ttk.Entry(datos, textvariable=self.nombre2, width=20).grid(row=2,column=2, sticky="ew", padx=(3,6), pady=3)

        ttk.Label(datos, text="Primer Apellido*").grid(row=2, column=3, sticky="ew", padx=(6,3), pady=3)
        surname_vcmd = (self.root.register(self.validar_nombre), '%P')
        ttk.Entry(datos, textvariable=self.apellido1, width=20,
                  validate='key', validatecommand=surname_vcmd).grid(row=2, column=4, sticky="ew", padx=(3,6), pady=3)
        ttk.Label(datos, text="Segundo Apellido").grid(row=3, column=1, sticky="ew", padx=5, pady=3)
        ttk.Entry(datos, textvariable=self.apellido2, width=20).grid(row=3, column=2, sticky="ew", padx=5, pady=3)

        # Teléfono y Profesión
        ttk.Label(datos, text="Teléfono").grid(row=3, column=3, sticky="ew", padx=5, pady=3)
        # validar teléfono: formato 9876-1534 o 9876 1534
        tel_vcmd = (self.root.register(self.validar_telefono), '%P')
        self.telefono_entry = ttk.Entry(datos, textvariable=self.telefono, width=20,
                                        validate='key', validatecommand=tel_vcmd)
        self.telefono_entry.grid(row=3, column=4, sticky="ew", padx=5, pady=3)
        
        ttk.Label(datos, text="Profesión").grid(row=4, column=1, sticky="ew", padx=5, pady=3)
        self.profesion_entry = ttk.Entry(datos, textvariable=self.profesion, width=25)
        self.profesion_entry.grid(row=4, column=2, sticky="ew", padx=5, pady=3, ipady=4)

        # Dirección
        ttk.Label(datos, text="Dirección").grid(row=4, column=3, sticky="ew", padx=5, pady=3)
        ttk.Entry(datos, textvariable=self.direccion, width=20).grid(row=4, column=4, sticky="ew", padx=5, pady=3)

        # --- Información del contrato ---
        contrato = ttk.LabelFrame(container, text="Información del Contrato", padding=5)
        contrato.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        for i in range(5):
            contrato.grid_rowconfigure(i, weight=1)
        for j in range(4):
            contrato.grid_columnconfigure(j, weight=1)

        ttk.Label(contrato, text="Dependencia").grid(row=1, column=0, sticky="ew", padx=5, pady=3)
        self.dependencia_cb = ttk.Combobox(contrato, values=DEPENDENCIAS, textvariable=self.dependencia, width=20, state="readonly")
        self.dependencia_cb.grid(row=1, column=1, sticky="ew", padx=5, pady=3)

        ttk.Label(contrato, text="Cargo").grid(row=1, column=2, sticky="ew", padx=5, pady=3)
        self.cargo_cb = ttk.Combobox(contrato, values=CARGOS, textvariable=self.cargo, width=20, state="readonly")
        self.cargo_cb.grid(row=1, column=3, sticky="ew", padx=5, pady=3)

        ttk.Label(contrato, text="Fecha Inicio").grid(row=2, column=0, sticky="ew", padx=5, pady=3)
        self.fecha_inicio = DateEntry(contrato, date_pattern="yyyy-mm-dd", width=12)
        self.fecha_inicio.grid(row=2, column=1, sticky="ew", padx=5, pady=3)

        ttk.Label(contrato, text="Fecha Finalización").grid(row=2, column=2, sticky="ew", padx=5, pady=3)
        self.fecha_fin = DateEntry(contrato, date_pattern="yyyy-mm-dd", width=12)
        self.fecha_fin.grid(row=2, column=3, sticky="ew", padx=5, pady=3)
        self.fecha_inicio.bind("<<DateEntrySelected>>", self.actualizar_dias)
        self.fecha_fin.bind("<<DateEntrySelected>>", self.actualizar_dias)

        ttk.Label(contrato, text="Sueldo (Lps)").grid(row=3, column=0, sticky="ew", padx=5, pady=3)
        ttk.Entry(contrato, textvariable=self.sueldo, width=15).grid(row=3, column=1, sticky="ew", padx=5, pady=3)

        ttk.Label(contrato, text="Años de Servicio").grid(row=3, column=2, sticky="ew", padx=5, pady=3)
        self.anios_entry = ttk.Entry(contrato, textvariable=self.anioss, width=15)
        self.anios_entry.grid(row=3, column=3, sticky="ew", padx=5, pady=3)

        ttk.Label(contrato, text="Días a Gozar").grid(row=4, column=0, sticky="ew", padx=5, pady=3)
        self.dias_entry = ttk.Entry(contrato, textvariable=self.diasg, width=15)
        self.dias_entry.grid(row=4, column=1, sticky="ew", padx=5, pady=3)

        # Campos calculados: Meses y Días totales (se actualizan en actualizar_dias)
        ttk.Label(contrato, text="Meses (calc.)").grid(row=4, column=2, sticky="ew", padx=5, pady=3)
        self.meses_entry = ttk.Entry(contrato, textvariable=self.meses_calc, width=18, state="readonly")
        self.meses_entry.grid(row=4, column=3, sticky="ew", padx=5, pady=3)

        ttk.Label(contrato, text="Días (totales)").grid(row=5, column=0, sticky="ew", padx=5, pady=3)
        self.totaldays_entry = ttk.Entry(contrato, textvariable=self.total_days_calc, width=18, state="readonly")
        self.totaldays_entry.grid(row=5, column=1, sticky="ew", padx=5, pady=3)

        # --- Cuenta de usuario ---
        usuario_frame = ttk.LabelFrame(container, text="Cuenta de Usuario", padding=5)
        usuario_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        for i in range(3):
             usuario_frame.grid_rowconfigure(i, weight=1)
        for j in range(4):
             usuario_frame.grid_columnconfigure(j, weight=1)

        ttk.Label(usuario_frame, text="Usuario").grid(row=1, column=0, sticky="ew", padx=5, pady=3)
        self.usuario_entry = ttk.Entry(usuario_frame, textvariable=self.usuario, width=30)
        self.usuario_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=3)

        ttk.Label(usuario_frame, text="Contraseña").grid(row=2, column=0, sticky="ew", padx=5, pady=3)
        self.pass_entry = ttk.Entry(usuario_frame, textvariable=self.contrasena, show="*", width=30)
        self.pass_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=3)

        ttk.Label(usuario_frame, text="Confirmar Contraseña").grid(row=2, column=2, sticky="ew", padx=5, pady=3)
        self.pass2_entry = ttk.Entry(usuario_frame, textvariable=self.confirmacion_contrasena, show="*", width=30)
        self.pass2_entry.grid(row=2, column=3, sticky="ew", padx=5, pady=3)

        ttk.Label(usuario_frame, text="Rol").grid(row=4, column=0, sticky="ew", padx=5, pady=3)

        self.rol = tk.StringVar()  # variable para almacenar el valor seleccionado
        self.rol_combo = ttk.Combobox(
             usuario_frame,
             textvariable=self.rol,
             values=["Administrador", "Usuario"],
             state="readonly",  # evita que el usuario escriba texto libre
             width=18
        )
        self.rol_combo.grid(row=4, column=1, sticky="ew", padx=5, pady=3)
        self.rol_combo.set("Usuario")  # valor por defecto

        ttk.Label(usuario_frame, text="Observacion").grid(row=4, column=2, sticky="ew", padx=5, pady=3)
        ttk.Entry(usuario_frame, textvariable=self.unidad, width=20).grid(row=4, column=3, sticky="ew", padx=5, pady=3)

        self.pass_error = tk.Label(usuario_frame, text="", fg="red", font=("Segoe UI", 8))
        self.pass_error.grid(row=3, column=2, columnspan=1, sticky="ew", padx=5)

        # Asociar validación al StringVar correcto
        self.confirmacion_contrasena.trace_add("write", self.validar_pass)

        # --- Documentos y botones principales en la misma fila (docs a la izquierda, botones principales a la derecha apilados) ---
        bottom_row = ttk.Frame(container)
        bottom_row.grid(row=3, column=0, sticky="nsew", padx=10, pady=(6,0))
        bottom_row.grid_columnconfigure(0, weight=3)
        bottom_row.grid_columnconfigure(1, weight=0)

        # Estilo específico para botones de documento (más "alto" y con aspecto de tarjeta/documento)
        style.configure(
            "Doc.TButton",
            font=("Segoe UI", 12, "bold"),
            foreground="white",
            background="#2E7D32",
            padding=(12, 10),
            relief="flat"
        )

        # Left: LabelFrame de documentos (más ancho y suficiente altura para botones grandes)
        docs = ttk.LabelFrame(bottom_row, text="📁 Documentos Adjuntos", padding=8)
        docs.grid(row=0, column=0, sticky="nw", padx=(0,12), pady=0)

        # Aumentado ancho pero permitir que la altura se ajuste exactamente al contenido
        docs.configure(width=1250, height=260)
        docs.grid_propagate(False)  # mantener tamaño fijo; botón debe ajustarse dentro
        docs.configure(width=1250)   # ancho amplio; altura la define el contenido
        docs.grid_propagate(True)    # dejar que el frame ajuste su altura según los botones

        for c in range(4):
            docs.grid_columnconfigure(c, weight=1)
        docs.grid_rowconfigure(0, weight=1)

        # --- Botones de documentos ---
        self.btn_cv = ttk.Button(docs, text="CV\n(Adjuntar)", style="DocGray.TButton",
                                command=lambda: self.manejar_documento('cv'), compound="top")
        docs.grid_rowconfigure(0, weight=1)
        self.btn_cv.grid(row=0, column=0, padx=8, pady=8, ipadx=100, ipady=18)

        self.btn_contrato = ttk.Button(docs, text="Contrato\n(Adjuntar)", style="DocGray.TButton",
                                command=lambda: self.manejar_documento('contrato'), compound="top")
        docs.grid_rowconfigure(0, weight=1)
        self.btn_contrato.grid(row=0, column=1, padx=8, pady=8, ipadx=100, ipady=18)

        self.btn_id = ttk.Button(docs, text="Identidad\n(Adjuntar)", style="DocGray.TButton",
                                command=lambda: self.manejar_documento('id'), compound="top")
        docs.grid_rowconfigure(0, weight=1)
        self.btn_id.grid(row=0, column=2, padx=8, pady=8, ipadx=100, ipady=18)

        self.btn_solvencia = ttk.Button(docs, text="Solvencia\n(Adjuntar)", style="DocGray.TButton",
                                command=lambda: self.manejar_documento('solvencia'), compound="top")
        docs.grid_rowconfigure(0, weight=1)
        self.btn_solvencia.grid(row=0, column=3, padx=8, pady=8, ipadx=100, ipady=18)

        # Etiquetas de confirmación debajo de los botones (compactas)
        self.cv_ok = ttk.Label(docs, text="", foreground="green")
        self.contrato_ok = ttk.Label(docs, text="", foreground="green")
        self.id_ok = ttk.Label(docs, text="", foreground="green")
        self.solvencia_ok = ttk.Label(docs, text="", foreground="green")
        self.cv_ok.grid(row=1, column=0, pady=(4,0))
        self.contrato_ok.grid(row=1, column=1, pady=(4,0))
        self.id_ok.grid(row=1, column=2, pady=(4,0))
        self.solvencia_ok.grid(row=1, column=3, pady=(4,0))

        # Right: panel vertical con los 3 botones principales (apilados uno debajo de otro), compactos
        btns = ttk.Frame(bottom_row)
        btns.grid(row=0, column=1, sticky="n", padx=(0,6), pady=0)
        btns.grid_columnconfigure(0, weight=1)

        # Tamaño compacto para que quepan junto al LabelFrame ancho
        btn_width = 14
        btn_ipadx = 6
        btn_ipady = 6

        self.guardar_btn = ttk.Button(btns, text="💾 Crear", command=self.guardar, style="Main.Small.TButton", width=btn_width)
        self.guardar_btn.grid(row=0, column=0, padx=6, pady=(10,6), ipadx=btn_ipadx, ipady=btn_ipady, sticky="ew")

        self.limpiar_btn = ttk.Button(btns, text="🧹 Limpiar", command=self.limpiar, style="Main.Small.TButton", width=btn_width)
        self.limpiar_btn.grid(row=1, column=0, padx=6, pady=6, ipadx=btn_ipadx, ipady=btn_ipady, sticky="ew")

        self.regresar_btn = ttk.Button(btns, text="↩ Regresar", command=self.cancelar, style="Main.Small.TButton", width=btn_width)
        self.regresar_btn.grid(row=2, column=0, padx=6, pady=(6,10), ipadx=btn_ipadx, ipady=btn_ipady, sticky="ew")

        self.verificar_contratos()

        init_db()

    def verificar_contratos(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            hoy = datetime.now().date()
            limite = hoy + timedelta(days=7)

            # Buscar contratos próximos a vencer o vencidos
            cursor.execute("""
                           SELECT id, nombre1, apellido1, fecha_finalizacion, estado
                           FROM colaborador
                           WHERE fecha_finalizacion IS NOT NULL
            """)
                
            registros = cursor.fetchall()
                
            proximos = []
            vencidos = []
                
            for colab in registros:
                id_colab, nombre, apellido, fecha_final, estado = colab
                if fecha_final:
                    fecha_final = fecha_final if isinstance(fecha_final, datetime) else datetime.strptime(str(fecha_final), "%Y-%m-%d").date()
                    if hoy > fecha_final and estado != "Inactivo":
                        vencidos.append(f"{nombre} {apellido}")
                        cursor.execute("UPDATE colaborador SET estado='Inactivo' WHERE id_colaborador=%s", (id_colab,))
                    elif hoy <= fecha_final <= limite:
                        proximos.append(f"{nombre} {apellido} ({fecha_final})")
                        
            conn.commit()
                
            # Notificaciones visuales
            if proximos or vencidos:
                mensaje = ""
                if proximos:
                    mensaje += "📅 Contratos por vencer en menos de 7 días:\n" + "\n".join(proximos) + "\n\n"
                if vencidos:
                    mensaje += "⚠ Contratos vencidos (marcados como Inactivos):\n" + "\n".join(vencidos)
                    messagebox.showwarning("Aviso de Contratos", mensaje)
                    
            cursor.close()
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Error al verificar contratos", str(e))
    
    def mostrar_menu_documento(self, boton, path):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Abrir", command=lambda: self.abrir_archivo(path))
        menu.add_command(label="Descargar / Guardar como...", command=lambda: self.descargar_archivo(path))
        menu.add_command(label="Ver", command=lambda: self.abrir_archivo(path))  # ver = abrir
        # Mostrar el menú donde esté el botón
        x = boton.winfo_rootx()
        y = boton.winfo_rooty() + boton.winfo_height()
        menu.tk_popup(x, y)

    # --- Funciones de interfaz ---
    def buscar_colaborador_por_identidad(self, event=None):
        identidad = self.identidad.get().strip()
        if len(identidad) < 4:  # esperar un poco para evitar spam a la BD
            return
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT *
            FROM colaborador
            WHERE identidad LIKE %s
            LIMIT 1
        """, (identidad + "%",))
        row = cur.fetchone()
        conn.close()

        if row:
            # llenar campos
            self.nombre1.set(row["nombre1"])
            self.nombre2.set(row["nombre2"])
            self.apellido1.set(row["apellido1"])
            self.apellido2.set(row["apellido2"])
            self.telefono.set(row["telefono"])
            self.direccion.set(row["direccion"])
            self.profesion.set(row["profesion"])
            self.unidad.set(row["unidad"])
            self.sueldo.set(row["sueldo"])

            # combos
            self.dependencia.set(row["dependencia"]) if row["dependencia"] else None
            self.cargo.set(row["cargo"]) if row["cargo"] else None
            self.tipo_contrato.set(row["tipo_contrato"]) if row["tipo_contrato"] else None

            # fechas
            try:
                self.fecha_inicio.set_date(row["fecha_inicio"])
                self.fecha_fin.set_date(row["fecha_fin"])
                self.fecha_nac_entry.set_date(row["fecha_nacimiento"])
            except:
                pass

            # foto
            if row["foto"] and os.path.exists(row["foto"]):
                img = Image.open(row["foto"])
                img = img.resize((130,130))
                self.foto_img = ImageTk.PhotoImage(img)
                self.foto_label.configure(image=self.foto_img, text="")
                self.foto_label.image = self.foto_img

    def seleccionar_foto(self, event=None):
        path = filedialog.askopenfilename(filetypes=[("Imagen", "*.png *.jpg *.jpeg")])
        if path:
            self.foto_src = path
            img = Image.open(path)
            img = img.resize((130, 130))
            self.foto_img = ImageTk.PhotoImage(img)
            self.foto_label.configure(image=self.foto_img, text="")
            self.foto_label.image = self.foto_img  # corregir asignación correcta

            # animación visual breve al agregar foto: parpadeo suave del marco
            try:
                orig_bg = self.foto_frame.cget("bg")
                highlight = "#c8e6c9"  # verde muy claro
                self.foto_frame.configure(bg=highlight)
                self.foto_label.configure(bg=highlight)
                # restaurar después de 220 ms
                self.root.after(220, lambda: (self.foto_frame.configure(bg=orig_bg),
                                              self.foto_label.configure(bg=orig_bg)))
            except Exception:
                pass

    def select_cv(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path:  # aquí sí existe path
            self.cv_src = path
            self.marcar_ok(self.btn_cv, self.cv_ok)

    def select_contrato(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path:
            self.contrato_src = path
            self.marcar_ok(self.btn_contrato, self.contrato_ok)

    def select_identidad(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path:
            self.id_src = path
            self.marcar_ok(self.btn_id, self.id_ok)

    def select_solvencia(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path:
            self.solvencia_src = path
            self.marcar_ok(self.btn_solvencia, self.solvencia_ok)

    def validar_pass(self, *args):
        if self.confirmacion_contrasena.get() != self.contrasena.get():
            self.pass_error.configure(text="Las contraseñas no coinciden")
        else:
            self.pass_error.configure(text="")

    def validar_identidad(self, P):
        if P == "":
            return True
        # permitir escritura parcial (solo dígitos y guiones)
        if re.fullmatch(r'[\d\- ]*', P):
            return True
        return False
    
    def validar_telefono(self, P):
        if P == "":
            return True
        if len(P) > 9:
            return False
        # solo dígitos, espacio o guion permitidos mientras escribe
        if not re.match(r'^[0-9 \-]*$', P):
            return False
        # cuando ya tiene 9 caracteres, exigir formato estricto
        if len(P) == 9:
            return bool(re.match(r'^\d{4}[- ]\d{4}$', P))
        return True
    
    def validar_nombre(self, P):
        if P == "":
            return True
        # sólo letras y espacios
        return bool(re.match(r'^[A-Za-zÁÉÍÓÚÜáéíóúüÑñ ]*$', P))
    
    def normalizar_sueldo(self, valor):
        """
        Convierte un sueldo como 1,500 o 1.500,00 a decimal estándar para PostgreSQL
        """
        if not valor:
            return None

        # quitar espacios
        valor = valor.strip()

        # si usa coma como decimal: 1.500,00 -> 1500.00
        if "," in valor and "." in valor:
            valor = valor.replace(".", "").replace(",", ".")

        # si solo usa coma: 1500,50 -> 1500.50
        elif "," in valor:
            valor = valor.replace(",", ".")

        # quitar separadores de miles
        valor = valor.replace(",", "").replace(" ", "")

        try:
            return float(valor)
        except:
            messagebox.showwarning("Error de formato",
                                   "Formato de sueldo incorrecto.")
            return None

    def tipo_cambio(self, event=None):
        tipo = self.tipo_contrato.get()
        # controlar años/días del contrato
        if tipo in ("Especial", "Jornal"):
            self.anios_entry.configure(state="disabled")
            self.dias_entry.configure(state="disabled")
        else:
            self.anios_entry.configure(state="normal")
            self.dias_entry.configure(state="normal")

        # controlar campos de usuario: solo habilitados para "Permanente"
        if tipo == "Permanente":
            self.usuario_entry.configure(state="normal")
            self.pass_entry.configure(state="normal")
            self.pass2_entry.configure(state="normal")
            # rol_combo: readonly para selección, habilitar/deshabilitar mediante state
            self.rol_combo.configure(state="readonly")
        else:
            # deshabilitar y limpiar valores
            try:
                self.usuario_entry.configure(state="disabled")
                self.pass_entry.configure(state="disabled")
                self.pass2_entry.configure(state="disabled")
                self.rol_combo.configure(state="disabled")
            except Exception:
                pass
            self.usuario.set("")
            self.contrasena.set("")
            self.confirmacion_contrasena.set("")
            self.rol.set("Usuario")

    def actualizar_dias(self, event=None):
        pass
    def actualizar_dias(self, event=None):
        """
        Calcula y actualiza:
         - total_days_calc: días totales entre fecha_inicio y fecha_fin (calendarizados)
         - meses_calc: meses enteros = total_days // 30
         - anioss: años enteros = total_days // 365 (solo si tipo_contrato == 'Permanente')
        """
        try:
            fi = self.fecha_inicio.get_date()
            ff = self.fecha_finalizacion.get_date()  # si el widget se llama diferente colócame su nombre
        except Exception:
            self.anioss.set("")
            self.meses_calc.set("")
            self.total_days_calc.set("")
            return

        # validación básica de fechas
        if not fi or not ff or ff < fi:
            self.anioss.set("")
            self.meses_calc.set("")
            self.total_days_calc.set("")
            return

        # calcular días totales (calendarizados)
        total_days = (ff - fi).days
        self.total_days_calc.set(str(total_days))

        # meses y años como enteros (varchar en BD al guardar)
        months = total_days // 30 if total_days >= 0 else 0
        years = total_days // 365 if total_days >= 0 else 0
        self.meses_calc.set(str(months))

        if self.tipo_contrato.get() == "Permanente":
            self.anioss.set(str(years))
        else:
            self.anioss.set("")

    def manejar_documento(self, tipo):
        """
        tipo: 'cv', 'contrato', 'id', 'solvencia'
        """
        attr_src = f"{tipo}_src"
        boton = getattr(self, f"btn_{tipo}")
        etiqueta = getattr(self, f"{tipo}_ok")

        current_path = getattr(self, attr_src, None)

        if not current_path:
            # No hay archivo adjunto: abrir selector
            path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
            if path:
                setattr(self, attr_src, path)
                self.marcar_ok(boton, etiqueta)
        else:
            # Archivo existe: mostrar menú Abrir / Descargar / Ver
            self.mostrar_menu_documento(boton, current_path)

    def abrir_archivo(self, path):
        """
        Abrir el archivo según el sistema operativo
        """
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(["open", path])
        else:  # Linux y otros
            subprocess.call(["xdg-open", path])

    def descargar_archivo(self, path):
        destino = filedialog.asksaveasfilename(
            initialfile=os.path.basename(path),
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")]
        )
        if destino:
            shutil.copy2(path, destino)
            messagebox.showinfo("Descarga completada", f"Archivo guardado en:\n{destino}")

    def marcar_ok(self, boton, etiqueta):
        try:
            boton.configure(style="Success.TButton")
            txt = boton.cget("text") or ""
            if "(Adjuntar)" in txt:
                boton.configure(text=txt.replace("(Adjuntar)", "(Adjuntado)"))
            else:
                if "(Adjuntado)" not in txt:
                    boton.configure(text=txt + "\n(Adjuntado)")
            etiqueta.configure(text="✔️ Adjuntado correctamente")
        except Exception:
            pass

    def limpiar(self):
        for var in [
            self.identidad, self.nombre1, self.nombre2, self.apellido1, self.apellido2,
            self.telefono, self.profesion, self.direccion, self.usuario,
            self.contrasena, self.confirmacion_contrasena,
            self.sueldo, self.anioss, self.diasg, self.unidad, self.rol
        ]:
            var.set("")

        # Restablecer la foto (solo quitar la imagen, no tocar estilos)
        try:
            self.meses_calc.set("")
            self.total_days_calc.set("")
            self.foto_label.image = None
            self.foto_label.configure(image="", text="📷 Seleccionar Foto")
        except Exception:
            pass

        # Borrar rutas de archivos adjuntos
        self.cv_src = self.contrato_src = self.solvencia_src = self.id_src = self.foto_src = None

        # Restaurar estilo original de botones de documentos y texto '(Adjuntar)'
        btn_texts = {
            "btn_cv": "CV\n(Adjuntar)",
            "btn_contrato": "Contrato\n(Adjuntar)",
            "btn_id": "Identidad\n(Adjuntar)",
            "btn_solvencia": "Solvencia\n(Adjuntar)"
        }
        for attr in ("btn_cv", "btn_contrato", "btn_id", "btn_solvencia"):
            boton = getattr(self, attr, None)
            if boton:
                try:
                    boton.configure(style="Folder.TButton")
                    # restablecer texto al valor original si corresponde
                    original = btn_texts.get(attr)
                    if original:
                        boton.configure(text=original)
                except Exception:
                    pass

        # Quitar textos de confirmación
        for etiqueta in (getattr(self, "cv_ok", None), getattr(self, "contrato_ok", None),
                         getattr(self, "id_ok", None), getattr(self, "solvencia_ok", None)):
            if etiqueta:
                try:
                    etiqueta.configure(text="")
                except Exception:
                    pass

        # Opcional: volver a los valores por defecto de los combobox
        if DEPENDENCIAS:
            self.dependencia.set(DEPENDENCIAS[0])
        else:
            self.dependencia.set("")
        if CARGOS:
            self.cargo.set(CARGOS[0])
        else:
            self.cargo.set("")
        self.tipo_contrato.set(CONTRACT_TYPES[0])

    def cancelar(self):
        import os
        import sys
        self.root.destroy()
        os.execl(sys.executable, sys.executable, "Main.py")

    def guardar(self):
        identidad_valor = self.identidad.get().strip()

        # --- VALIDAR IDENTIDAD DUPLICADA ---
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM colaborador WHERE identidad = %s LIMIT 1", (identidad_valor,))
        existe = cur.fetchone()

        conn.close()

        if existe:
            messagebox.showwarning(
                "Identidad duplicada",
                "❌ Este colaborador ya está registrado en el sistema."
            )
            return
        
        # --- FOTO POR DEFECTO ---
        if not self.foto_src:
            self.foto_src = "uploads/admin.jpg"


        # --- NORMALIZAR SUELDO ---
        sueldo_normalizado = self.normalizar_sueldo(self.sueldo.get())
        if sueldo_normalizado is None:
            return  # detener si el sueldo es inválido

        # --- GUARDAR EN BASE DE DATOS ---
        guardar_empleado(
            self.identidad.get(), self.nombre1.get(), self.nombre2.get(),
            self.apellido1.get(), self.apellido2.get(), self.telefono.get(),
            self.profesion.get(), self.tipo_contrato.get(), self.direccion.get(),
            self.dependencia.get(), self.cargo.get(), self.usuario.get(),
            self.contrasena.get(), self.confirmacion_contrasena.get(),
            self.rol.get(), self.unidad.get(), self.cv_src,
            self.fecha_inicio.get_date(), self.fecha_fin.get_date(),
            self.contrato_src, self.solvencia_src, self.id_src,
            self.foto_src, sueldo_normalizado, self.anioss.get(),
            self.diasg.get(), self.fecha_nac_entry.get_date()
        )

        # --- MENSAJE Y LIMPIEZA ---
        messagebox.showinfo("Éxito", "Colaborador registrado correctamente.")
        self.limpiar()

    # --- Indicadores visuales ---
    def marcar_ok(self, boton, etiqueta):
        boton.configure(style="Success.TButton")
        etiqueta.configure(text="✔️ Adjuntado correctamente")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()