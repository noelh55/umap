import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from PIL import Image, ImageTk
import os
import sys
import subprocess
import traceback
from datetime import date, timedelta
import psycopg2
from editarcolaborador import App
from tkinter import ttk, filedialog
import subprocess

# ---- Configuración PostgreSQL ----
DB_CONFIG = {
    "host": "localhost",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

BG = "#f9fafb"
TEXT_COLOR = "#2c3e50"
FONT = ("Segoe UI", 10)

def conectar_bd():
    """Conecta a la base de datos PostgreSQL según la configuración global."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print("Error conectando a la base de datos:", e)
        return None

# ---- Colores y estilos ----
BG = "#ecf0f1"
FRAME_BG = "#34495e"
BTN_BG = "#1abc9c"
BTN_HOVER = "#16a085"
TEXT_COLOR = "#2c3e50"
ENTRY_BG = "#ffffff"

class ColaboradorWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Gestión de Colaboradores")
        self.master.geometry("1100x700")
        self.master.configure(bg=BG)
        self.master.state("zoomed")

        # Variables de filtro
        self.estado_var = tk.StringVar(value="Todos")
        self.tipo_contrato_var = tk.StringVar(value="Todos")
        self.id_var = tk.StringVar()
        self.identidad_var = tk.StringVar()
        self.nombre_var = tk.StringVar()
        self.sueldo_var = tk.StringVar()
        self.cargo_var = tk.StringVar()
        self.dependencia_var = tk.StringVar()

        # Cargar listas desde la BD antes de crear los Combobox que las usan
        # (si falla la carga, cargar_listas deja listas vacías)
        try:
            self.cargar_listas()
        except Exception:
            # asegurar atributos por si cargar_listas no corrige
            self.lista_dependencias = getattr(self, "lista_dependencias", [])
            self.lista_cargos = getattr(self, "lista_cargos", [])
            self.lista_identidades = getattr(self, "lista_identidades", [])
            self.lista_nombres_completos = getattr(self, "lista_nombres_completos", [])

        # Frame principal
        main_frame = tk.Frame(self.master, bg=BG, padx=15, pady=15)
        main_frame.pack(fill="both", expand=True)

        # ==== Filtros ==== #
        filtros_frame = tk.LabelFrame(
            main_frame,
            text="Filtros de Búsqueda",
            bg=BG,
            fg=TEXT_COLOR,
            font=("Segoe UI", 12, "bold"),
            padx=25,
            pady=25,
            bd=2,
            relief="groove"
        )
        filtros_frame.pack(fill="x", pady=10)

        # --- Primera fila de filtros ---
        fila1 = tk.Frame(filtros_frame, bg=BG)
        fila1.pack(pady=8)

        tk.Label(fila1, text="Estado:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=8)
        estado_cb = ttk.Combobox(fila1, textvariable=self.estado_var,
                                 values=["Todos", "Activo", "Inactivo"], state="readonly", width=20)
        estado_cb.grid(row=0, column=1, padx=8)
        estado_cb.bind("<<ComboboxSelected>>", lambda e: self.actualizar_tabla())

        tk.Label(fila1, text="Tipo Contrato:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=8)
        tipo_cb = ttk.Combobox(fila1, textvariable=self.tipo_contrato_var,
                               values=["Todos", "Permanente", "Jornal", "Contrato Especial"], state="readonly", width=20)
        tipo_cb.grid(row=0, column=3, padx=8)
        tipo_cb.bind("<<ComboboxSelected>>", lambda e: self.actualizar_tabla())

        tk.Label(fila1, text="Dependencia:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=4, padx=8)
        # Combobox editable con lista cargada de BD
        self.dependencia_cb = ttk.Combobox(fila1, textvariable=self.dependencia_var,
                                   values=self.lista_dependencias, state="normal", width=25)
        self.dependencia_cb.grid(row=0, column=5, padx=8)
        self.dependencia_cb.bind("<<ComboboxSelected>>", lambda e: self.actualizar_tabla())

        tk.Label(fila1, text="Cargo:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=6, padx=8)
        self.cargo_cb = ttk.Combobox(fila1, textvariable=self.cargo_var,
                             values=self.lista_cargos, state="normal", width=25)
        self.cargo_cb.grid(row=0, column=7, padx=8)
        self.cargo_cb.bind("<<ComboboxSelected>>", lambda e: self.actualizar_tabla())

        for col in range(8):
            fila1.grid_columnconfigure(col, weight=1)

        # --- Segunda fila ---
        fila2 = tk.Frame(filtros_frame, bg=BG)
        fila2.pack(pady=8)

        tk.Label(fila2, text="ID:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=8)
        tk.Entry(fila2, textvariable=self.id_var, bg=ENTRY_BG, width=20, font=("Segoe UI", 10)).grid(row=0, column=1, padx=8)

         # Identidad: Combobox editable (se puede escribir manualmente)
        tk.Label(fila2, text="Identidad:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=8)
        self.identidad_cb = ttk.Combobox(fila2, textvariable=self.identidad_var,
                                 values=self.lista_identidades, state="normal", width=25)
        self.identidad_cb.grid(row=0, column=3, padx=8)
        self.identidad_cb.bind("<<ComboboxSelected>>", lambda e: self.actualizar_tabla())

        tk.Label(fila2, text="Nombre:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=4, padx=8)
        self.nombre_cb = ttk.Combobox(fila2, textvariable=self.nombre_var,
                              values=self.lista_nombres_completos, state="normal", width=30)
        self.nombre_cb.grid(row=0, column=5, padx=8)
        self.nombre_cb.bind("<<ComboboxSelected>>", lambda e: self.actualizar_tabla())

         # ---- Sueldo: combobox de rangos + min/max manual ----
        tk.Label(fila2, text="Sueldo (filtro):", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=6, padx=8)
        self.sueldo_range_cb = ttk.Combobox(fila2, state="readonly", width=20,
                                            values=["Todos", "0-1000", "1000-5000", "5000-10000", "10000+"])
        self.sueldo_range_cb.current(0)
        self.sueldo_range_cb.grid(row=0, column=7, padx=8)
        self.sueldo_range_cb.bind("<<ComboboxSelected>>", lambda e: self.actualizar_tabla())

        for col in range(8):
            fila2.grid_columnconfigure(col, weight=1)

        # --- Tercera fila (Fechas) ---
        fila3 = tk.Frame(filtros_frame, bg=BG)
        fila3.pack(pady=8)

        tk.Label(fila3, text="Desde:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=8)
        self.anio_inicio = DateEntry(fila3, date_pattern="yyyy-mm-dd", width=18, background="#1abc9c", foreground="white")
        self.anio_inicio.grid(row=0, column=1, padx=8)
        self.anio_inicio.bind("<<DateEntrySelected>>", lambda e: self.actualizar_tabla())

        tk.Label(fila3, text="Hasta:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=8)
        self.anio_fin = DateEntry(fila3, date_pattern="yyyy-mm-dd", width=18, background="#3498db", foreground="white")
        self.anio_fin.grid(row=0, column=3, padx=8)
        self.anio_fin.bind("<<DateEntrySelected>>", lambda e: self.actualizar_tabla())

        for col in range(4):
            fila3.grid_columnconfigure(col, weight=1)

        # ==== Tabla ==== #
        tabla_frame = tk.Frame(main_frame, bg=BG, bd=2, relief="groove", height=350)  # altura reducida
        tabla_frame.pack(fill="x", pady=10)  # fill solo en X para no estirarse verticalmente

        columnas = ("#", "id", "identidad", "nombre", "tipo_contrato", "dependencia", "cargo",
                    "fecha_inicio", "fecha_fin", "sueldo", "estado")
        self.tree = ttk.Treeview(tabla_frame, columns=columnas, show="headings", height=12)
        # --- Estilo de tabla con colores ---
        style = ttk.Style()
        style.configure("mystyle.Treeview", 
                        background="#FFFFFF",
                        foreground="black",
                        rowheight=25,
                        font=("Arial", 10))
        style.map("mystyle.Treeview", background=[("selected", "#0078D7")])
        self.tree.configure(style="mystyle.Treeview")
        self.tree.bind("<Double-1>", self.mostrar_ficha)

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                        background=FRAME_BG, foreground=TEXT_COLOR)
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=25, background="white", fieldbackground="white")

        for col in columnas:
            self.tree.heading(col, text=col.replace("_", " ").capitalize())
            w = 50 if col == "#" else 120
            self.tree.column(col, anchor="center", width=w)

        vsb = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        tabla_frame.columnconfigure(0, weight=1)
        tabla_frame.rowconfigure(0, weight=1)

        # contador de registros debajo de la tabla
        self.count_label = tk.Label(main_frame, text="Registros: 0", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10))
        self.count_label.pack(anchor="w", padx=20)

        # ==== Botones ==== #
        btns_frame = tk.Frame(main_frame, bg=BG)
        btns_frame.pack(pady=20)

        btn_color_default = "#bdc3c7"  # gris claro
        btn_color_hover = "#5dade2"    # azul claro
 
        def on_enter(e, btn):
            btn.configure(bg=btn_color_hover)

        def on_leave(e, btn):
            btn.configure(bg=btn_color_default)

        btn_pdf = tk.Button(btns_frame, text="📄 Exportar PDF", bg=btn_color_default, fg="white",
                    font=("Segoe UI", 11, "bold"), relief="flat", width=18, height=2,
                    command=self.exportar_pdf)
        btn_pdf.grid(row=0, column=0, padx=15)
        btn_pdf.bind("<Enter>", lambda e: on_enter(e, btn_pdf))
        btn_pdf.bind("<Leave>", lambda e: on_leave(e, btn_pdf))

        btn_excel = tk.Button(btns_frame, text="📊 Exportar Excel", bg=btn_color_default, fg="white", 
                      font=("Segoe UI", 11, "bold"), relief="flat", width=18, height=2,
                      command=self.exportar_excel)
        btn_excel.grid(row=0, column=1, padx=15)
        btn_excel.bind("<Enter>", lambda e: on_enter(e, btn_excel))
        btn_excel.bind("<Leave>", lambda e: on_leave(e, btn_excel))

        btn_limpiar = tk.Button(btns_frame, text="🧹 Limpiar Filtros", bg=btn_color_default, fg="black",
                        font=("Segoe UI", 11, "bold"), relief="flat", width=18, height=2,
                        command=self.limpiar)
        btn_limpiar.grid(row=0, column=3, padx=15)
        btn_limpiar.bind("<Enter>", lambda e: on_enter(e, btn_limpiar))
        btn_limpiar.bind("<Leave>", lambda e: on_leave(e, btn_limpiar))

        btn_regresar = tk.Button(btns_frame, text="↩️ Regresar", bg=btn_color_default, fg="white",
                         font=("Segoe UI", 11, "bold"), relief="flat", width=18, height=2,
                         command=self.volver_main)
        btn_regresar.grid(row=0, column=4, padx=15)
        btn_regresar.bind("<Enter>", lambda e: on_enter(e, btn_regresar))
        btn_regresar.bind("<Leave>", lambda e: on_leave(e, btn_regresar))

        # Refrescar tabla cada segundo
        def refrescar_tabla_periodica():
            self.actualizar_estados_bd()
            self.actualizar_tabla()
            self.master.after(1000, refrescar_tabla_periodica)
        refrescar_tabla_periodica()

        # ---- Actualizar estado automático ----
        self.actualizar_estados_bd()
        self.actualizar_tabla()
        # actualizar datos iniciales
        self.actualizar_estados_bd()
        self.actualizar_tabla()

    def obtener_empleados(self):
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                id,
                COALESCE(identidad, '') AS identidad,
                COALESCE(nombre1, '') || ' ' || COALESCE(nombre2, '') || ' ' ||
                COALESCE(apellido1, '') || ' ' || COALESCE(apellido2, '') AS nombre_completo,
                COALESCE(tipo_contrato, '') AS tipo_contrato,
                COALESCE(dependencia, '') AS dependencia,
                COALESCE(cargo, '') AS cargo,
                fecha_inicio,
                fecha_finalizacion,
                COALESCE(sueldo, 0) AS sueldo,
                estado
            FROM colaborador
            ORDER BY id ASC
        """)

        empleados = cur.fetchall()
        conn.close()
        return empleados

    def actualizar_estados_bd(self):
        hoy = date.today()
        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            # obtener id y fecha_finalizacion para decidir estado por fila
            cur.execute("SELECT id, fecha_finalizacion, estado FROM colaborador")
            rows = cur.fetchall()
            for id_, fecha_fin, estado_actual in rows:
                # decidir nuevo estado (ajusta los literales según la restricción)
                nuevo = "Activo" if (fecha_fin is None or fecha_fin >= hoy) else "Inactivo"
                nuevo = nuevo.strip()
                if estado_actual != nuevo:
                    try:
                        cur.execute("UPDATE colaborador SET estado = TRIM(BOTH FROM %s) WHERE id = %s", (nuevo.strip(), id_))
                    except Exception as e_upd:
                        # loguear fila conflictiva para diagnóstico
                        print(f"Error actualizando estado id={id_}, fecha_fin={fecha_fin}, intento='{nuevo}': {e_upd}")
            conn.commit()
        except Exception as e:
            print("Error en actualizar_estados_bd:", e)
        finally:
            if conn:
                conn.close()

    def cargar_listas(self):
        # Repetir actualización cada 3 segundos
        self.root.after(3000, self.cargar_listas)
        """Carga listas distintas desde la tabla colaborador para filtros."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            # dependencias y cargos
            cur.execute("SELECT DISTINCT dependencia FROM colaborador WHERE dependencia IS NOT NULL ORDER BY dependencia")
            self.lista_dependencias = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT DISTINCT cargo FROM colaborador WHERE cargo IS NOT NULL ORDER BY cargo")
            self.lista_cargos = [row[0] for row in cur.fetchall()]
            # identidades
            cur.execute("SELECT DISTINCT identidad FROM colaborador WHERE identidad IS NOT NULL ORDER BY identidad")
            self.lista_identidades = [row[0] for row in cur.fetchall()]
            # nombres completos (componer)
            cur.execute("SELECT nombre1, nombre2, apellido1, apellido2 FROM colaborador")
            nombres = []
            for n1, n2, a1, a2 in cur.fetchall():
                parts = [p for p in (n1, n2, a1, a2) if p]
                if parts:
                    nombres.append(" ".join(parts))
            # eliminar duplicados manteniendo orden
            seen = set()
            self.lista_nombres_completos = []
            for nm in nombres:
                if nm not in seen:
                    seen.add(nm)
                    self.lista_nombres_completos.append(nm)
            conn.close()
        except Exception as e:
            print("Error cargando listas desde BD:", e)
            self.lista_dependencias = []
            self.lista_cargos = []
            self.lista_identidades = []
            self.lista_nombres_completos = []
        
        for row in self.tree.get_children():
            self.tree.delete(row)

    # ---- Filtrado actualizado ---- #
    def filtrar_empleados(self, empleados):
        # Filtros de interfaz
        estado_filtro = (self.estado_var.get() or "").strip()
        tipo_filtro = (self.tipo_contrato_var.get() or "").strip()
        fecha_inicio = self.anio_inicio.get_date() if hasattr(self, "anio_inicio") else None
        fecha_fin = self.anio_fin.get_date() if hasattr(self, "anio_fin") else None

        id_filtro = (self.id_var.get() or "").strip().lower()
        identidad_filtro = (self.identidad_var.get() or "").strip().lower()
        nombre_filtro = (self.nombre_var.get() or "").strip().lower()
        cargo_filtro = (self.cargo_var.get() or "").strip().lower()
        dep_filtro = (self.dependencia_var.get() or "").strip().lower()

        # rango de sueldo
        sueldo_range = (self.sueldo_range_cb.get() if hasattr(self, "sueldo_range_cb") else "").strip()
        min_sueldo, max_sueldo = None, None
        if sueldo_range and sueldo_range != "Todos":
            if sueldo_range.endswith("+"):
                try:
                    min_sueldo = int(sueldo_range.replace("+", ""))
                except Exception:
                    min_sueldo = None
                max_sueldo = None
            else:
                parts = sueldo_range.split("-")
                try:
                    min_sueldo = int(parts[0])
                    max_sueldo = int(parts[1])
                except Exception:
                    min_sueldo = max_sueldo = None

        filtrados = []
        for emp in empleados:
            # Desempaquetar según SELECT actual
            (id_, identidad, nombre_completo, tipo_contrato, dependencia, cargo,
            fecha_inicio_emp, fecha_finalizacion_emp, sueldo, estado) = emp

            # Normalizar fechas
            try:
                fi_date = fecha_inicio_emp if isinstance(fecha_inicio_emp, date) else (date.fromisoformat(str(fecha_inicio_emp)) if fecha_inicio_emp else None)
            except Exception:
                fi_date = None

            try:
                ff_date = fecha_finalizacion_emp if isinstance(fecha_finalizacion_emp, date) else (date.fromisoformat(str(fecha_finalizacion_emp)) if fecha_finalizacion_emp else None)
            except Exception:
                ff_date = None

            nombre = nombre_completo or ""

            # Determinar estado real del empleado
            emp_estado = (estado or "").strip().lower()
            if not emp_estado:
                if ff_date and ff_date < date.today():
                    emp_estado = "Inactivo"
                else:
                    emp_estado = "Activo"
            # 1) Filtrar por estado (mostrar todos si estado_filtro es "Todos")
            if estado_filtro != "Todos":
                if emp_estado != estado_filtro.lower():
                    continue

            # 2) Filtrar por tipo de contrato (mostrar todos si tipo_filtro es "Todos")
            if tipo_filtro != "Todos":
                if not tipo_contrato or str(tipo_contrato).strip().lower() != tipo_filtro.lower():
                    continue

            # 3) Filtros por ID, Identidad, Nombre
            if id_filtro and id_filtro not in str(id_).lower():
                continue
            if identidad_filtro and identidad_filtro not in str(identidad).lower():
                continue
            if nombre_filtro and nombre_filtro not in nombre.lower():
                continue

            # 4) Filtrar por cargo y dependencia
            if cargo_filtro and cargo_filtro not in (cargo or "").lower():
                continue
            if dep_filtro and dep_filtro not in (dependencia or "").lower():
                continue

            # 5) Filtrar por sueldo
            try:
                sueldo_val = float(sueldo) if sueldo is not None and str(sueldo) != "" else 0.0
            except Exception:
                sueldo_val = 0.0
            if min_sueldo is not None and sueldo_val < min_sueldo:
                continue
            if max_sueldo is not None and sueldo_val > max_sueldo:
                continue

            fi_date = fi_date or None
            ff_date = ff_date or None
            # 6) Filtrar por rango de fechas
            if fecha_inicio and fecha_fin:
                emp_start = fi_date or date.min
                emp_end = ff_date or date.max
                # Incluir inactivos aunque el contrato ya finalizó
                if emp_end < fecha_inicio or emp_start > fecha_fin:
                    continue

            filtrados.append((
                id_, identidad, nombre, tipo_contrato, dependencia, cargo,
                fi_date or "", ff_date or "", sueldo_val, estado
            ))

        return filtrados

    def actualizar_tabla(self):
        # Limpiar tabla
        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            conn = conectar_bd()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, identidad, nombre1 || ' ' || nombre2 || ' ' || apellido1 || ' ' || apellido2 AS nombre,
                       tipo_contrato, dependencia, cargo, fecha_inicio, fecha_finalizacion, sueldo, estado
                FROM colaborador
                ORDER BY id
            """)
            filas = cur.fetchall()
            conn.close()

            for idx, fila in enumerate(filas, start=1):
                # fila: id, identidad, nombre, tipo_contrato, dependencia, cargo, fecha_inicio, fecha_finalizacion, sueldo, estado
                tree_id = self.tree.insert("", "end", values=(idx, *fila))
            
                # Colorear según estado
                estado = fila[-1]  # último campo: estado
                if estado.lower() == "activo":
                    self.tree.item(tree_id, tags=("activo",))
                elif estado.lower() == "inactivo":
                    self.tree.item(tree_id, tags=("inactivo",))
                else:
                    self.tree.item(tree_id, tags=())

            # Definir estilos de tags
            self.tree.tag_configure("activo", background="#d4efdf")   # verde claro
            self.tree.tag_configure("inactivo", background="#f5b7b1") # rojo claro

            # Actualizar contador de registros
            self.count_label.config(text=f"Registros: {len(filas)}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la tabla:\n{e}")

    def mostrar_ficha(self, event):
        """Muestra ventana flotante con ficha editable del colaborador (doble click)."""
        import os
        from tkinter import filedialog
        from PIL import Image, ImageTk

        item = self.tree.focus()
        if not item:
            return

        vals = self.tree.item(item, "values")
        if not vals:
            return

        _, emp_id, identidad, nombre, tipo, dep, cargo, inicio, fin, sueldo, _ = vals

        # --- Crear ventana ---
        top = tk.Toplevel(self.master)
        top.title(f"Editar Colaborador - {nombre}")
        top.geometry("900x550")
        top.configure(bg="#ecf0f1")
        top.resizable(False, False)
        top.transient(self.master)
        top.grab_set()

        # Centrar ventana
        w, h = 900, 550
        x = (top.winfo_screenwidth() // 2) - (w // 2)
        y = (top.winfo_screenheight() // 2) - (h // 2)
        top.geometry(f"{w}x{h}+{x}+{y}")

        # --- Estilos ---
        style = ttk.Style(top)
        style.theme_use("clam")
        style.configure("TLabel", background="#ecf0f1", foreground="#2c3e50", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8, relief="flat")
        style.map("TButton", background=[("active", "#16a085"), ("!active", "#1abc9c")],
                  foreground=[("active", "white"), ("!active", "white")])
        style.configure("TEntry", font=("Segoe UI", 11))

        # --- Conectar BD y obtener datos del colaborador ---
        conn = conectar_bd()
        cur = conn.cursor()
        cur.execute("""
            SELECT identidad, nombre1, nombre2, apellido1, apellido2, telefono, direccion,
                tipo_contrato, dependencia, cargo, fecha_inicio, fecha_finalizacion, sueldo, foto_path,
                cv_path, contrato_path, id_path, solvencia_path
            FROM colaborador WHERE id = %s
        """, (emp_id,))
        fila = cur.fetchone()

        cv_path = fila[14]
        contrato_path = fila[15]
        id_path = fila[16]
        solvencia_path = fila[17]

        # Cargar listas desde BD
        def obtener_lista(tabla):
            try:
                cur.execute(f"SELECT nombre FROM {tabla}")
                return [r[0] for r in cur.fetchall()]
            except:
                return []

        contratos_list = obtener_lista("contratos")
        dependencias_list = obtener_lista("dependencias")
        cargos_list = obtener_lista("cargos")
        conn.close()

        # --- Variables ---
        identidad_var = tk.StringVar(value=fila[0])
        nombre1_var = tk.StringVar(value=fila[1])
        nombre2_var = tk.StringVar(value=fila[2])
        apellido1_var = tk.StringVar(value=fila[3])
        apellido2_var = tk.StringVar(value=fila[4])
        telefono_var = tk.StringVar(value=fila[5])
        direccion_var = tk.StringVar(value=fila[6])
        tipo_contrato_var = tk.StringVar(value=fila[7])
        dependencia_var = tk.StringVar(value=fila[8])
        cargo_var = tk.StringVar(value=fila[9])
        fecha_inicio_var = tk.StringVar(value=fila[10])
        fecha_finalizacion_var = tk.StringVar(value=fila[11])
        sueldo_var = tk.StringVar(value=fila[12])
        foto_path = fila[13]

        # --- Estructura general ---
        main_frame = tk.Frame(top, bg="#ffffff", bd=2, relief="flat")
        main_frame.pack(fill="both", expand=True, padx=25, pady=10)

        # --- Logo municipal (muni.jpg) ---
        try:
            logo_img = Image.open("muni.jpg")
            logo_img = logo_img.resize((80, 80))  # MÁS pequeño aún
            logo_tk = ImageTk.PhotoImage(logo_img)

            lbl_logo = tk.Label(top, image=logo_tk, bg="#ecf0f1")
            lbl_logo.image = logo_tk

            # BAJADO 2 FILAS (y más abajo)
            lbl_logo.place(x=720, y=120)  
        except Exception as e:
            print("Error cargando logo:", e)

        # --- Sección izquierda (Foto) ---
        foto_frame = tk.Frame(main_frame, bg="#ffffff")
        foto_frame.pack(side="left", fill="y", padx=(10, 30))

        tk.Label(foto_frame, text="Foto del colaborador", bg="#ffffff",
                 fg="#2c3e50", font=("Segoe UI", 12, "bold")).pack(pady=(0, 10))

        def cambiar_documento(var_ruta):
            ruta = filedialog.askopenfilename(
                title="Seleccionar archivo",
                filetypes=[("Todos los archivos", "*.*")]
            )
            if ruta:
                var_ruta.set(ruta)

        # Cargar foto
        def cargar_foto(ruta):
            try:
                img = Image.open(ruta)
                img = img.resize((180, 200))
                return ImageTk.PhotoImage(img)
            except:
                return None

        img_actual = cargar_foto(foto_path)
        lbl_foto = tk.Label(foto_frame, image=img_actual, bg="#bdc3c7", width=180, height=200)
        lbl_foto.image = img_actual
        lbl_foto.pack(pady=(0, 10))

        def abrir_archivo(ruta):
            if ruta and os.path.exists(ruta):
                try:
                    subprocess.Popen(ruta, shell=True)
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")
            else:
                messagebox.showwarning("Aviso", "Archivo no disponible.")

        def cambiar_foto():
            ruta = filedialog.askopenfilename(
                title="Seleccionar nueva foto",
                filetypes=[("Archivos de imagen", "*.jpg *.png *.jpeg")]
            )
            if ruta:
                nueva = cargar_foto(ruta)
                if nueva:
                    lbl_foto.configure(image=nueva)
                    lbl_foto.image = nueva
                    nonlocal foto_path
                    foto_path = ruta

        btn_cambiar = tk.Button(foto_frame, text="Cambiar Foto", bg="#1abc9c", fg="white",
                                font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                                command=cambiar_foto)
        btn_cambiar.pack(fill="x", pady=5)

        # --- Sección derecha (Datos) ---
        data_frame = tk.Frame(main_frame, bg="#ffffff")
        data_frame.pack(side="left", fill="both", expand=True)

        campos = [
            ("Identidad:", identidad_var),
            ("Primer Nombre:", nombre1_var),
            ("Segundo Nombre:", nombre2_var),
            ("Primer Apellido:", apellido1_var),
            ("Segundo Apellido:", apellido2_var),
            ("Teléfono:", telefono_var),
            ("Dirección:", direccion_var)
        ]

        fila = 0
        for label, var in campos:
            tk.Label(data_frame, text=label, bg="#ffffff", fg="#2c3e50",
                    font=("Segoe UI", 10, "bold")).grid(row=fila, column=0, sticky="e", pady=4, padx=5)
            ttk.Entry(data_frame, textvariable=var, width=30).grid(row=fila, column=1, pady=4, padx=5)
            fila += 1

        # Comboboxes con datos desde BD
        combos = [
            ("Tipo de Contrato:", tipo_contrato_var, contratos_list),
            ("Dependencia:", dependencia_var, dependencias_list),
            ("Cargo:", cargo_var, cargos_list)
        ]
        for label, var, lista in combos:
            tk.Label(data_frame, text=label, bg="#ffffff", fg="#2c3e50",
                     font=("Segoe UI", 10, "bold")).grid(row=fila, column=0, sticky="e", pady=4, padx=5)
            ttk.Combobox(data_frame, textvariable=var, values=lista, state="readonly", width=27).grid(row=fila, column=1, pady=4, padx=5)
            fila += 1

        # Fechas y sueldo
        tk.Label(data_frame, text="Fecha Inicio:", bg="#ffffff", fg="#2c3e50",
                 font=("Segoe UI", 10, "bold")).grid(row=fila, column=0, sticky="e", pady=4, padx=5)
        ttk.Entry(data_frame, textvariable=fecha_inicio_var, width=30).grid(row=fila, column=1, pady=4)
        fila += 1
        tk.Label(data_frame, text="Fecha Finalización:", bg="#ffffff", fg="#2c3e50",
                 font=("Segoe UI", 10, "bold")).grid(row=fila, column=0, sticky="e", pady=4, padx=5)
        ttk.Entry(data_frame, textvariable=fecha_finalizacion_var, width=30).grid(row=fila, column=1, pady=4)
        fila += 1
        tk.Label(data_frame, text="Sueldo:", bg="#ffffff", fg="#2c3e50",
                 font=("Segoe UI", 10, "bold")).grid(row=fila, column=0, sticky="e", pady=4, padx=5)
        ttk.Entry(data_frame, textvariable=sueldo_var, width=30).grid(row=fila, column=1, pady=4)
        fila += 1

        # --- Documentos Adjuntos ---
        adjuntos = [
            ("CV:", cv_path),
            ("Contrato:", contrato_path),
            ("ID:", id_path),
            ("Solvencia:", solvencia_path)
        ]

        fila_doc = fila  # continuar fila del último entry
        adj_vars = {}  # diccionario para guardar las rutas actualizadas

        for label_text, ruta in adjuntos:
            var = tk.StringVar(value=ruta)
            adj_vars[label_text] = var
            tk.Label(data_frame, text=label_text, bg="#ffffff", fg="#2c3e50",
                    font=("Segoe UI", 10, "bold")).grid(row=fila_doc, column=0, sticky="e", pady=4, padx=5)
            entry = ttk.Entry(data_frame, textvariable=var, width=30)
            entry.grid(row=fila_doc, column=1, pady=4, padx=5)
    
            frame_btns = tk.Frame(data_frame, bg="#ffffff")
            frame_btns.grid(row=fila_doc, column=2, pady=4, padx=5)

            tk.Button(frame_btns, text="Abrir", bg="#3498db", fg="white", font=("Segoe UI", 9, "bold"),
                      relief="flat", command=lambda r=var: abrir_archivo(r.get())).pack(side="left", padx=2)
            tk.Button(frame_btns, text="Cambiar", bg="#1abc9c", fg="white", font=("Segoe UI", 9, "bold"),
                      relief="flat",
                      command=lambda r=var: cambiar_documento(r)).pack(side="left", padx=2)
            fila_doc += 1

        # --- Botones inferiores ---
        btn_frame = tk.Frame(top, bg="#ecf0f1")
        btn_frame.pack(fill="x", pady=15)

        def actualizar_datos():
            try:
                conn = conectar_bd()
                cur = conn.cursor()
                cur.execute("""
                    UPDATE colaborador
                    SET identidad=%s, nombre1=%s, nombre2=%s, apellido1=%s, apellido2=%s,
                        telefono=%s, direccion=%s, tipo_contrato=%s, dependencia=%s,
                        cargo=%s, fecha_inicio=%s, fecha_finalizacion=%s, sueldo=%s, foto_path=%s,
                        cv_path=%s, contrato_path=%s, id_path=%s, solvencia_path=%s
                    WHERE id=%s
                """, (
                    identidad_var.get(), nombre1_var.get(), nombre2_var.get(), apellido1_var.get(), apellido2_var.get(),
                    telefono_var.get(), direccion_var.get(), tipo_contrato_var.get(), dependencia_var.get(),
                    cargo_var.get(), fecha_inicio_var.get(), fecha_finalizacion_var.get(), sueldo_var.get(),
                    foto_path,
                    adj_vars["CV:"].get(),
                    adj_vars["Contrato:"].get(),
                    adj_vars["ID:"].get(),
                    adj_vars["Solvencia:"].get(),
                    emp_id
                ))
                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Datos actualizados correctamente.")
                top.destroy()
                self.actualizar_tabla()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar el colaborador:\n{e}")

        # --- Botones inferiores ---
        btn_frame = tk.Frame(main_frame, bg="#ffffff")
        btn_frame.pack(fill="x", pady=10)

        btn_actualizar = tk.Button(
            top, text="💾 Actualizar", bg="#1abc9c", fg="white",
            font=("Segoe UI", 10, "bold"), width=12, height=1, relief="flat",
            #cursor="hand2",
            command=actualizar_datos
        )
        btn_actualizar.pack(fill="x", pady=5)
        btn_actualizar.place(x=720, y=150)

        btn_cerrar = tk.Button(
            top, text="❌ Cerrar", bg="#e74c3c", fg="white",
            font=("Segoe UI", 10, "bold"), width=12, height=1, relief="flat",
            command=top.destroy
        )
        btn_cerrar.pack(fill="x", pady=5)
        btn_cerrar.place(x=720, y=190)

    # ---- Limpiar filtros ---- #
    def limpiar(self):
        for var in [self.estado_var, self.tipo_contrato_var, self.id_var, self.identidad_var,
                    self.nombre_var, self.sueldo_var, self.cargo_var, self.dependencia_var]:
            var.set("")
        # valores por defecto
        self.estado_var.set("Todos")
        self.tipo_contrato_var.set("Todos")
        # sueldo rango por defecto
        try:
            self.sueldo_range_cb.set("Todos")
        except Exception:
            pass
        # fechas: hoy
        self.anio_inicio.set_date(date.today())
        self.anio_fin.set_date(date.today())
        # recargar listas (por si se añadieron nuevos colaboradores) y actualizar combobox values
        try:
            self.cargar_listas()
            # reasignar valores a comboboxes visibles
            self.dependencia_cb['values'] = self.lista_dependencias
            self.cargo_cb['values'] = self.lista_cargos
            self.identidad_cb['values'] = self.lista_identidades
            self.nombre_cb['values'] = self.lista_nombres_completos
        except Exception:
            pass
        # mostrar toda la información (tabla inicial)
        self.actualizar_tabla()

    # ---- Exportar PDF ---- #
    def exportar_pdf(self):
        data = [self.tree.item(i, "values") for i in self.tree.get_children()]
        if not data:
            messagebox.showwarning("Sin datos", "No hay información para exportar.")
            return

        pdf_path = "reporte_colaboradores.pdf"
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica", 10)
        c.drawString(50, 750, "Reporte de Colaboradores UMAP")
        y = 720
        headers = ["ID", "Identidad", "Nombre", "Contrato", "Dependencia", "Cargo", "Inicio", "Fin", "Sueldo", "Estado"]
        x_positions = [30, 70, 150, 260, 330, 420, 500, 570, 630, 690]

        for i, h in enumerate(headers):
            c.drawString(x_positions[i], y, h)

        y -= 20
        for row in data:
            if y < 50:
                c.showPage()
                y = 750
            for i, val in enumerate(row):
                c.drawString(x_positions[i], y, str(val))
            y -= 18

        c.save()
        messagebox.showinfo("Éxito", f"PDF generado: {pdf_path}")
        self.ultimo_pdf = pdf_path

    # ---- Exportar Excel ---- #
    def exportar_excel(self):
        data = [self.tree.item(i, "values") for i in self.tree.get_children()]
        if not data:
            messagebox.showwarning("Sin datos", "No hay información para exportar.")
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Colaboradores"
        headers = ["ID", "Identidad", "Nombre", "Contrato", "Dependencia", "Cargo", "Inicio", "Fin", "Sueldo", "Estado"]
        ws.append(headers)
        for row in data:
            ws.append(row)

        filename = "reporte_colaboradores.xlsx"
        wb.save(filename)
        messagebox.showinfo("Éxito", f"Excel generado: {filename}")

    # ---- Imprimir PDF ---- #
    def imprimir_pdf(self):
        if not hasattr(self, "ultimo_pdf") or not os.path.exists(self.ultimo_pdf):
            messagebox.showwarning("Atención", "Primero genere el PDF.")
            return
        try:
            os.startfile(self.ultimo_pdf, "print")
        except Exception:
            try:
                subprocess.run(["xdg-open", self.ultimo_pdf])
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el PDF: {e}")

    # ---- Volver a Main ---- #
    def volver_main(self):
        self.master.destroy()
        import Main
        os.execl(sys.executable, sys.executable, "Main.py")

# ==== Ejecutar ventana ==== #
if __name__ == "__main__":
    root = tk.Tk()
    app = ColaboradorWindow(root)

    # ---- Búsqueda en tiempo real ----
    for var in [app.id_var, app.identidad_var, app.nombre_var, app.sueldo_var, app.cargo_var, app.dependencia_var]:
        var.trace_add("write", lambda *args: app.actualizar_tabla())
    
    # Combos también filtran en tiempo real
    app.estado_var.trace_add("write", lambda *args: app.actualizar_tabla())
    app.tipo_contrato_var.trace_add("write", lambda *args: app.actualizar_tabla())

    root.mainloop()