import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import psycopg2
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cargo import VentanaCargo
import subprocess
from datetime import date, timedelta
from crearuser import CrearUsuarioApp
from contrato import VentanaContrato
from panelperfil import AdminUsuarios
import matplotlib
matplotlib.use("TkAgg")  # FORZAR Tkinter backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from admin_permisos import SolicitudesFlotante
from reportec import ReporteEmpleados

# ---------- COLORES DEL DISEÑO MODERNO ----------
BG = "#ecf0f1"       # Fondo principal
TEXT = "#2c3e50"     # Texto oscuro
PANEL = "#2c3e50"    # Panel lateral
BOTON = "#1abc9c"    # Color de botones activos
HOVER = "#16a085"    # Hover de botones

# ---------- CONFIGURACIÓN DE BASE DE DATOS ----------
DB_CONFIG = {
    "host": "localhost",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap",
    "port": "5432"
}

# ---------- VARIABLE GLOBAL PARA EL TOAST ----------
MOSTRAR_BIENVENIDA = True

# 🔧 Evitar errores "invalid command name" al cerrar ventanas
import tkinter
def safe_tk_error_handler(*args):
    # Ignora errores de callbacks después del cierre
    pass

tkinter.Tk.report_callback_exception = staticmethod(safe_tk_error_handler)

