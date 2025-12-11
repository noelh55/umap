import sys
import psycopg2
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
from datetime import date, timedelta
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PermisosDiasLaborales import EditarP
from vacaciones import SolicitudVacaciones  # Importa la clase de tu archivo vacaciones.py

# ---------- COLORES DEL DISEÑO MODERNO ----------
BG = "#ecf0f1"
TEXT = "#2c3e50"
PANEL = "#2c3e50"
BOTON = "#1abc9c"
HOVER = "#16a085"

# ---------- CONFIGURACIÓN DE BASE DE DATOS ----------
DB_CONFIG = {
    "host": "localhost",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap",
    "port": "5432"
}

MOSTRAR_BIENVENIDA = True

# ============================================================
# FUNCIÓN GENERAL DE CONEXIÓN
# ============================================================
def conectar_db():
    return psycopg2.connect(
        host="localhost",
        database="database_umap",
        user="postgres",
        password="umap",
        port="5432"
    )

# ============================================================
# CLASE PRINCIPAL DE PANEL DE USUARIO
# ============================================================
class PantallaPrincipal: 
    def __init__(self, root, usuario_actual, mostrar_toast_bienvenida=True):
        global MOSTRAR_BIENVENIDA

        self.root = root
        self.usuario_actual = usuario_actual
        self.detalle_abierto = None
        self.mostrar_toast_bienvenida = mostrar_toast_bienvenida and MOSTRAR_BIENVENIDA

        # Inicializar la variable de la ventana flotante
        self.ventana_permisos = None

        # --- Configuración base ---
        self.root.title("Sistema Administrativo UMAP - Usuarios")
        self.root.state("zoomed")
        self.root.configure(bg=BG)

        # --- Cargar información del usuario ---
        self.usuario_info = self.obtener_info_usuario()

        # --- Construir interfaz ---
        self.crear_panel_lateral()
        self.crear_panel_principal()

        # --- Notificación de bienvenida ---
        if self.mostrar_toast_bienvenida:
            self.root.after(500, lambda: self.mostrar_notificacion(f"Bienvenido, {self.usuario_info.get('nombre', 'Usuario')}!"))
            MOSTRAR_BIENVENIDA = False

        self.after_actualizar_dashboard = self.root.after(1000, self.actualizar_dashboard)

    def conectar_bd(self):
        return psycopg2.connect(**DB_CONFIG)

    def obtener_info_usuario(self):
        """
        Obtiene información del usuario actual desde tabla usuarios o colaborador.
        Devuelve un diccionario con: nombre completo, rol, dependencia, cargo y foto_path.
        """
        try:
            conn = self.conectar_bd()
            cur = conn.cursor()
            # Primero intentamos desde tabla colaborador
            cur.execute("""
                SELECT nombre1, nombre2, apellido1, apellido2, rol, cargo, dependencia, foto_path
                FROM colaborador
                WHERE usuario = %s
            """, (self.usuario_actual,))
            row = cur.fetchone()
            if row:
                nombre_completo = " ".join(filter(None, [row[0], row[1], row[2], row[3]]))
                return {
                    "nombre": nombre_completo,
                    "rol": "",
                    "cargo": row[5],
                    "dependencia": row[6],
                    "foto_path": row[7],
                    "origen": "colaborador"
                }
            # Si no se encuentra en colaborador, buscamos en usuarios
            cur.execute("""
                SELECT nombre, nombre2, apellido1, apellido2, rol, foto_path
                FROM usuarios
                WHERE usuario = %s
            """, (self.usuario_actual,))
            row2 = cur.fetchone()
            conn.close()
            if row2:
                nombre_completo = " ".join(filter(None, [row2[0], row2[1], row2[2], row2[3]]))
                return {
                    "nombre": nombre_completo,
                    "rol": row2[4],
                    "cargo": "",          # No mostrar cargo
                    "dependencia": "",    # No mostrar dependencia
                    "foto_path": row2[5],
                    "origen": "usuarios"
                }
            # Si no se encuentra en ninguna tabla
            return {"nombre": "Desconocido", "rol": "", "cargo": "", "dependencia": "", "foto_path": "", "origen": ""}
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo obtener la información del usuario:\n{e}")
            return {"nombre": "Error", "rol": "", "cargo": "", "dependencia": "", "foto_path": "", "origen": ""}

    # ============================================================
    # PANEL PRINCIPAL
    # ============================================================
    def crear_panel_principal(self):
        self.panel_principal = tk.Frame(self.root, bg=BG)
        self.panel_principal.pack(fill="both", expand=True, side="right")
        self.var_dias_ausencia = tk.StringVar()
        self.var_dias_ausencia.set(self.calcular_dias_ausencia())

        # --- Encabezado superior ---
        header_frame = tk.Frame(self.panel_principal, bg=PANEL, height=100)
        header_frame.pack(fill="x", side="top", anchor="n")
        header_frame.pack_propagate(False)

        titulo_header = tk.Label(
            header_frame,
            text="SISTEMA MUNICIPAL",
            bg=PANEL,
            fg="white",
            font=("Segoe UI Semibold", 20, "bold"),
            anchor="center"
        )
        titulo_header.pack(expand=True, fill="both")

        # --- Separador visual ---
        separador = tk.Frame(self.panel_principal, bg="#F7F3F3", height=2)
        separador.pack(fill="x", side="top")

        container = ttk.Frame(self.panel_principal, padding=10)
        container.pack(fill="both", expand=True)

        # ---------- CUADROS SUPERIORES ----------
        cuadros_data = [
            ("📅 Días Trabajados", self.calcular_dias_trabajados(), "#1abc9c"),
            ("🏖️ Días Gozar", self.calcular_dias_a_gozar(), "#3498db"),
            ("🕒 Días de Ausencia", self.var_dias_ausencia, "#e67e22"),
            ("📅 Días Restantes", self.calcular_dias_restantes(), "#9b59b6"),
        ]
        cuadros_frame = tk.Frame(container, bg=BG)
        cuadros_frame.pack(fill="x", pady=(30, 20))
        cuadros_frame.grid_columnconfigure((0,1,2,3), weight=1)

        # Variable para actualizar dinámicamente Dias de Ausencia
        self.var_dias_ausencia = tk.StringVar(value=self.calcular_dias_ausencia())

        for i, (titulo, valor, color) in enumerate(cuadros_data):
            frame = tk.Frame(cuadros_frame, bg=color, height=100, width=200)
            frame.grid(row=0, column=i, padx=8, sticky="nsew")
            frame.pack_propagate(False)

            # Label del título
            tk.Label(frame, text=titulo, bg=color, fg="white",
                    font=("Segoe UI", 11, "bold")).pack(pady=(8,0))

            # Label del valor, dinámico con StringVar o valor fijo
            valor_lbl = tk.Label(frame,
                                textvariable=valor if isinstance(valor, tk.StringVar) else None,
                                text=valor if not isinstance(valor, tk.StringVar) else None,
                                font=("Arial", 18, "bold"), bg=color, fg="white")
            valor_lbl.pack(pady=(3,8))

        # ---------------- PANEL DE SOLICITUDES ----------------
        solicitudes_frame = ttk.LabelFrame(container, text="Solicitudes", padding=10)
        solicitudes_frame.pack(fill="both", expand=True, pady=10)

        tabla_frame = ttk.Frame(solicitudes_frame)
        tabla_frame.pack(fill="both", padx=5, pady=5)
        tabla_frame.columnconfigure(0, weight=1)
        tabla_frame.rowconfigure(0, weight=1)

        columnas = ("#", "identidad", "usuario", "tipo", "cargo", "dependencia", "fecha", "estado", "ver")
        encabezados = ["#", "Identidad", "Usuario", "Tipo Solicitud", "Cargo", "Dependencia", "Fecha", "Estado", "👁️"]

        self.tree = ttk.Treeview(tabla_frame, columns=columnas, show="headings", height=8)
        for col, texto in zip(columnas, encabezados):
            self.tree.heading(col, text=texto)
            self.tree.column(col, anchor="center", width=120)
        self.tree.column("ver", width=50)

        vsb = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        tabla_frame.columnconfigure(0, weight=1)
        tabla_frame.rowconfigure(0, weight=1)

        # Configurar colores según estado
        self.tree.tag_configure("aprobada", background="#c8f7c5")   # verde claro
        self.tree.tag_configure("rechazada", background="#f7c5c5")  # rojo claro
        self.tree.tag_configure("pendiente", background="#e8e8e8")  # gris claro

        self.tree.bind("<Double-1>", self.ver_detalle_solicitud)
        self.cargar_solicitudes()

        # ---------- GRÁFICOS ----------
        graficos_container = tk.Frame(container, bg=BG)
        graficos_container.pack(fill="x", pady=(10, 10))

        datos_graficos = [
            ("Dias Trabajados", int(cuadros_data[0][1])),
            ("Dias Gozados", int(cuadros_data[1][1])),
            ("Dias Pendientes", int(cuadros_data[2][1].get())),
            ("Dias Restantes", int(cuadros_data[3][1]))
        ]

        colores_graficos = ["#1abc9c", "#3498db", "#e67e22", "#9b59b6"]

        for i, (titulo, valor) in enumerate(datos_graficos):
            frame = tk.Frame(graficos_container, bg=BG, width=200, height=140)
            frame.pack(side="left", expand=True, padx=10, pady=5)
            frame.pack_propagate(False)

            nombre_frame = tk.Frame(frame, bg=colores_graficos[i], height=28)
            nombre_frame.pack(fill="x", side="top")
            tk.Label(nombre_frame, text=titulo, bg=colores_graficos[i], fg="white",
                     font=("Segoe UI", 11, "bold")).pack(expand=True)

            fig, ax = plt.subplots(figsize=(2.4, 1.5))
            ax.pie([valor, max(valor * 1.5, 100) - valor],
                   startangle=180,
                   colors=[colores_graficos[i], "#ecf0f1"],
                   wedgeprops={'width': 0.4, 'edgecolor': 'white'})
            ax.axis('equal')

            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.draw()
            canvas.get_tk_widget().pack(expand=True, fill="both")

        footer_label = tk.Label(
            self.panel_principal,
            text="Municipalidad de la Esperanza",
            bg=BG,
            fg="#2980b9",
            font=("Segoe UI", 9, "italic"),
            anchor="se"
        )
        footer_label.pack(side="bottom", anchor="se", padx=10, pady=5)

    # ============================================================
    # PANEL LATERAL
    # ============================================================
    def crear_panel_lateral(self):
        self.panel_lateral = tk.Frame(self.root, bg=PANEL, width=300)
        self.panel_lateral.pack(side="left", fill="y")
        self.panel_lateral.pack_propagate(False)

        foto_path = self.usuario_info.get("foto_path")
        if foto_path and os.path.exists(foto_path):
            img = Image.open(foto_path).resize((160, 160), Image.LANCZOS)
            self.foto_img = ImageTk.PhotoImage(img)
            foto_frame = tk.Frame(self.panel_lateral, bg=PANEL)
            foto_frame.pack(pady=(40, 20))
            tk.Label(foto_frame, image=self.foto_img, bg=PANEL, bd=3, relief="solid").pack()

        # Mostrar nombre completo
        tk.Label(
            self.panel_lateral,
            text=self.usuario_info.get("nombre", "Usuario"),
            font=("Segoe UI", 11, "bold"),
            bg=PANEL,
            fg="white"
        ).pack()

        # Mostrar cargo y dependencia solo si el usuario viene de colaborador
        if self.usuario_info.get("origen") == "colaborador":
            tk.Label(
                self.panel_lateral,
                text=self.usuario_info.get("cargo", ""),
                font=("Segoe UI", 10),
                bg=PANEL,
                fg="white"
            ).pack()
            tk.Label(
                self.panel_lateral,
                text=self.usuario_info.get("dependencia", ""),
                font=("Segoe UI", 10),
                bg=PANEL,
                fg="white"
            ).pack(pady=(0, 10))

        # Mostrar rol solo si NO viene de colaborador
        if self.usuario_info.get("origen") != "colaborador":
            tk.Label(
                self.panel_lateral,
                text=self.usuario_info.get("rol", ""),
                font=("Segoe UI", 10),
                bg=PANEL,
                fg="white"
            ).pack(pady=(0, 25))

        botones = [
            ("📆 Ausencias", self.mostrar_info_sistema),
            ("🏖️ Vacaciones", self.mostrar_vacaciones),
            ("📊 Reportes", self.mostrar_dashboard),
            ("👤 Perfil", self.configuracion_dashboard),
            ("🔚 Salir", self.volver_login)
        ]

        for texto, comando in botones:
            boton = tk.Button(
                self.panel_lateral,
                text=texto,
                font=("Segoe UI", 11, "bold"),
                bg="#34495e",
                fg="white",
                activebackground=HOVER,
                activeforeground="white",
                relief="flat",
                command=comando,
                cursor="hand2",
                padx=25,
                pady=12
            )
            boton.pack(fill="x", padx=15, pady=8)

    # ============================================================
    # FUNCIONES AUXILIARES
    # ============================================================
    def actualizar_dashboard(self):
        try:
            # Actualizar el label que muestra días de ausencia
            if hasattr(self, "lbl_dias_ausencia"):
                self.lbl_dias_ausencia.config(text=self.calcular_dias_ausencia())
        except:
            pass

        # Volver a ejecutar dentro de 1 segundo
        self.after_actualizar = self.root.after(1000, self.actualizar_dashboard)

    def actualizar_dashboard(self):
        # Actualiza dinámicamente el contador de días de ausencia
        try:
            nuevo_valor = self.calcular_dias_ausencia()
            self.var_dias_ausencia.set(nuevo_valor)
        except:
            pass

        # Repite cada segundo
        self.after_actualizar_dashboard = self.root.after(1000, self.actualizar_dashboard)

    def actualizar_tabla(self):
        try:
            self.cargar_solicitudes()
        except:
            pass
        self.root.after(1000, self.actualizar_tabla)

    def calcular_dias_contrato(self):
        inicio = date(date.today().year, 1, 1)
        fin = date(date.today().year, 12, 31)
        dias = 0
        while inicio <= fin:
            if inicio.weekday() < 5:
                dias += 1
            inicio += timedelta(days=1)
        return str(dias)
    
    def calcular_dias_trabajados(self):
        try:
            conn = self.conectar_bd()
            cur = conn.cursor()

            # buscar fecha_inicio del usuario
            cur.execute("""
                SELECT fecha_inicio
                FROM colaborador
                WHERE usuario = %s
            """, (self.usuario_actual,))

            row = cur.fetchone()
            conn.close()

            if not row or not row[0]:
                return "0"

            fecha_inicio = row[0]
            fecha_actual = date.today()

            dias = 0
            while fecha_inicio <= fecha_actual:
                if fecha_inicio.weekday() < 5:   # lunes-viernes
                    dias += 1
                fecha_inicio += timedelta(days=1)

            return str(dias)

        except Exception:
            return "0"
        
    def calcular_dias_a_gozar(self):
        try:
            conn = self.conectar_bd()
            cur = conn.cursor()

            cur.execute("""
                SELECT fecha_inicio
                FROM colaborador
                WHERE usuario = %s
            """, (self.usuario_actual,))

            row = cur.fetchone()
            conn.close()

            if not row or not row[0]:
                return "0"

            fecha_inicio = row[0]
            hoy = date.today()

            # años completos transcurridos
            anios = hoy.year - fecha_inicio.year
            if (hoy.month, hoy.day) < (fecha_inicio.month, fecha_inicio.day):
                anios -= 1

            if anios <= 0:
                return "0"

            dias = min(anios * 5, 20)
            return str(dias)

        except Exception:
            return "0"
        
    def calcular_dias_a_gozar(self):
        try:
            conn = self.conectar_bd()
            cur = conn.cursor()

            cur.execute("""
                SELECT fecha_inicio
                FROM colaborador
                WHERE usuario = %s
            """, (self.usuario_actual,))

            row = cur.fetchone()
            conn.close()

            if not row or not row[0]:
                return "0"

            fecha_inicio = row[0]
            hoy = date.today()

            # años completos transcurridos
            anios = hoy.year - fecha_inicio.year
            if (hoy.month, hoy.day) < (fecha_inicio.month, fecha_inicio.day):
                anios -= 1

            if anios <= 0:
                return "0"

            dias = min(anios * 5, 20)
            return str(dias)

        except Exception:
            return "0"
        
    def calcular_dias_ausencia(self):
        try:
            conn = self.conectar_bd()
            cur = conn.cursor()

            # Obtener identidad e id del colaborador
            cur.execute("""
                SELECT identidad, id 
                FROM colaborador
                WHERE usuario = %s
            """, (self.usuario_actual,))
            row = cur.fetchone()

            if not row:
                conn.close()
                return "0"

            identidad, colaborador_id = row

            # Traer SOLO aprobadas
            cur.execute("""
                SELECT fecha_inicio, fecha_fin
                FROM permisos_dias_laborales
                WHERE (colaborador_id = %s OR identidad = %s)
                AND estado = 'Aprobada'
                ORDER BY fecha_inicio ASC
            """, (colaborador_id, identidad))

            solicitudes = cur.fetchall()
            conn.close()

            if not solicitudes:
                return "0"

            hoy = date.today()

            # ---- AGRUPAR BLOQUES CONSECUTIVOS ----
            bloques = []
            inicio_b = solicitudes[0][0]
            fin_b = solicitudes[0][1]

            for fi, ff in solicitudes[1:]:
                # Si la siguiente solicitud empieza justo al día siguiente → es consecutiva
                if fi == fin_b + timedelta(days=1):
                    fin_b = ff
                else:
                    bloques.append((inicio_b, fin_b))
                    inicio_b = fi
                    fin_b = ff

            bloques.append((inicio_b, fin_b))

            # ---- CALCULAR DÍAS RESTANTES ----
            total_restante = 0

            for fi, ff in bloques:
                dia = max(fi, hoy)
                while dia <= ff:
                    if dia.weekday() < 5:     # Solo días hábiles L–V
                        total_restante += 1
                    dia += timedelta(days=1)

            return str(total_restante)

        except Exception:
            return "0"
        
    def calcular_dias_restantes(self):
        try:
            conn = self.conectar_bd()
            cur = conn.cursor()

            # obtener la fecha_fin del usuario
            cur.execute("""
                SELECT fecha_finalizacion
                FROM colaborador
                WHERE usuario = %s
            """, (self.usuario_actual,))
            row = cur.fetchone()
            conn.close()

            if not row or not row[0]:
                return "0"

            fecha_finalizacion = row[0]
            hoy = date.today()

            # Si ya llegó a la fecha_fin → 0
            if hoy >= fecha_finalizacion:
                return "0"

            dias = 0
            dia = hoy

            while dia <= fecha_finalizacion:
                if dia.weekday() < 5:  # lunes a viernes
                    dias += 1
                dia += timedelta(days=1)

            return str(dias)

        except Exception:
            return "0"

    def contar_empleados(self):
        try:
            conn = self.conectar_bd()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM usuarios;")
            total = cur.fetchone()[0]
            conn.close()
            return str(total)
        except Exception:
            return "0"

    def mostrar_vacaciones(self):
        try:
            # Si la ventana no existe o ya fue cerrada
            if not hasattr(self, 'ventana_vacaciones') or self.ventana_vacaciones is None or not self.ventana_vacaciones.winfo_exists():
                self.ventana_vacaciones = SolicitudVacaciones(self.root, self.usuario_actual)
            else:
                self.ventana_vacaciones.lift()  # Trae la ventana al frente
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el formulario de vacaciones:\n{e}")

    def mostrar_dashboard(self):
        try:
            import reportesusuario # o el archivo donde esté tu clase ReportesU
            reportesusuario.ReportesU(self.root, usuario_actual=self.usuario_actual)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema al abrir el reporte:\n{e}")

    def configuracion_dashboard(self):
        try:
            import editar_perfil
            editar_perfil.EditarPerfil(self.root, user_id=self.usuario_actual)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema al abrir la configuración:\n{e}")

    def volver_login(self):
        global MOSTRAR_BIENVENIDA
        MOSTRAR_BIENVENIDA = True

        # Ejecutar login solo una vez
        script_path = os.path.abspath("log.py")
        subprocess.Popen([sys.executable, script_path])

        # Cancelar after() si hay alguno
        try:
            self.root.after_cancel(self.after_cargar)
        except:
            pass
        try:
            self.root.after_cancel(self.after_actualizar)
        except:
            pass

        self.root.destroy()
        sys.exit()

    def mostrar_info_sistema(self):
        try:
            import PermisosDiasLaborales
            PermisosDiasLaborales.EditarP(self.root, user_id=self.usuario_actual)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema al abrir las solicitudes:\n{e}")
        
    def cargar_solicitudes(self):
        try:
            conn = self.conectar_bd()
            cur = conn.cursor()

            # Obtener el id del colaborador según el usuario_actual
            cur.execute("""
                SELECT id
                FROM colaborador
                WHERE usuario = %s
            """, (self.usuario_actual,))
            row = cur.fetchone()
            if not row:
                conn.close()
                return
            colaborador_id = row[0]

            # Permisos de días laborales del usuario_actual
            cur.execute("""
                SELECT p.id, c.identidad, 
                       CONCAT(c.nombre1, ' ', c.apellido1) AS nombre_usuario,
                       'Días Laborales' AS tipo,
                       c.cargo, c.dependencia,
                       p.fecha_entrega AS fecha, p.estado
                FROM permisos_dias_laborales p
                JOIN colaborador c ON p.colaborador_id = c.id
                WHERE p.colaborador_id = %s
                ORDER BY p.fecha_entrega DESC
            """, (colaborador_id,))
            permisos_dias = cur.fetchall()

            # Vacaciones del usuario_actual
            cur.execute("""
                SELECT v.id, c.identidad, 
                        CONCAT(c.nombre1, ' ', c.apellido1) AS nombre_usuario,
                        'Vacaciones' AS tipo,
                        c.cargo, c.dependencia,
                        v.fecha_inicio AS fecha, v.estado
                FROM vacaciones v
                JOIN colaborador c ON v.colaborador_id = c.id
                WHERE v.colaborador_id = %s
                ORDER BY v.fecha_inicio DESC
            """, (colaborador_id,))
            vacaciones = cur.fetchall()

            conn.close()

            # Limpiar tabla
            for item in self.tree.get_children():
                self.tree.delete(item)

            # ---- Insertar todas las filas correctamente ----
            for fila in permisos_dias + vacaciones:

                if len(fila) < 8:
                    continue

                estado = fila[7]

                if estado == "Aprobada":
                    tag = "aprobada"
                elif estado == "Rechazada":
                    tag = "rechazada"
                else:
                    tag = "pendiente"

                self.tree.insert("", "end", values=(
                    fila[0],   # id
                    fila[1],   # identidad
                    fila[2],   # usuario
                    fila[3],   # tipo
                    fila[4],   # cargo
                    fila[5],   # dependencia
                    fila[6],   # fecha
                    fila[7],   # estado
                    "👁️"
                ), tags=(tag,))

            # Configurar colores una sola vez
            self.tree.tag_configure("aprobada", background="#c8f7c5")   # verde
            self.tree.tag_configure("rechazada", background="#f7c5c5")  # rojo
            self.tree.tag_configure("pendiente", background="#fff4cc")  # amarillo

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema al cargar solicitudes: {e}")

    def ver_detalle_solicitud(self, event):
        # 1️⃣ Si ya hay una ventana abierta → no abrir otra
        if self.detalle_abierto and self.detalle_abierto.winfo_exists():
            self.detalle_abierto.lift()
            return

        item = self.tree.selection()
        if not item:
            return

        datos = self.tree.item(item, "values")

        # 2️⃣ Crear ventana única
        self.detalle_abierto = tk.Toplevel(self.root)
        detalle = self.detalle_abierto
        detalle.title(f"Solicitud #{datos[0]}")
        # Centrado automático
        detalle.update_idletasks()
        w = 420
        h = 380
        x = (detalle.winfo_screenwidth() // 2) - (w // 2)
        y = (detalle.winfo_screenheight() // 2) - (h // 2)
        detalle.geometry(f"{w}x{h}+{x}+{y}")

        ttk.Label(detalle, text=f"👤 Usuario: {datos[2]}", font=("Segoe UI", 11, "bold")).pack(pady=4)
        ttk.Label(detalle, text=f"🆔 Identidad: {datos[1]}", font=("Segoe UI", 10)).pack(pady=3)
        ttk.Label(detalle, text=f"💼 Cargo: {datos[4]}", font=("Segoe UI", 10)).pack(pady=3)
        ttk.Label(detalle, text=f"🏢 Dependencia: {datos[5]}", font=("Segoe UI", 10)).pack(pady=3)
        ttk.Label(detalle, text=f"📋 Tipo: {datos[3]}", font=("Segoe UI", 10)).pack(pady=3)
        if datos[3] == "Días Laborales":
            ttk.Label(detalle, text=f"📅 Fecha entrega: {datos[6]}", font=("Segoe UI", 10)).pack(pady=3)
         # Para ambos tipos
        ttk.Label(detalle, text=f"📅 Fecha inicio: {datos[6]}", font=("Segoe UI", 10)).pack(pady=3)
        ttk.Label(detalle, text=f"📅 Fecha fin: {datos[6]}", font=("Segoe UI", 10)).pack(pady=3)
        ttk.Label(detalle, text=f"🔖 Estado: {datos[7]}", font=("Segoe UI", 10, "bold")).pack(pady=8)

        # 3️⃣ Cuando la ventana se cierre → permitir abrir otra
        detalle.protocol("WM_DELETE_WINDOW", lambda: self.cerrar_detalle(detalle))

    def cerrar_detalle(self, ventana):
        ventana.destroy()
        self.detalle_abierto = None

    # ---------- NOTIFICACIÓN TIPO TOAST ----------
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

        def fade_in(alpha=0.0):
            if not self.toast.winfo_exists():
                return
            alpha += 0.05
            if alpha >= 1.0:
                if self.toast.winfo_exists():
                    self.toast.after(2000, fade_out)
                return
            self.toast.attributes("-alpha", alpha)
            self.toast.after(30, lambda: fade_in(alpha))

        def fade_out(alpha=1.0):
            if not self.toast.winfo_exists():
                return
            alpha -= 0.05
            if alpha <= 0.0:
                if self.toast.winfo_exists():
                    self.toast.destroy()
                return
            self.toast.attributes("-alpha", alpha)
            self.toast.after(30, lambda: fade_out(alpha))

        fade_in()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        usuario = sys.argv[1]
    else:
        usuario = "admin"

    root = tk.Tk()
    app = PantallaPrincipal(root, usuario_actual=usuario)
    root.mainloop()