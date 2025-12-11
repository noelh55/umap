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
class ReportesWindow:
    def __init__(self, master):
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
        # --- FILTROS ---
        filtros_frame = tk.Frame(self.tab_permisos, bg="#ffffff")
        filtros_frame.pack(fill="x", pady=5, padx=10)

        tk.Label(filtros_frame, text="Buscar Nombre:", bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        self.perm_nombre_var = tk.StringVar()
        self.entry_buscar_permiso = ttk.Entry(filtros_frame, textvariable=self.perm_nombre_var, width=20)
        self.entry_buscar_permiso.grid(row=0, column=1, padx=5)
        self.entry_buscar_permiso.bind("<KeyRelease>", lambda e: self.cargar_tabla_permisos())  # binding

        # ---- Identidad: Combobox editable con autocompletado ----
        tk.Label(filtros_frame, text="Identidad:", bg="#ffffff").grid(row=0, column=2, padx=5, pady=5)
        self.perm_identidad_var = tk.StringVar()
        # Cargar lista de identidades desde la base o una variable predefinida
        self.lista_identidades = self.obtener_lista_identidades()  # función que definiremos abajo
        self.entry_identidad_perm = ttk.Combobox(filtros_frame, textvariable=self.perm_identidad_var,
                                                 values=self.lista_identidades, state="normal", width=20)
        self.entry_identidad_perm.grid(row=0, column=3, padx=5)

        # Filtrado dinámico mientras se escribe
        def filtrar_identidad(*args):
            texto = self.perm_identidad_var.get().lower()
            filtradas = [i for i in self.lista_identidades if texto in i.lower()]
            self.entry_identidad_perm['values'] = filtradas
            self.cargar_tabla_permisos()

        self.perm_identidad_var.trace_add("write", filtrar_identidad)
        self.entry_identidad_perm.bind("<<ComboboxSelected>>", lambda e: self.cargar_tabla_permisos())

        tk.Label(filtros_frame, text="Tipo Permiso:", bg="#ffffff").grid(row=0, column=4, padx=5, pady=5)
        self.perm_tipo_var = tk.StringVar()
        ttk.Entry(filtros_frame, textvariable=self.perm_tipo_var, width=15).grid(row=0, column=5, padx=5)

        tk.Label(filtros_frame, text="Estado:", bg="#ffffff").grid(row=0, column=6, padx=5, pady=5)
        self.perm_estado_var = tk.StringVar()
        ttk.Entry(filtros_frame, textvariable=self.perm_estado_var, width=15).grid(row=0, column=7, padx=5)

        # ---- bindings ----
        self.entry_buscar_tipo_perm = filtros_frame.grid_slaves(row=0, column=3)[0]
        self.entry_buscar_estado_perm = filtros_frame.grid_slaves(row=0, column=5)[0]
        self.entry_buscar_tipo_perm.bind("<KeyRelease>", lambda e: self.cargar_tabla_permisos())
        self.entry_buscar_estado_perm.bind("<KeyRelease>", lambda e: self.cargar_tabla_permisos())

        ttk.Button(filtros_frame, text="Limpiar", command=self.limpiar_filtros_permisos).grid(row=0, column=8, padx=5)

        # --- TABLA ---
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

        # 👉 binding para doble clic
        self.tree_permisos.bind("<Double-1>", self.mostrar_detalle_colaborador)

        # --- CONTADOR ---
        self.label_contador_permisos = tk.Label(self.tab_permisos, text="", bg="#ffffff", font=("Segoe UI", 12, "bold"))
        self.label_contador_permisos.pack(pady=5)

        self.cargar_tabla_permisos()

    def obtener_lista_identidades(self):
        # Conecta DB y obtiene todas las identidades
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT identidad FROM colaborador ORDER BY identidad")
            rows = cur.fetchall()
            conn.close()
            return [r[0] for r in rows]
        except:
            return []

    def limpiar_filtros_permisos(self):
        self.perm_identidad_var.set("")
        self.entry_identidad_perm['values'] = self.lista_identidades
        self.perm_nombre_var.set("")
        self.perm_tipo_var.set("")
        self.perm_estado_var.set("")
        self.cargar_tabla_permisos()
    
    def limpiar_filtros_vacaciones(self):
        self.vac_nombre_var.set("")
        self.vac_estado_var.set("")
        self.cargar_tabla_vacaciones()

    def cargar_tabla_permisos(self):
        # Limpiar tabla
        for row in self.tree_permisos.get_children():
            self.tree_permisos.delete(row)

        query = """SELECT identidad, nombre_completo, tipo_permiso, dias_solicitados,
                   caracter, checks, estado, fecha_entrega, colaborador_id
                   FROM permisos_dias_laborales WHERE 1=1"""
        params = []

        if self.perm_identidad_var.get():
            query += " AND identidad ILIKE %s"
            params.append(f"%{self.perm_identidad_var.get()}%")
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
                values = (idx, *row)  # incluye colaborador_id como última columna
                self.tree_permisos.insert("", "end", values=values)
                self.tabla_datos_permisos.append(values)

            self.label_contador_permisos.config(text=f"Total de solicitudes: {len(self.tabla_datos_permisos)}")

            # Colores por estado
            for item in self.tree_permisos.get_children():
                estado = self.tree_permisos.item(item, "values")[7].lower()  # columna Estado
                if estado in ("aceptada", "aprobada"):
                    self.tree_permisos.item(item, tags=("verde",))
                elif estado == "rechazada":
                    self.tree_permisos.item(item, tags=("rojo",))
                elif estado == "pendiente":
                    self.tree_permisos.item(item, tags=("gris",))

            self.tree_permisos.tag_configure("verde", background="#c6f5d9")
            self.tree_permisos.tag_configure("rojo", background="#f5c6c6")
            self.tree_permisos.tag_configure("gris", background="#e2e2e2")

            # Ocultar columna colaborador_id
            self.tree_permisos["displaycolumns"] = ("#", "Identidad", "Nombre Completo", "Tipo Permiso",
                                                    "Días Solicitados", "Caracter", "Checks", "Estado", "Fecha Entrega")

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
        self.entry_buscar_vac.bind("<KeyRelease>", lambda e: self.cargar_tabla_vacaciones())  # binding

        tk.Label(filtros_frame, text="Estado:", bg="#ffffff").grid(row=0, column=2, padx=5, pady=5)
        self.vac_estado_var = tk.StringVar()
        ttk.Entry(filtros_frame, textvariable=self.vac_estado_var, width=15).grid(row=0, column=3, padx=5)

        ttk.Button(filtros_frame, text="Limpiar", command=self.limpiar_filtros_vacaciones).grid(row=0, column=4, padx=5)

        self.tree_vac_frame = tk.Frame(self.tab_vacaciones, bg="#ffffff")
        self.tree_vac_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columnas = ("#", "Identidad", "Nombre Completo", "Fecha Inicio", "Días a Gozar",
                    "Días Solicitados", "Días Gozados", "Días Restantes", "Estado", "colaborador_id")
        self.tree_vac = ttk.Treeview(self.tree_vac_frame, columns=columnas, show="headings", height=20)
        for col in columnas:
            self.tree_vac.heading(col, text=col)
            self.tree_vac.column(col, width=120, anchor="center")
        self.tree_vac.column("#", width=50)
        self.tree_vac.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(self.tree_vac_frame, orient="vertical", command=self.tree_vac.yview)
        self.tree_vac.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # 👉 binding para doble clic
        self.tree_vac.bind("<Double-1>", self.mostrar_detalle_colaborador)

        self.label_contador_vac = tk.Label(self.tab_vacaciones, text="", bg="#ffffff", font=("Segoe UI", 12, "bold"))
        self.label_contador_vac.pack(pady=5)

        self.cargar_tabla_vacaciones()

    def limpiar_filtros_vacaciones(self):
        self.vac_nombre_var.set("")
        self.vac_estado_var.set("")
        self.cargar_tabla_vacaciones()
    
    def cerrar_ventana(self):
        self.root.destroy()

    def cargar_tabla_vacaciones(self):
        # limpiar tabla
        for row in self.tree_vac.get_children():
            self.tree_vac.delete(row)

        query = """
            SELECT identidad, nombre_completo, fecha_inicio, dias_a_gozar, dias_solicitados, 
                dias_gozados, dias_restantes, estado, colaborador_id
            FROM vacaciones 
            WHERE 1=1
        """
        params = []

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
                values = (idx, *row)  # incluye colaborador_id como última columna
                self.tree_vac.insert("", "end", values=values)
                self.tabla_datos_vacaciones.append(values)

            self.label_contador_vac.config(text=f"Total de solicitudes: {len(self.tabla_datos_vacaciones)}")

            # COLORES
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

        except Exception as e:
            self.label_contador_vac.config(text=f"Error: {e}")
    
    def generar_pdf(self, fila_colaborador, tree_detalle, tabla_origen):
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from tkinter import filedialog

        ruta = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not ruta:
            return

        doc = SimpleDocTemplate(ruta, pagesize=landscape(A4))
        elementos = []
        styles = getSampleStyleSheet()

        # Logo
        import os
        logo_path = os.path.join(os.getcwd(), "muni.jpg") 
        if os.path.exists(logo_path):
            from reportlab.platypus import Image
            logo = Image(logo_path, width=80, height=80)
            elementos.append(logo)

        elementos.append(Spacer(1,10))
        elementos.append(Paragraph("Reporte Detallado del Colaborador", styles['Title']))
        elementos.append(Spacer(1,10))

        # Info colaborador
        info = [[ "Nombre", fila_colaborador[0] ],
                [ "Identidad", fila_colaborador[1] ],
                [ "Cargo", fila_colaborador[2] ],
                [ "Dependencia", fila_colaborador[3] ]]
        t_info = Table(info, hAlign='LEFT')
        t_info.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.black)]))
        elementos.append(t_info)
        elementos.append(Spacer(1,10))

        # Si tabla origen es vacaciones, agregar datos vacacionales
        # Si tabla origen es vacaciones, agregar datos vacacionales
        if tabla_origen == self.tree_vac:
            # Asumiendo fila_colaborador = [nombre_completo, identidad, cargo, dependencia, ...]
            info.append(["Fecha Inicio", fila_colaborador[4] if len(fila_colaborador) > 4 else ""])
            info.append(["Fecha Finalización", fila_colaborador[5] if len(fila_colaborador) > 5 else ""])
            info.append(["Días Solicitados", fila_colaborador[6] if len(fila_colaborador) > 6 else ""])
            info.append(["Días Gozados", fila_colaborador[7] if len(fila_colaborador) > 7 else ""])
            info.append(["Días Restantes", fila_colaborador[8] if len(fila_colaborador) > 8 else ""])
            info.append(["Caracter", fila_colaborador[9] if len(fila_colaborador) > 9 else ""])
            info.append(["Motivo/Check", fila_colaborador[10] if len(fila_colaborador) > 10 else ""])
            info.append(["Observaciones", fila_colaborador[11] if len(fila_colaborador) > 11 else ""])
            info.append(["Comprobante", fila_colaborador[12] if len(fila_colaborador) > 12 else ""])

        elementos.append(Spacer(1,20))
        firmas = [["Firma Director", "", "Firma RH", "", "Firma Solicitante", "", "Firma Jefe Inmediato", ""]]
        t_firmas = Table(firmas, colWidths=150, hAlign="CENTER")
        t_firmas.setStyle(TableStyle([('LINEABOVE',(0,0),(0,0),1,colors.black),
                                      ('LINEABOVE',(2,0),(2,0),1,colors.black),
                                      ('LINEABOVE',(4,0),(4,0),1,colors.black),
                                      ('LINEABOVE',(6,0),(6,0),1,colors.black)]))
        elementos.append(t_firmas)

        # Tabla solicitudes
        datos_tree = [tree_detalle["columns"]]
        for row_id in tree_detalle.get_children():
            datos_tree.append(tree_detalle.item(row_id)["values"])

        # Colores según estado
        estilo_tabla = [('GRID',(0,0),(-1,-1),1,colors.black)]
        for i, fila in enumerate(datos_tree[1:], start=1):
            estado = str(fila[-1]).lower()
            if estado in ("aceptada", "aprobada"):
                estilo_tabla.append(('BACKGROUND',(0,i),(-1,i),colors.lightgreen))
            elif estado == "rechazada":
                estilo_tabla.append(('BACKGROUND',(0,i),(-1,i),colors.salmon))
            elif estado == "pendiente":
                estilo_tabla.append(('BACKGROUND',(0,i),(-1,i),colors.lightgrey))

        t_solicitudes = Table(datos_tree, hAlign='LEFT')
        t_solicitudes.setStyle(TableStyle(estilo_tabla))
        elementos.append(t_solicitudes)
        elementos.append(Spacer(1,10))

        doc.build(elementos)
    
    def mostrar_detalle_colaborador(self, event):
        item_sel = event.widget.selection()
        if not item_sel:
            return
        item = item_sel[0]
        fila = event.widget.item(item, "values")
        colaborador_id = fila[-1] if len(fila) > 8 else None  # id oculto en permisos, None si vacaciones

        # Saber de qué tabla proviene
        tabla_origen = event.widget

        # Crear ventana flotante centrada
        detalle_win = tk.Toplevel(self.root)
        detalle_win.title("Detalle Colaborador")
        detalle_win.configure(bg="white")
        detalle_win.resizable(False, False)
        detalle_win.transient(self.root)
        detalle_win.grab_set()
        ancho, alto = 700, 400
        x = (self.root.winfo_screenwidth() - ancho)//2
        y = (self.root.winfo_screenheight() - alto)//2
        detalle_win.geometry(f"{ancho}x{alto}+{x}+{y}")

        # Traer info colaborador
        if colaborador_id:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""SELECT nombre1, nombre2, apellido1, apellido2, identidad, cargo, dependencia, foto_path
                           FROM colaborador WHERE id=%s""", (colaborador_id,))
            col = cur.fetchone()
            conn.close()
        else:
            col = None

        nombre_completo = f"{col[0]} {col[1]} {col[2]} {col[3]}" if col else "N/A"
        identidad = col[4] if col else "N/A"
        cargo = col[5] if col else "N/A"
        dependencia = col[6] if col else "N/A"
        foto_path = col[7] if col and col[7] else None

        # ----- INFO HORIZONTAL -----
        info_frame = tk.Frame(detalle_win, bg="white")
        info_frame.pack(fill="x", padx=10, pady=10)

        # Foto
        if foto_path:
            from PIL import Image, ImageTk
            img = Image.open(foto_path)
            img = img.resize((100,100))
            foto = ImageTk.PhotoImage(img)
            lbl_foto = tk.Label(info_frame, image=foto, bg="white")
            lbl_foto.image = foto
            lbl_foto.pack(side="left", padx=10)

        # Datos
        datos_frame = tk.Frame(info_frame, bg="white")
        datos_frame.pack(side="left", padx=10)
        tk.Label(datos_frame, text=nombre_completo, font=("Segoe UI", 14, "bold"), bg="white").pack(anchor="w")
        tk.Label(datos_frame, text=f"Identidad: {identidad}", bg="white").pack(anchor="w")
        tk.Label(datos_frame, text=f"Cargo: {cargo}", bg="white").pack(anchor="w")
        tk.Label(datos_frame, text=f"Dependencia: {dependencia}", bg="white").pack(anchor="w")

        # Datos adicionales (solo si tabla origen es vacaciones)
        vac = None
        if tabla_origen == self.tree_vac:
        # traer detalles completos
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""SELECT fecha_inicio, fecha_finalizacion, dias_a_gozar, dias_solicitados,
                                  dias_gozados, dias_restantes, caracter, motivo, observaciones, comprobante_path
                           FROM vacaciones
                           WHERE colaborador_id=%s
                           ORDER BY fecha_inicio DESC""", (colaborador_id,))
            vac = cur.fetchone()
            conn.close()

        if vac:
            info_vac_frame = tk.Frame(datos_frame, bg="white")
            info_vac_frame.pack(anchor="w", pady=5)
            tk.Label(info_vac_frame, text=f"Fecha Inicio: {vac[0]}", bg="white").pack(anchor="w")
            tk.Label(info_vac_frame, text=f"Fecha Finalización: {vac[1]}", bg="white").pack(anchor="w")
            tk.Label(info_vac_frame, text=f"Días a Gozar: {vac[2]}", bg="white").pack(anchor="w")
            tk.Label(info_vac_frame, text=f"Días Solicitados: {vac[3]}", bg="white").pack(anchor="w")
            tk.Label(info_vac_frame, text=f"Días Gozados: {vac[4]}", bg="white").pack(anchor="w")
            tk.Label(info_vac_frame, text=f"Días Restantes: {vac[5]}", bg="white").pack(anchor="w")
            tk.Label(info_vac_frame, text=f"Caracter: {vac[6]}", bg="white").pack(anchor="w")
            tk.Label(info_vac_frame, text=f"Motivo/Check: {vac[7]}", bg="white").pack(anchor="w")
            tk.Label(info_vac_frame, text=f"Observaciones: {vac[8]}", bg="white").pack(anchor="w")

        # Comprobante
        if vac[9]:
            import webbrowser
            def abrir_comprobante():
                webbrowser.open(vac[9])
            tk.Button(info_vac_frame, text="Abrir Comprobante", command=abrir_comprobante).pack(anchor="w", pady=2)

        # ----- TREE HORIZONTAL -----
        tree_frame = tk.Frame(detalle_win, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Si la tabla origen es permisos
        if tabla_origen == self.tree_permisos:
            columnas = ("Tipo Permiso", "Días Solicitados", "Estado")
            consulta = "SELECT tipo_permiso, dias_solicitados, estado FROM permisos_dias_laborales WHERE colaborador_id=%s ORDER BY fecha_entrega DESC"
            color_verde = "#c6f5d9"
            color_rojo = "#f5c6c6"
            color_gris = "#e2e2e2"
        else:  # vacaciones
            columnas = ("Fecha Inicio", "Días a Gozar", "Estado")
            consulta = "SELECT fecha_inicio, dias_a_gozar, estado FROM vacaciones WHERE colaborador_id=%s ORDER BY fecha_inicio DESC"
            color_verde = "#d4f4dd"
            color_rojo = "#f4d4d4"
            color_gris = "#eaeaea"

        tree_detalle = ttk.Treeview(tree_frame, columns=columnas, show="headings", height=7)
        for col_name in columnas:
            tree_detalle.heading(col_name, text=col_name)
            tree_detalle.column(col_name, width=150, anchor="center")

        tree_detalle.pack(fill="both", expand=True, side="left")   # <-- AHORA SI

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree_detalle.yview)
        tree_detalle.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Cargar datos de DB
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(consulta, (colaborador_id,))
        for row in cur.fetchall():
            item = tree_detalle.insert("", tk.END, values=row)
            estado = row[2].lower()
            if estado in ("aceptada", "aprobada"):
                tree_detalle.item(item, tags=("verde",))
            elif estado == "rechazada":
                tree_detalle.item(item, tags=("rojo",))
            elif estado == "pendiente":
                tree_detalle.item(item, tags=("gris",))
        conn.close()

        tree_detalle.tag_configure("verde", background=color_verde)
        tree_detalle.tag_configure("rojo", background=color_rojo)
        tree_detalle.tag_configure("gris", background=color_gris)

        # ----- BOTONES PDF Y CERRAR -----
        botones_frame = tk.Frame(detalle_win, bg="white")
        botones_frame.pack(pady=10)
        ttk.Button(botones_frame, text="Cerrar", command=detalle_win.destroy).pack(side="left", padx=10)
        ttk.Button(botones_frame, text="Exportar a PDF",
                   command=lambda: self.generar_pdf([nombre_completo, identidad, cargo, dependencia],
                                                   tree_detalle, tabla_origen)).pack(side="left", padx=10)