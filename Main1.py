import sys
import psycopg2
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cargo import VentanaCargo
import subprocess
from datetime import date, timedelta
from crearuser import CrearUsuarioApp
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
        password="umap"
    )

# ============================================================
# CLASE PRINCIPAL DE PANEL DE USUARIO
# ============================================================
class PantallaPrincipal:
    def __init__(self, root, usuario_actual, mostrar_toast_bienvenida=True):
        global MOSTRAR_BIENVENIDA

        self.root = root
        self.usuario_actual = usuario_actual
        self.mostrar_toast_bienvenida = mostrar_toast_bienvenida and MOSTRAR_BIENVENIDA

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

    # ============================================================
    # PANEL PRINCIPAL
    # ============================================================
    def crear_panel_principal(self):
        self.panel_principal = tk.Frame(self.root, bg=BG)
        self.panel_principal.pack(fill="both", expand=True, side="right")

        # --- Encabezado superior (ligeramente más bajo) ---
        header_frame = tk.Frame(self.panel_principal, bg=PANEL, height=100, bd=0, relief="flat")
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

        # ---------- CUADROS SUPERIORES (más abajo y con espacio extra) ----------
        cuadros_data = [
            ("📅 Dias Trabajados", "40", "#1abc9c"),
            ("🏖️ Dias Gozar", "10", "#3498db"),
            ("🕒 Dias Pendientes", self.calcular_dias_contrato(), "#e67e22"),
            ("👥 Dias Restantes", self.contar_empleados(), "#9b59b6"),
        ]

        cuadros_frame = tk.Frame(container, bg=BG)
        cuadros_frame.pack(fill="x", pady=(30, 20))  # Más separado del encabezado
        cuadros_frame.grid_columnconfigure((0,1,2,3), weight=1)

        for i, (titulo, valor, color) in enumerate(cuadros_data):
            frame = tk.Frame(cuadros_frame, bg=color, height=100, width=200)
            frame.grid(row=0, column=i, padx=8, sticky="nsew")
            frame.pack_propagate(False)

            tk.Label(frame, text=titulo, bg=color, fg="white",
                     font=("Segoe UI", 11, "bold")).pack(pady=(8,0))
            tk.Label(frame, text=valor, bg=color, fg="white",
                     font=("Segoe UI", 20, "bold")).pack(pady=(3,8))

        # --- Panel de solicitudes (más separado de los cuadros) ---
        solicitudes_frame = ttk.LabelFrame(container, text="Solicitudes", padding=10)
        solicitudes_frame.pack(fill="x", expand=False, pady=(20, 30))  # Mayor separación

        tabla_frame = ttk.Frame(solicitudes_frame)
        tabla_frame.pack(fill="x", padx=5, pady=5, expand=False)

        columnas = ("id", "usuario", "tipo", "fecha", "descripcion", "estado", "ver")
        encabezados = ["ID", "Usuario", "Tipo Solicitud", "Fecha", "Descripción", "Estado", "👁️"]

        self.tree = ttk.Treeview(tabla_frame, columns=columnas, show="headings", height=8)
        for col, texto in zip(columnas, encabezados):
            self.tree.heading(col, text=texto)
            self.tree.column(col, anchor="center", width=130)
        self.tree.column("descripcion", width=250)
        self.tree.column("ver", width=50)

        vsb = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        tabla_frame.columnconfigure(0, weight=1)
        tabla_frame.rowconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.ver_detalle_solicitud)

        # ---------- GRÁFICOS (más altos y bien distribuidos) ----------
        graficos_container = tk.Frame(container, bg=BG)
        graficos_container.pack(fill="x", pady=(10, 10))  # Subido y con espacio uniforme

        datos_graficos = [
            ("Dias Trabajados", int(cuadros_data[0][1])),
            ("Dias Gozados", int(cuadros_data[1][1])),
            ("Dias Pendientes", int(cuadros_data[2][1])),
            ("Dias Restantes", int(cuadros_data[3][1]))
        ]

        colores_graficos = ["#1abc9c", "#3498db", "#e67e22", "#9b59b6"]

        for i, (titulo, valor) in enumerate(datos_graficos):
            frame = tk.Frame(graficos_container, bg=BG, width=200, height=140)  # Más alto
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
        self.panel_lateral = tk.Frame(self.root, bg=PANEL, width=300, bd=0, relief="flat")
        self.panel_lateral.pack(side="left", fill="y")
        self.panel_lateral.pack_propagate(False)

        foto_path = self.usuario_info.get("foto_path")
        if foto_path and os.path.exists(foto_path):
            img = Image.open(foto_path).resize((160, 160), Image.LANCZOS)
            self.foto_img = ImageTk.PhotoImage(img)
            foto_frame = tk.Frame(self.panel_lateral, bg=PANEL)
            foto_frame.pack(pady=(40, 20))
            tk.Label(foto_frame, image=self.foto_img, bg=PANEL, bd=3, relief="solid").pack()

        tk.Label(
            self.panel_lateral,
            text=self.usuario_info.get("nombre", "Usuario"),
            font=("Segoe UI", 11, "bold"),
            bg=PANEL,
            fg="white"
        ).pack()
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
            ("📊 Configuracion", self.configuracion_dashboard),
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
            cur.execute("SELECT COUNT(*) FROM usuarios;")
            total = cur.fetchone()[0]
            conn.close()
            return str(total)
        except Exception:
            return "0"

    def mostrar_vacaciones(self):
        messagebox.showinfo("Vacaciones", "Aquí se mostrarán las vacaciones del colaborador.")

    def mostrar_dashboard(self):
        messagebox.showinfo("Reportes", "Aquí se mostrará el Formulario de Reportes")

    def configuracion_dashboard(self):
        try:
            # Abrir el formulario editar_perfil.py como ventana flotante
            import editar_perfil
            editar_perfil.EditarPerfil(self.root, user_id=self.usuario_actual)
            # No se necesita nuevo_root.mainloop(), el Toplevel maneja la ventana flotante
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema al abrir la configuración:\n{e}")


    def volver_login(self):
        global MOSTRAR_BIENVENIDA
        MOSTRAR_BIENVENIDA = True
        script_path = os.path.abspath("log.py")
        subprocess.Popen([sys.executable, script_path])
        self.root.destroy()
        sys.exit()

    def mostrar_info_sistema(self):
        messagebox.showinfo("Ausencias", "Aquí se mostrará el Formulario de Ausencias")

    def ver_detalle_solicitud(self, event):
        item = self.tree.selection()
        if not item:
            return
        datos = self.tree.item(item, "values")
        detalle = tk.Toplevel(self.root)
        detalle.title(f"Solicitud #{datos[0]}")
        detalle.geometry("400x300")

        ttk.Label(detalle, text=f"👤 Usuario: {datos[1]}", font=("Segoe UI", 11)).pack(pady=5)
        ttk.Label(detalle, text=f"📋 Tipo: {datos[2]}", font=("Segoe UI", 11)).pack(pady=5)
        ttk.Label(detalle, text=f"📅 Fecha: {datos[3]}", font=("Segoe UI", 11)).pack(pady=5)
        ttk.Label(detalle, text=f"📝 Descripción:", font=("Segoe UI", 11, "bold")).pack(pady=5)
        tk.Message(detalle, text=datos[4], width=350).pack(pady=5)
        ttk.Label(detalle, text=f"🔖 Estado: {datos[5]}", font=("Segoe UI", 11)).pack(pady=10)

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

# ============================================================
# MAIN PRINCIPAL
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        usuario = sys.argv[1]
    else:
        usuario = "admin"

    root = tk.Tk()
    app = PantallaPrincipal(root, usuario_actual=usuario)
    root.mainloop()