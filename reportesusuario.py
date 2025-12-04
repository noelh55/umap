import tkinter as tk
from tkinter import ttk, filedialog
import psycopg2
import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

# ---------------- CONFIGURACIÓN BD ----------------
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

# ---------------- VENTANA DE REPORTE ----------------
class ReportesU:
    def __init__(self, master, usuario_actual):
        self.usuario_actual = usuario_actual  # 👈 guardar para usar en filtros
        # ---------------- VENTANA FLOTAENTE ----------------
        self.root = tk.Toplevel(master)
        self.root.title("Reporte de Solicitudes")
        self.root.configure(bg="#f4f6f9")
        self.root.resizable(False, False)
        self.root.transient(master)
        self.root.grab_set()

        # Centrar ventana
        ancho, alto = 1200, 700
        x = (self.root.winfo_screenwidth() - ancho)//2
        y = (self.root.winfo_screenheight() - alto)//2
        self.root.geometry(f"{ancho}x{alto}+{x}+{y}")

        # ---------------- CARD ----------------
        self.card_canvas = tk.Canvas(self.root, width=1200, height=700, bg=self.root["bg"], highlightthickness=0)
        self.card_canvas.place(relx=0.5, rely=0.5, anchor="center")
        self.round_rectangle(10, 10, 1190, 690, radius=25, fill="#ffffff", outline="#ffffff")
        self.card_frame = tk.Frame(self.card_canvas, bg="#ffffff")
        self.card_frame.place(x=0, y=0, width=1200, height=700)

        # ---------------- TÍTULO ----------------
        tk.Label(self.card_frame, text="Reporte de Solicitudes",
                 font=("Segoe UI", 18, "bold"), bg="#ffffff").pack(pady=15)

        # ---------------- PESTAÑAS ----------------
        self.notebook = ttk.Notebook(self.card_frame)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=10)

        self.tab_permisos = ttk.Frame(self.notebook)
        self.tab_vacaciones = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_permisos, text="Permisos de Días Laborales")
        self.notebook.add(self.tab_vacaciones, text="Vacaciones")

        # ---------------- VARIABLES ----------------
        self.tabla_datos_permisos = []
        self.tabla_datos_vacaciones = []

        # ---------------- CONSTRUIR UI ----------------
        self.build_tab_permisos()
        self.build_tab_vacaciones()

        # ---------------- BOTÓN CERRAR ----------------
        ttk.Button(self.card_frame, text="Cerrar", command=self.root.destroy).pack(pady=5)

    # ---------------- RECTÁNGULO REDONDEADO ----------------
    def round_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [x1+radius, y1,
                  x2-radius, y1,
                  x2, y1,
                  x2, y1+radius,
                  x2, y2-radius,
                  x2, y2,
                  x2-radius, y2,
                  x1+radius, y2,
                  x1, y2,
                  x1, y2-radius,
                  x1, y1+radius,
                  x1, y1]
        return self.card_canvas.create_polygon(points, smooth=True, **kwargs)

    # ======================
    # TAB PERMISOS
    # ======================
    def build_tab_permisos(self):
        filtros_frame = tk.Frame(self.tab_permisos, bg="#ffffff")
        filtros_frame.pack(fill="x", pady=5, padx=10)

        tk.Label(filtros_frame, text="Buscar Nombre:", bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        self.perm_nombre_var = tk.StringVar()
        self.entry_buscar_permiso = ttk.Entry(filtros_frame, textvariable=self.perm_nombre_var, width=20)
        self.entry_buscar_permiso.grid(row=0, column=1, padx=5)
        self.entry_buscar_permiso.bind("<KeyRelease>", lambda e: self.cargar_tabla_permisos())

        tk.Label(filtros_frame, text="Tipo Permiso:", bg="#ffffff").grid(row=0, column=2, padx=5, pady=5)
        self.perm_tipo_var = tk.StringVar()
        ttk.Entry(filtros_frame, textvariable=self.perm_tipo_var, width=15).grid(row=0, column=3, padx=5)

        tk.Label(filtros_frame, text="Estado:", bg="#ffffff").grid(row=0, column=4, padx=5, pady=5)
        self.perm_estado_var = tk.StringVar()
        ttk.Entry(filtros_frame, textvariable=self.perm_estado_var, width=15).grid(row=0, column=5, padx=5)

        ttk.Button(filtros_frame, text="Limpiar", command=self.limpiar_filtros_permisos).grid(row=0, column=6, padx=5)

        # TABLA
        self.tree_permisos_frame = tk.Frame(self.tab_permisos, bg="#ffffff")
        self.tree_permisos_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columnas = ("#", "Identidad", "Nombre Completo", "Tipo Permiso", "Días Solicitados",
                    "Caracter", "Checks", "Estado", "Fecha Entrega")
        self.tree_permisos = ttk.Treeview(self.tree_permisos_frame, columns=columnas, show="headings", height=20)
        for col in columnas:
            self.tree_permisos.heading(col, text=col)
            self.tree_permisos.column(col, width=120, anchor="center")
        self.tree_permisos.column("#", width=50)
        self.tree_permisos.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(self.tree_permisos_frame, orient="vertical", command=self.tree_permisos.yview)
        self.tree_permisos.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.tree_permisos.bind("<Double-1>", self.mostrar_detalle_colaborador)

        self.label_contador_permisos = tk.Label(self.tab_permisos, text="", bg="#ffffff", font=("Segoe UI", 12, "bold"))
        self.label_contador_permisos.pack(pady=5)

        self.cargar_tabla_permisos()

    def limpiar_filtros_permisos(self):
        self.perm_nombre_var.set("")
        self.perm_tipo_var.set("")
        self.perm_estado_var.set("")
        self.cargar_tabla_permisos()

    def cargar_tabla_permisos(self):
        # Limpiar tabla
        for row in self.tree_permisos.get_children():
            self.tree_permisos.delete(row)

        # 👈 Filtrar solo solicitudes del usuario_actual
        query = """
            SELECT identidad, nombre_completo, tipo_permiso, dias_solicitados,
                   caracter, checks, estado, fecha_entrega, colaborador_id
            FROM permisos_dias_laborales
            WHERE usuario = %s
        """
        params = [self.usuario_actual]

        if self.perm_nombre_var.get():
            query += " AND nombre_completo ILIKE %s"
            params.append(f"%{self.perm_nombre_var.get()}%")
        if self.perm_tipo_var.get():
            query += " AND tipo_permiso ILIKE %s"
            params.append(f"%{self.perm_tipo_var.get()}%")
        if self.perm_estado_var.get():
            query += " AND estado ILIKE %s"
            params.append(f"%{self.perm_estado_var.get()}%")

        query += " ORDER BY fecha_entrega DESC"

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            conn.close()

            self.tabla_datos_permisos = []
            for idx, row in enumerate(rows, start=1):
                values = (idx, *row)
                self.tree_permisos.insert("", "end", values=values)
                self.tabla_datos_permisos.append(values)

            self.label_contador_permisos.config(text=f"Total de solicitudes: {len(self.tabla_datos_permisos)}")

            # Colores
            for item in self.tree_permisos.get_children():
                estado = self.tree_permisos.item(item, "values")[7].lower()
                if estado in ("aceptada", "aprobada"):
                    self.tree_permisos.item(item, tags=("verde",))
                elif estado == "rechazada":
                    self.tree_permisos.item(item, tags=("rojo",))
                elif estado == "pendiente":
                    self.tree_permisos.item(item, tags=("gris",))

            self.tree_permisos.tag_configure("verde", background="#c6f5d9")
            self.tree_permisos.tag_configure("rojo", background="#f5c6c6")
            self.tree_permisos.tag_configure("gris", background="#e2e2e2")

        except Exception as e:
            self.label_contador_permisos.config(text=f"Error: {e}")

    # ======================
    # TAB VACACIONES
    # ======================
    def build_tab_vacaciones(self):
        filtros_frame = tk.Frame(self.tab_vacaciones, bg="#ffffff")
        filtros_frame.pack(fill="x", pady=5, padx=10)

        tk.Label(filtros_frame, text="Buscar Nombre:", bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        self.vac_nombre_var = tk.StringVar()
        self.entry_buscar_vac = ttk.Entry(filtros_frame, textvariable=self.vac_nombre_var, width=20)
        self.entry_buscar_vac.grid(row=0, column=1, padx=5)
        self.entry_buscar_vac.bind("<KeyRelease>", lambda e: self.cargar_tabla_vacaciones())

        tk.Label(filtros_frame, text="Estado:", bg="#ffffff").grid(row=0, column=2, padx=5, pady=5)
        self.vac_estado_var = tk.StringVar()
        ttk.Entry(filtros_frame, textvariable=self.vac_estado_var, width=15).grid(row=0, column=3, padx=5)

        ttk.Button(filtros_frame, text="Limpiar", command=self.limpiar_filtros_vacaciones).grid(row=0, column=4, padx=5)

        # TABLA
        self.tree_vac_frame = tk.Frame(self.tab_vacaciones, bg="#ffffff")
        self.tree_vac_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columnas = ("#", "Identidad", "Nombre Completo", "Fecha Inicio", "Días a Gozar",
                   "Días Solicitados", "Días Gozados", "Días Restantes", "Estado")

        self.tree_vac = ttk.Treeview(self.tree_vac_frame, columns=columnas, show="headings", height=20)
        for col in columnas:
            self.tree_vac.heading(col, text=col)
            self.tree_vac.column(col, width=120, anchor="center")
        self.tree_vac.column("#", width=50)
        self.tree_vac.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(self.tree_vac_frame, orient="vertical", command=self.tree_vac.yview)
        self.tree_vac.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.tree_vac.bind("<Double-1>", self.mostrar_detalle_colaborador)

        self.label_contador_vac = tk.Label(self.tab_vacaciones, text="", bg="#ffffff", font=("Segoe UI", 12, "bold"))
        self.label_contador_vac.pack(pady=5)

        self.cargar_tabla_vacaciones()

    def limpiar_filtros_vacaciones(self):
        self.vac_nombre_var.set("")
        self.vac_estado_var.set("")
        self.cargar_tabla_vacaciones()

    def cargar_tabla_vacaciones(self):
        # limpiar tabla
        for row in self.tree_vac.get_children():
            self.tree_vac.delete(row)

        # 👈 Filtrar solo solicitudes del usuario_actual
        query = """
            SELECT identidad, nombre_completo, fecha_inicio, dias_a_gozar, dias_solicitados,
                   dias_gozados, dias_restantes, estado
            FROM vacaciones
            WHERE usuario = %s
        """
        params = [self.usuario_actual]

        if self.vac_nombre_var.get():
            query += " AND nombre_completo ILIKE %s"
            params.append(f"%{self.vac_nombre_var.get()}%")

        if self.vac_estado_var.get():
            query += " AND estado ILIKE %s"
            params.append(f"%{self.vac_estado_var.get()}%")

        query += " ORDER BY fecha_inicio DESC"

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            conn.close()

            self.tabla_datos_vacaciones = []
            for idx, row in enumerate(rows, start=1):
                values = (idx, *row)
                self.tree_vac.insert("", "end", values=values)
                self.tabla_datos_vacaciones.append(values)

            self.label_contador_vac.config(text=f"Total de solicitudes: {len(self.tabla_datos_vacaciones)}")

            # Colores
            for item in self.tree_vac.get_children():
                estado = self.tree_vac.item(item, "values")[8].lower()
                if estado in ("aceptada", "aprobada"):
                    self.tree_vac.item(item, tags=("verde",))
                elif estado == "rechazada":
                    self.tree_vac.item(item, tags=("rojo",))
                elif estado == "pendiente":
                    self.tree_vac.item(item, tags=("gris",))

            self.tree_vac.tag_configure("verde", background="#c6f5d9")
            self.tree_vac.tag_configure("rojo", background="#f5c6c6")
            self.tree_vac.tag_configure("gris", background="#e2e2e2")

            # ----- BOTONES PDF Y CERRAR -----
            botones_frame = tk.Frame(detalle_win, bg="white")
            botones_frame.pack(pady=10)
            ttk.Button(botones_frame, text="Cerrar", command=detalle_win.destroy).pack(side="left", padx=10)
            ttk.Button(botones_frame, text="Exportar a PDF",
                       command=lambda: self.generar_pdf([nombre_completo, identidad, cargo, dependencia],
                                                       tree_detalle, tabla_origen)).pack(side="left", padx=10)
        
        except Exception as e:
            self.label_contador_vac.config(text=f"Error: {e}")