# ---------- CLASE DASHBOARD PRINCIPAL ----------
class PantallaPrincipal:
    def __init__(self, root, usuario_actual, mostrar_toast_bienvenida=True):
        global MOSTRAR_BIENVENIDA

        self.root = root
        self.usuario_actual = usuario_actual
        self.mostrar_toast_bienvenida = mostrar_toast_bienvenida and MOSTRAR_BIENVENIDA  # solo true al loguearse

        # --- Configuración base ---
        self.root.title("Sistema Administrativo UMAP - Dashboard")
        self.root.state("zoomed")
        self.root.configure(bg=BG)

        # --- Cargar información del usuario ---
        self.usuario_info = self.obtener_info_usuario()

        # --- Construir interfaz ---
        self.crear_panel_lateral()
        self.crear_panel_principal()
        #self.mostrar_solicitud()  # o el método donde cargas por primera vez
        self.cargar_solicitudes()
        self.actualizar_solicitudes_auto()
        
        self.cargar_solicitudes_vacaciones()
        self.cargar_solicitudes_permisos()
        self.actualizar_tabla_solicitudes()

        # --- Notificación de bienvenida solo al loguearse ---
        if self.mostrar_toast_bienvenida:
            self.root.after(500, lambda: self.mostrar_notificacion(f"Bienvenido, {self.usuario_info.get('nombre', 'Usuario')}!"))
            MOSTRAR_BIENVENIDA = False  # ya no volverá a mostrarse

    # ---------- CONEXIÓN BD ----------
    def conectar_bd(self):
        return psycopg2.connect(**DB_CONFIG)

    def obtener_info_usuario(self):
        try:
            conn = self.conectar_bd()
            cur = conn.cursor()
            cur.execute("""
                SELECT nombre, rol, unidad, foto_path
                FROM usuarios
                WHERE usuario = %s
            """, (self.usuario_actual,))
            row = cur.fetchone()
            conn.close()
            if row:
                return {"nombre": row[0], "rol": row[1], "unidad": row[2], "foto_path": row[3]}
            else:
                return {"nombre": "Desconocido", "rol": "", "unidad": "", "foto_path": ""}
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo obtener la información del usuario:\n{e}")
            return {"nombre": "Error", "rol": "", "unidad": "", "foto_path": ""}

    # ---------- PANEL LATERAL ----------
    def crear_panel_lateral(self):
        self.panel_lateral = tk.Frame(self.root, bg=PANEL, width=300, bd=0, relief="flat")
        self.panel_lateral.pack(side="left", fill="y")
        self.panel_lateral.pack_propagate(False)

        tk.Label(
            self.panel_lateral,
            text="Sistema Municipal",
            font=("Segoe UI", 16, "bold"),
            bg=PANEL,
            fg="white"
        ).pack(pady=15)

        botones = [
            ("👤 Colaboradores", self.abrir_colaborador),
            ("💼 Cargos", self.abrir_cargo),
            ("👨🏼‍💻 Dependencias", self.abrir_dependencia),
            ("👥 Ver Colaboradores", self.abrir_ver_usuario),
            ("📆 Ausencias", self.mostrar_info_sistema),
            ("📊 Reportes", self.mostrar_dashboard),
            ("📑 Contrato", self.mostrar_contrato),
            ("📋 Reporte AV", self.hacer_solicitudes),
            ("📜 Perfiles", self.mostrar_perfiles),
            ("🔚 Salir", self.volver_login)
        ]

        for texto, comando in botones:
            boton = tk.Button(
                self.panel_lateral,
                text=texto,
                font=("Segoe UI", 12),
                bg="#34495e",
                fg="white",
                activebackground=HOVER,
                activeforeground="white",
                relief="flat",
                command=comando
            )
            boton.pack(fill="x", pady=5, padx=10, ipady=10)

    # ---------- PANEL PRINCIPAL ----------
    def crear_panel_principal(self):
        self.panel_principal = tk.Frame(self.root, bg=BG)
        self.panel_principal.pack(side="left", fill="both", expand=True)

        # --- Encabezado superior ---
        header_frame = tk.Frame(self.panel_principal, bg=PANEL, height=90, bd=0, relief="flat")
        header_frame.pack(fill="x", side="top")

        # --- Contenedor de usuario a la DERECHA ---
        user_info_frame = tk.Frame(header_frame, bg=PANEL)
        user_info_frame.pack(side="right", padx=25, pady=10)

        # FOTO (derecha)
        foto_path = self.usuario_info.get("foto_path")
        if foto_path and os.path.exists(foto_path):
            img = Image.open(foto_path).resize((60, 60))
            mask = Image.new("L", img.size, 0)
            from PIL import ImageDraw
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
            img.putalpha(mask)
            circle_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
            circle_img.paste(img, (0, 0), mask=img)
            self.foto_img = ImageTk.PhotoImage(circle_img)
            tk.Label(user_info_frame, image=self.foto_img, bg=PANEL).pack(side="right", padx=(10,0))

        # TEXTO (nombre y rol a la izquierda de la foto)
        texto_frame = tk.Frame(user_info_frame, bg=PANEL)
        texto_frame.pack(side="right", fill="both", pady=5)

        tk.Label(
            texto_frame,
            text=self.usuario_info.get("nombre", "Usuario"),
            font=("Segoe UI", 10, "bold"),
            bg=PANEL,
            fg="white"
        ).pack(anchor="e")

        tk.Label(
            texto_frame,
            text=self.usuario_info.get("rol", ""),
            font=("Segoe UI", 8),
            bg=PANEL,
            fg="white"
        ).pack(anchor="e")

        # --- Separador visual ---
        separador = tk.Frame(self.panel_principal, bg="#F7F3F3", height=2)
        separador.pack(fill="x", side="top")

        container = ttk.Frame(self.panel_principal, padding=10)
        container.pack(fill="both", expand=True)

        # ---------- CUADROS SUPERIORES ----------
        conteos = self.obtener_conteos_contrato()

        cuadros_data = [
            ("📅 Colaboradores", str(conteos["Permanente"]), "#1abc9c"),
            ("🏖️ Contrato Especial", str(conteos["Especial"]), "#3498db"),
            ("🕒 Contrato Jornal", str(conteos["Jornal"]), "#e67e22"),
            ("👥 Total Colaboradores", self.contar_empleados(), "#9b59b6"),
        ]

        cuadros_frame = tk.Frame(container, bg=BG)
        cuadros_frame.pack(fill="x", pady=10)
        cuadros_frame.grid_columnconfigure((0,1,2,3), weight=1)

        for i, (titulo, valor, color) in enumerate(cuadros_data):
            frame = tk.Frame(cuadros_frame, bg=color, height=100, width=200)
            frame.grid(row=0, column=i, padx=8, sticky="nsew")
            frame.pack_propagate(False)

            tk.Label(frame, text=titulo, bg=color, fg="white",
                     font=("Segoe UI", 11, "bold")).pack(pady=(8,0))
            tk.Label(frame, text=valor, bg=color, fg="white",
                     font=("Segoe UI", 20, "bold")).pack(pady=(3,8))

        # --- Panel de solicitudes ---
        solicitudes_frame = ttk.LabelFrame(container, text="Solicitudes", padding=10)
        solicitudes_frame.pack(fill="both", expand=True, pady=10)

        tabla_frame = ttk.Frame(solicitudes_frame)
        tabla_frame.pack(fill="both", padx=5, pady=5)

        columnas = ("#", "identidad", "usuario", "tipo", "cargo", "dependencia","fecha", "estado", "ver")
        encabezados = ["#", "Identidad", "Usuario", "Tipo Solicitud", "cargo", "dependencia", "fecha","Estado", "👁️"]

        tabla_frame.columnconfigure(0, weight=1)
        tabla_frame.rowconfigure(0, weight=1)

        # --- NUEVA TABLA DE SOLICITUDES DESDE BD ---
        self.tree = ttk.Treeview(tabla_frame, columns=columnas, show="headings", height=10)
        self.tree.tag_configure("pendiente", background="#E6E6E6")
        for col, texto in zip(columnas, encabezados):
            self.tree.heading(col, text=texto)
            self.tree.column(col, anchor="center", width=130)
        self.tree.column("#", width=40)
        self.tree.column("ver", width=50)

        vsb = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

       # --- Obtener solicitudes de la base de datos ---
        try:
            conn = self.conectar_bd()
            cur = conn.cursor()

            # 1. VACACIONES
            cur.execute("""
                SELECT 
                    v.id,
                    v.identidad,
                    v.nombre_completo,
                    'Vacaciones' AS tipo,
                    v.fecha_inicio,
                    v.estado,
                    c.cargo,
                    c.dependencia
                FROM vacaciones v
                LEFT JOIN colaborador c ON c.identidad = v.identidad
                ORDER BY v.creado_en DESC;
            """)
            vacaciones = cur.fetchall()

            # 2. PERMISOS
            cur.execute("""
                SELECT
                    p.id,
                    p.identidad,
                    p.nombre_completo,
                    p.tipo_permiso AS tipo,
                    p.fecha_inicio,
                    p.estado,
                    c.cargo,
                    c.dependencia
                FROM permisos_dias_laborales p
                LEFT JOIN colaborador c ON c.identidad = p.identidad
                ORDER BY p.creado_en DESC;
            """)
            permisos = cur.fetchall()

            conn.close()

            todas_solicitudes = vacaciones + permisos

            # LIMPIAR TABLA ANTES DE CARGAR
            for item in self.tree.get_children():
                self.tree.delete(item)

            # INSERTAR
            for i, row in enumerate(todas_solicitudes, 1):
                """
                row =
                0 id
                1 identidad
                2 nombre_completo
                3 tipo (Vacaciones / Permiso)
                4 fecha_inicio
                5 estado
                6 cargo
                7 dependencia
               """

                estado = row[5].lower()

                if estado == "pendiente":
                    tag = "pendiente"
                elif estado == "aceptado":
                    tag = "aceptado"
                elif estado == "rechazado":
                    tag = "rechazado"
                else:
                    tag = ""

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        i,
                        row[1],            # identidad
                        row[2],            # usuario
                        row[3],            # tipo solicitud
                        row[6],            # cargo
                        row[7],            # dependencia
                        str(row[4]),       # fecha
                        row[5],            # estado
                        "👁"               # icono para ver detalle
                    ),
                    tags=(tag,)
                )

            # Colores
            self.tree.tag_configure('pendiente', background='#d3d3d3')
            self.tree.tag_configure('aceptado', background='#a8e6a1')
            self.tree.tag_configure('rechazado', background='#f5a1a1')

            # ACTUALIZAR CADA MINUTO
            self.root.after(60000, self.cargar_solicitudes)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar solicitudes:\n{e}")

        # --- Bind para ver detalle ---
        self.tree.bind("<Double-1>", self.ver_detalle_solicitud)

        self.tree.bind("<Double-1>", self.ver_detalle_solicitud)

        # ---------- CONTENEDOR HORIZONTAL PARA GRÁFICOS + NUEVO CUADRO ----------
        graficos_y_cuadro_container = tk.Frame(container, bg=BG)
        graficos_y_cuadro_container.pack(fill="x", pady=(15, 0))

        # ---------- GRÁFICOS ----------
        graficos_container = tk.Frame(graficos_y_cuadro_container, bg=BG)
        graficos_container.pack(side="left", fill="x", expand=True)

        datos_graficos = [
            ("Total sueldos", int(cuadros_data[0][1])),
            ("Vacaciones/Ausencias", int(cuadros_data[1][1])),
            #("Contrato Jornal", int(cuadros_data[2][1])),
            ("Total Colaboradores", int(cuadros_data[2][1]))
        ]

        colores_graficos = ["#1abc9c", "#3498db", "#9b59b6"]
        #  "#e67e22",

        for i, (titulo, valor) in enumerate(datos_graficos):
            frame = tk.Frame(graficos_container, bg=BG, width=210, height=120) 
            frame.pack(side="left", expand=True, padx=6, pady=10)
            frame.pack_propagate(False)

            nombre_frame = tk.Frame(frame, bg=colores_graficos[i], height=28)
            nombre_frame.pack(fill="x", side="top")
            tk.Label(nombre_frame, text=titulo, bg=colores_graficos[i], fg="white",
                     font=("Segoe UI", 10, "bold")).pack(expand=True)

            fig, ax = plt.subplots(figsize=(2.6, 1.4))
            ax.pie([valor, max(valor * 1.5, 100) - valor],
                   startangle=180,
                   colors=[colores_graficos[i], "#ecf0f1"],
                   wedgeprops={'width': 0.4, 'edgecolor': 'white'})
            ax.axis('equal')

            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.draw()
            canvas.get_tk_widget().pack(expand=True, fill="both")

        # ---------- NUEVO CUADRO AL LADO DE LOS GRÁFICOS ----------
        nuevo_cuadro_container = tk.Frame(graficos_y_cuadro_container, bg=BG, width=190, height=120)
        nuevo_cuadro_container.pack(side="left", padx=6, pady=10)
        nuevo_cuadro_container.pack_propagate(False)

        # --- Calcular totales de vacaciones y permisos ---
        try:
            conn = self.conectar_bd()
            cur = conn.cursor()

            # Total Vacaciones
            cur.execute("SELECT COUNT(*) FROM vacaciones;")
            self.total_vacaciones = cur.fetchone()[0]

            # Total Permisos
            cur.execute("SELECT COUNT(*) FROM permisos_dias_laborales;")
            self.total_permisos = cur.fetchone()[0]

            conn.close()
        except Exception as e:
            self.total_vacaciones = 0
            self.total_permisos = 0
            print(f"[ERROR] No se pudieron obtener los totales: {e}")

        # Lista de datos para mostrar
        nuevo_cuadros_data = [
            (f"🏖️ Vacaciones / {self.total_vacaciones}",
             f"🕒 Ausencias / {self.total_permisos}",
            "#1abc9c")
        ]
        
        for i, (titulo, valor, color) in enumerate(nuevo_cuadros_data):
            frame = tk.Frame(nuevo_cuadro_container, bg=color, width=240, height=100)
            frame.pack(expand=True, fill="both")
            frame.pack_propagate(False)

            tk.Label(frame, text=titulo, bg=color, fg="white",
                     font=("Segoe UI", 11, "bold"), anchor="center", justify="center").pack(expand=True, pady=(5, 2))
            tk.Label(frame, text=valor, bg=color, fg="white",
                     font=("Segoe UI", 11, "bold"), anchor="center", justify="center").pack(expand=True, pady=(2, 5))

        # --- Texto azul ---
        tk.Label(
            container,
            text="Municipalidad de la Esperanza",
            font=("Calibri", 10, "italic"),
            fg="#1565c0",
            bg=BG
        ).pack(side="right", anchor="se", padx=15, pady=8)

    # ---------- FUNCIONES AUXILIARES ----------
    def actualizar_tabla_solicitudes(self):
        try:
            # Limpiar la tabla
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Unir vacaciones + permisos
            solicitudes = []

            for v in self.vacaciones:
                solicitudes.append((
                    v[0],        # id
                    v[1],        # identidad
                    v[2],        # nombre
                    "Vacación",
                    v[8],        # cargo
                    v[9],        # dependencia
                    str(v[4]),   # fecha_inicio
                    v[6],        # estado
                    ""           # sin adjunto
                ))

            for p in self.permisos:
                solicitudes.append((
                    p[0],        # id
                    p[1],        # identidad
                    p[2],        # nombre
                    p[3],        # tipo permiso
                    p[8],        # cargo
                    p[9],        # dependencia
                    str(p[4]),   # fecha_inicio
                    p[6],        # estado
                    p[7]         # adjunto
                ))

            # Insertar en tabla
            for i, row in enumerate(solicitudes, 1):
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        i,
                        row[1],
                        row[2],
                        row[3],
                        row[4],
                        row[5],
                        row[6],
                        row[7],
                        row[8]  # adjunto
                    ),
                    tags=("pendiente",)
                )

            self.tree.tag_configure("pendiente", background="#d3d3d3")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar la tabla: {e}")

    def calcular_dias_contrato(self):
        inicio = date(date.today().year, 1, 1)
        fin = date(date.today().year, 12, 31)
        dias = 0
        while inicio <= fin:
            if inicio.weekday() < 5:
                dias += 1
            inicio += timedelta(days=1)
        return str(dias)

    def contar_empleados(self):
        try:
            conn = self.conectar_bd()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM colaborador;")
            total = cur.fetchone()[0]
            conn.close()
            return str(total)
        except Exception:
            return "0"
        
    def cargar_solicitudes(self):
        try:
            self.cargar_solicitudes_vacaciones()
            self.cargar_solicitudes_permisos()

            todas_solicitudes = self.vacaciones + self.permisos

            for item in self.tree.get_children():
                self.tree.delete(item)

            for i, row in enumerate(todas_solicitudes, 1):
                estado = str(row[5] or "").lower()  # <-- cambio aquí

                if estado == "pendiente":
                    tag = "pendiente"
                elif estado == "aceptado":
                    tag = "aceptado"
                elif estado == "rechazado":
                    tag = "rechazado"
                else:
                    tag = ""
                    
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        i,              # Número
                        row[1],         # identidad
                        row[2],         # usuario
                        row[3],         # tipo solicitud
                        row[8],         # cargo 
                        row[9],         # dependencia
                        str(row[4]),    # fecha
                        row[6],         # estado
                        row[7]          # adjunto
                    ),
                    tags=("pendiente",)
                )

            self.tree.tag_configure('pendiente', background='#d3d3d3')
            self.tree.tag_configure('aceptado', background='#a8e6a1')
            self.tree.tag_configure('rechazado', background='#f5a1a1')

            # Llamada recursiva cada minuto
            self.root.after(60000, self.cargar_solicitudes)

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar solicitudes: {e}")

    # Evitar mensajes "while executing ..." en la consola
    def suppress_tk_errors(*args):
        pass
    tk.Tk.report_callback_exception = suppress_tk_errors

    def cargar_solicitudes_vacaciones(self):
        try:
            conn = self.conectar_bd()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    v.id,
                    v.identidad,
                    v.nombre_completo,
                    'Vacaciones' AS tipo,
                    v.fecha_inicio,
                    v.dias_solicitados,
                    v.estado,
                    '' AS constancia_path,         -- Vacaciones NO tienen adjunto
                    c.cargo,
                    c.dependencia
                FROM vacaciones v
                LEFT JOIN colaborador c ON c.identidad = v.identidad
                WHERE v.estado = 'pendiente'
                ORDER BY v.creado_en DESC;
            """)
            self.vacaciones = cur.fetchall()
            conn.close()
        except Exception as e:
            self.vacaciones = []
            print(f"[ERROR] No se pudieron cargar vacaciones: {e}")

    def cargar_solicitudes_permisos(self):
        try:
            conn = self.conectar_bd()
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    p.id,
                    p.identidad,
                    p.nombre_completo,
                    p.tipo_permiso AS tipo,
                    p.fecha_inicio,
                    p.dias_solicitados,
                    p.estado,
                    p.constancia_path,
                    c.cargo,
                    c.dependencia
                FROM permisos_dias_laborales p
                LEFT JOIN colaborador c ON c.identidad = p.identidad
                WHERE p.estado = 'pendiente'
                ORDER BY p.creado_en DESC;
            """)
            self.permisos = cur.fetchall()
            conn.close()
        except Exception as e:
            self.permisos = []
            print(f"[ERROR] No se pudieron cargar permisos: {e}")

    def actualizar_solicitudes_auto(self):
        self.cargar_solicitudes_vacaciones()
        self.cargar_solicitudes_permisos()
        self.actualizar_tabla_solicitudes()  # donde llenas el treeview
        self.after_actualizar = self.root.after(60000, self.actualizar_solicitudes_auto)

    def mostrar_dashboard(self):
        from reportec import ReporteEmpleados
        ReporteEmpleados(self.root)  # Pasa el root principal como master
    
    # ✅ FUNCIONALIDAD CORRECTA: Mostrar Contrato SIN cerrar el Main
    def mostrar_contrato(self):
        from contrato import VentanaContrato
        ventana_contrato = VentanaContrato(self.root)
        ventana_contrato.transient(self.root)
        ventana_contrato.grab_set()
        ventana_contrato.focus_set()

    # ✅ Nueva función separada para los perfiles (antes era conflicto)
    def mostrar_perfiles(self):
        from panelperfil import AdminUsuarios
        ventana_panel = AdminUsuarios(self.root, usuario_actual=self.usuario_actual)
        ventana_panel.transient(self.root)
        ventana_panel.grab_set()
        ventana_panel.focus_set()

    def abrir_cargo(self):
        VentanaCargo(self.root)
    
    def hacer_solicitudes(self):
        from reportes import ReportesWindow
        ReportesWindow(self.root)   # <-- DEBE SER SELF

    def abrir_dependencia(self):
        from dependencia import VentanaDependencia
        VentanaDependencia(self.root)

    def mostrar_info_sistema(self):
        try:
            # Pasar self.root como master, no self
            win = SolicitudesFlotante(master=self.root)
            win.grab_set()  # modal opcional
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el formulario:\n{e}")

    def volver_login(self):
        global MOSTRAR_BIENVENIDA
        MOSTRAR_BIENVENIDA = True

        # Ejecutar login una sola vez
        script_path = os.path.abspath("log.py")
        subprocess.Popen([sys.executable, script_path])

        # Cancelar callbacks after si existen
        try:
            self.root.after_cancel(self.after_cargar)
        except:
            pass
        try:
            self.root.after_cancel(self.after_actualizar)
        except:
            pass

        # Cerrar esta ventana
        self.root.destroy()
        sys.exit()

    def abrir_colaborador(self):
        self.root.destroy()
        from Colaborador import App
        nuevo_root = tk.Tk()
        App(nuevo_root, usuario_actual=self.usuario_actual)
        nuevo_root.mainloop()

    def abrir_ver_usuario(self):
        self.root.destroy()
        import verempleado
        os.execl(sys.executable, sys.executable, "verempleado.py")

    def ver_detalle_solicitud(self, event):
        item = self.tree.selection()
        if not item:
            return

        datos = self.tree.item(item, "values")

        # Desglosar los valores según columnas:
        numero = datos[0]
        identidad = datos[1]
        usuario = datos[2]
        tipo = datos[3]
        cargo = datos[4]
        dependencia = datos[5]
        fecha = datos[6]
        estado = datos[7]

        # Traducir a nombre bonito
        tipo_legible = "Vacación" if tipo.lower() == "vacaciones" else "Ausencia"

        # Crear ventana
        detalle = tk.Toplevel(self.root)
        detalle.title(f"Detalle de Solicitud #{numero}")
        detalle.configure(bg="#F5F5F5")

        # Ajustar tamaño dinámico
        detalle.update_idletasks()
        width = 600      # más ancho para permitir dos columnas
        height = 420
        x = (detalle.winfo_screenwidth() // 2) - (width // 2)
        y = (detalle.winfo_screenheight() // 2) - (height // 2)
        detalle.geometry(f"{width}x{height}+{x}+{y}")
        detalle.resizable(False, False)

        # Marco principal
        frame = tk.Frame(detalle, bg="white", bd=2, relief="groove")
        frame.place(relx=0.5, rely=0.5, anchor="center", width=560, height=380)

        # Título
        ttk.Label(
            frame,
            text=f"Solicitud #{numero}",
            font=("Segoe UI", 15, "bold")
        ).pack(pady=8)

        # Información a mostrar
        info = [
            ("👤 Usuario:", usuario),
            ("🆔 Identidad:", identidad),
            ("📋 Tipo:", tipo_legible),
            ("💼 Cargo:", cargo),
            ("🏢 Dependencia:", dependencia),
            ("📅 Fecha:", fecha),
            ("🔖 Estado:", estado.capitalize())
        ]

        # FRAME para organizar en columnas
        container = tk.Frame(frame, bg="white")
        container.pack(pady=10)

        # Determinar si usar 1 o 2 columnas dependiendo del tamaño de texto
        usar_dos_columnas = any(len(valor) > 22 for _, valor in info)

        if usar_dos_columnas:
            # Crear dos columnas
            col1 = tk.Frame(container, bg="white")
            col2 = tk.Frame(container, bg="white")
            col1.grid(row=0, column=0, padx=10, sticky="n")
            col2.grid(row=0, column=1, padx=10, sticky="n")

            mitad = len(info) // 2 + (len(info) % 2)
            columna_1_items = info[:mitad]
            columna_2_items = info[mitad:]

            for label_text, valor in columna_1_items:
                f = tk.Frame(col1, bg="white")
                f.pack(anchor="w", pady=5)
                tk.Label(f, text=label_text, font=("Segoe UI", 11, "bold"), bg="white").pack(anchor="w")
                tk.Label(f, text=valor, font=("Segoe UI", 11), bg="white", fg="#333").pack(anchor="w")

            for label_text, valor in columna_2_items:
                f = tk.Frame(col2, bg="white")
                f.pack(anchor="w", pady=5)
                tk.Label(f, text=label_text, font=("Segoe UI", 11, "bold"), bg="white").pack(anchor="w")
                tk.Label(f, text=valor, font=("Segoe UI", 11), bg="white", fg="#333").pack(anchor="w")

        else:
            # Una sola columna
            for label_text, valor in info:
                f = tk.Frame(container, bg="white")
                f.pack(anchor="w", pady=5)
                tk.Label(f, text=label_text, font=("Segoe UI", 11, "bold"), bg="white").pack(anchor="w")
                tk.Label(f, text=valor, font=("Segoe UI", 11), bg="white", fg="#333").pack(anchor="w")

        # Recuperar adjunto (último valor enviado)
        adjunto = datos[8] if len(datos) > 8 else ""

        # Frame de botones
        botonera = tk.Frame(frame, bg="white")
        botonera.pack(pady=10)

        # Botón ver adjunto (solo si existe)
        if adjunto and os.path.exists(adjunto):
            ttk.Button(
                botonera,
                text="📄 Ver adjunto",
                command=lambda: os.startfile(adjunto)
            ).pack(pady=5)

        # Botón cerrar
        ttk.Button(botonera, text="Cerrar", command=detalle.destroy).pack(pady=5)

    # ---------- NOTIFICACIÓN TIPO TOAST SEGURA ----------
    def mostrar_notificacion(self, mensaje):
        self.toast = tk.Toplevel(self.root)
        self.toast.overrideredirect(True)
        self.toast.configure(bg="#333333")
        self.toast.attributes("-topmost", True)
        self.toast.attributes("-alpha", 0.0)

        self.root.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() - 300
        y = self.root.winfo_y() + 20
        self.toast.geometry(f"250x50+{x}+{y}")

        lbl = tk.Label(self.toast, text=mensaje, bg="#333333", fg="white", font=("Segoe UI", 10, "bold"))
        lbl.pack(expand=True, fill="both")

        # IDs de after
        self._fade_in_id = None
        self._fade_out_id = None

        def fade_in(alpha=0.0):
            if not self.toast.winfo_exists():
                return
            alpha += 0.05
            if alpha >= 1.0:
                if self.toast.winfo_exists():
                    self._fade_out_id = self.toast.after(2000, fade_out)
                return
            self.toast.attributes("-alpha", alpha)
            self._fade_in_id = self.toast.after(30, lambda: fade_in(alpha))

        def fade_out(alpha=1.0):
            if not self.toast.winfo_exists():
                return
            alpha -= 0.05
            if alpha <= 0.0:
                if self.toast.winfo_exists():
                    self.toast.destroy()
                return
            self.toast.attributes("-alpha", alpha)
            self._fade_out_id = self.toast.after(30, lambda: fade_out(alpha))

        fade_in()

    def _cerrar(self):
        if hasattr(self, "_reloj_after_id"):
            self.root.after_cancel(self._reloj_after_id)
        if hasattr(self, "_fade_in_id") and self._fade_in_id:
            try:
                self.root.after_cancel(self._fade_in_id)
            except:
                pass
        if hasattr(self, "_fade_out_id") and self._fade_out_id:
            try:
                self.root.after_cancel(self._fade_out_id)
            except:
                pass
        if hasattr(self, "toast") and self.toast.winfo_exists():
            self.toast.destroy()
            self.root.destroy()

    def obtener_conteos_contrato(self):
        conteos = {
            "Permanente": 0,
            "Especial": 0,
           "Jornal": 0
        }

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            cur.execute("""
                SELECT tipo_contrato, COUNT(*) 
                FROM colaborador 
                GROUP BY tipo_contrato;
            """)

            for tipo, total in cur.fetchall():
                if tipo in conteos:
                    conteos[tipo] += total

            cur.close()
            conn.close()

        except Exception as e:
            print(f"[ERROR] No se pudieron obtener los conteos: {e}")

        return conteos

# ---------- MAIN ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = PantallaPrincipal(root, usuario_actual="admin")
    root.mainloop()