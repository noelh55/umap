# login_full_sin_remember.py
import sys
import os
import subprocess
import psycopg2
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# from cargo import VentanaCargo   # mantén si existe en tu proyecto

# ---------------- CONFIGURACIÓN BASE DE DATOS ----------------
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

# ---------------- FUNCIONES ----------------
def toast(root, text, duration=2500):
    """Toast flotante en la esquina superior derecha con animación slide-in"""
    toast_win = tk.Toplevel(root)
    toast_win.overrideredirect(True)
    toast_win.attributes("-topmost", True)
    toast_win.configure(bg="#e74c3c")  # fondo rojo

    # Crear etiqueta
    toast_label = tk.Label(
        toast_win,
        text=text,
        fg="white",
        bg="#e74c3c",
        font=("Segoe UI", 11, "bold"),
        anchor="w"
    )
    toast_label.pack(ipadx=20, ipady=10, fill="both")

    # Posición inicial: fuera de la pantalla (derecha)
    root.update_idletasks()
    toast_width = 300
    toast_height = 60
    screen_x = root.winfo_x() + root.winfo_width() - toast_width - 10
    screen_y = root.winfo_y() + 10
    start_x = root.winfo_x() + root.winfo_width() + toast_width  # fuera a la derecha

    toast_win.geometry(f"{toast_width}x{toast_height}+{start_x}+{screen_y}")
    toast_win.attributes("-alpha", 0.0)

    # Animación slide-in
    alpha = 0.0
    step_alpha = 0.08
    step_x = 20

    def slide_in():
        nonlocal start_x, alpha
        alpha += step_alpha
        start_x -= step_x
        if alpha > 1.0: alpha = 1.0
        if start_x <= screen_x:
            toast_win.geometry(f"{toast_width}x{toast_height}+{screen_x}+{screen_y}")
            toast_win.attributes("-alpha", 1.0)
            root.after(duration, slide_out)
        else:
            toast_win.geometry(f"{toast_width}x{toast_height}+{start_x}+{screen_y}")
            toast_win.attributes("-alpha", alpha)
            root.after(30, slide_in)

    def slide_out():
        nonlocal start_x, alpha
        start_x += step_x
        alpha -= step_alpha
        if alpha <= 0:
            toast_win.destroy()
        else:
            toast_win.geometry(f"{toast_width}x{toast_height}+{start_x}+{screen_y}")
            toast_win.attributes("-alpha", alpha)
            root.after(30, slide_out)

    slide_in()

# ---------------- LOGIN APP ----------------
class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Municipal")
        # start hidden (for fade-in)
        self.root.attributes("-alpha", 0.0)
        try:
            self.root.attributes("-fullscreen", True)
        except Exception:
            pass
        self.root.geometry("500x500")
        self.root.resizable(False, False)
        self.mostrar_contrasena = False
        self._after_check_id = None

        # --- FONDO ---
        try:
            self.bg_image = Image.open("fondo.jpg")
            self.bg_image = self.bg_image.resize((root.winfo_screenwidth(), root.winfo_screenheight()))
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.bg_label = tk.Label(root, image=self.bg_photo)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception:
            self.bg_label = tk.Label(root, bg="#f0f2f5")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # --- FRAME PRINCIPAL ---
        self.main_frame = tk.Frame(root, bg="", bd=0)
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        # =============================================================
        # CARD IZQUIERDA (LOGO)
        # =============================================================
        self.info_canvas = tk.Canvas(self.main_frame, width=420, height=460, bg="#e8eef7", highlightthickness=0)
        self.info_canvas.grid(row=0, column=0, padx=0)
        self.round_rectangle(self.info_canvas, 10, 10, 410, 450, radius=35, fill="#ffffff", outline="#cfd9e3", width=2)

        self.info_frame = tk.Frame(self.info_canvas, bg="#ffffff")
        self.info_frame.place(x=0, y=0, width=420, height=460)
        try:
            self.logo_muni_img = Image.open("muni.jpg").resize((240, 240))
            self.logo_muni = ImageTk.PhotoImage(self.logo_muni_img)
            self.logo_muni_label = tk.Label(self.info_frame, image=self.logo_muni, bg="#ffffff")
            self.logo_muni_label.place(relx=0.5, rely=0.5, anchor="center")
        except Exception:
            self.logo_muni_label = tk.Label(self.info_frame, text="LOGO", bg="#ffffff", font=("Segoe UI", 20, "bold"))
            self.logo_muni_label.place(relx=0.5, rely=0.5, anchor="center")

        # =============================================================
        # CARD DERECHA (LOGIN)
        # =============================================================
        self.card_canvas = tk.Canvas(self.main_frame, width=420, height=460, bg="#dce6f9", highlightthickness=0)
        self.card_canvas.grid(row=0, column=1, padx=0)
        self.round_rectangle(self.card_canvas, 10, 10, 410, 450, radius=35, fill="#eef3fb", outline="#c5d3f0", width=2)

        self.card_frame = tk.Frame(self.card_canvas, bg="#eef3fb")
        self.card_frame.place(x=0, y=0, width=420, height=460)

        # --- TÍTULO LOGIN ---
        self.title_label = tk.Label(self.card_frame, text="SISTEMA MUNICIPAL", font=("Segoe UI", 18, "bold"), bg="#eef3fb", fg="#2c3e50")
        self.title_label.pack(pady=(25, 15))

        # --- FOTO USUARIO ---
        self.user_image_label = tk.Label(self.card_frame, bg="#eef3fb")
        self.user_image_label.pack(pady=(5, 10))
        self.user_photo = None
        self.load_default_user_photo()

        # --- CAMPOS ---
        self.usuario_entry = tk.Entry(self.card_frame, font=("Segoe UI", 12), fg="#7f8c8d")
        self.usuario_entry.pack(pady=6, fill="x", padx=60)
        self.usuario_entry.insert(0, "Ingrese usuario")
        self.usuario_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(self.usuario_entry, "Ingrese usuario"))
        self.usuario_entry.bind("<FocusOut>", lambda e: self.restore_placeholder(self.usuario_entry, "Ingrese usuario"))
        self.usuario_entry.bind("<KeyRelease>", lambda e: self.verificar_campos())
        self.usuario_entry.bind("<Return>", lambda e: self.contrasena_entry.focus_set())

        pass_frame = tk.Frame(self.card_frame, bg="#eef3fb")
        pass_frame.pack(fill="x", padx=60, pady=(6,0))
        self.contrasena_entry = tk.Entry(pass_frame, font=("Segoe UI", 12), fg="#7f8c8d", show="")
        self.contrasena_entry.pack(side="left", fill="x", expand=True)
        self.contrasena_entry.insert(0, "Ingrese contraseña")
        self.contrasena_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(self.contrasena_entry, "Ingrese contraseña", True))
        self.contrasena_entry.bind("<FocusOut>", lambda e: self.restore_placeholder(self.contrasena_entry, "Ingrese contraseña", True))
        self.contrasena_entry.bind("<KeyRelease>", lambda e: self.verificar_campos())
        self.contrasena_entry.bind("<Return>", lambda e: self.login_btn.focus_set())

        self.show_pass_btn = tk.Button(pass_frame, text="👁", relief="flat", bg="#eef3fb", command=self.toggle_password_visible)
        self.show_pass_btn.pack(side="left", padx=(6,0))

        # --- MENSAJE ---
        self.msg_label = tk.Label(self.card_frame, text="", fg="red", bg="#eef3fb", font=("Segoe UI", 10, "bold"))
        self.msg_label.pack(pady=(5, 0))

        # --- BOTÓN LOGIN ---
        self.login_btn = tk.Button(self.card_frame, text="Iniciar Sesión", bg="#74aceb", fg="white",
                                   font=("Segoe UI", 12, "bold"), bd=0, height=2, command=self.iniciar_sesion,
                                   relief="flat", highlightthickness=0, width=15)
        self.login_btn.place(relx=0.5, y=370, anchor="center")
        self.login_btn.bind("<Return>", lambda e: self.iniciar_sesion())

        # --- BOTÓN SALIR ---
        self.salir_label = tk.Label(self.card_frame, text="Salir", fg="#555555", bg="#eef3fb",
                                    font=("Segoe UI", 9, "underline"), cursor="hand2")
        self.salir_label.place(relx=0.5, y=415, anchor="center")
        self.salir_label.bind("<Button-1>", lambda e: self.root.destroy())

        self.root.bind("<Escape>", lambda e: root.destroy())
        self._fade_in_alpha = 0.0
        self._do_fade_in()
        if os.path.exists("logout_flag.txt"):
            try:
                u = open("logout_flag.txt").read().strip()
                toast(self.root, f"{u} cerró sesión")
            except:
                pass
            os.remove("logout_flag.txt")

    # ---------------- fade-in ----------------
    def _do_fade_in(self):
        try:
            self._fade_in_alpha += 0.08
            if self._fade_in_alpha >= 1.0:
                self.root.attributes("-alpha", 1.0)
                return
            self.root.attributes("-alpha", self._fade_in_alpha)
            self.root.after(25, self._do_fade_in)
        except Exception:
            pass

    # ---------------- RECTÁNGULO REDONDEADO ----------------
    def round_rectangle(self, canvas, x1, y1, x2, y2, radius=40, **kwargs):
        points = [x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
                  x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2,
                  x1, y2, x1, y2-radius, x1, y1+radius, x1, y1]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    def clear_placeholder(self, entry, text, is_password=False):
        if entry.get() == text:
            entry.delete(0, tk.END)
            entry.config(fg="#2c3e50")
            if is_password:
                entry.config(show="*")

    def restore_placeholder(self, entry, text, is_password=False):
        if not entry.get():
            entry.insert(0, text)
            entry.config(fg="#7f8c8d")
            if is_password:
                entry.config(show="")

    def toggle_password_visible(self):
        current = self.contrasena_entry.cget("show")
        if current == "":
            self.contrasena_entry.config(show="*")
            self.show_pass_btn.config(text="👁")
        else:
            if self.contrasena_entry.get() == "Ingrese contraseña":
                return
            self.contrasena_entry.config(show="")
            self.show_pass_btn.config(text="🚫")

    # ---------------- FOTO ----------------
    def load_default_user_photo(self):
        default_img = Image.new("RGBA", (100, 100), "#bdc3c7")
        mask = Image.new("L", (100, 100), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 100, 100), fill=255)
        default_img.putalpha(mask)
        circle_img = ImageTk.PhotoImage(default_img)
        self.user_image_label.config(image=circle_img)
        self.user_image_label.image = circle_img

    def load_user_photo(self, username):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT foto_path FROM usuarios WHERE usuario = %s", (username,))
            result = cur.fetchone()
            if not result:
                cur.execute("SELECT foto_path FROM colaborador WHERE usuario = %s", (username,))
                result = cur.fetchone()
            conn.close()
            if result and result[0] and os.path.exists(result[0]):
                img = Image.open(result[0]).resize((100, 100))
                mask = Image.new("L", (100, 100), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, 100, 100), fill=255)
                img.putalpha(mask)
                circle_img = ImageTk.PhotoImage(img)
                self.user_image_label.config(image=circle_img)
                self.user_image_label.image = circle_img
            else:
                self.load_default_user_photo()
        except Exception as e:
            print("Error cargando foto desde la base de datos:", e)
            self.load_default_user_photo()

    # ---------------- Verificación de campos ----------------
    def verificar_campos(self):
        self.msg_label.config(text="")
        usuario = self.usuario_entry.get().strip()
        contrasena = self.contrasena_entry.get().strip()
        placeholder_user = usuario == "Ingrese usuario" or usuario == ""
        placeholder_pass = contrasena == "Ingrese contraseña" or contrasena == ""

        if self._after_check_id:
            try:
                self.card_frame.after_cancel(self._after_check_id)
            except Exception:
                pass
            self._after_check_id = None

        if not placeholder_user and not placeholder_pass:
            self._after_check_id = self.card_frame.after(100, self._check_credentials_for_photo)
        else:
            self.load_default_user_photo()

    def _check_credentials_for_photo(self):
        usuario = self.usuario_entry.get().strip()
        contrasena = self.contrasena_entry.get().strip()
        if not usuario or not contrasena:
            self.load_default_user_photo()
            return

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT contrasena FROM usuarios WHERE usuario = %s", (usuario,))
            row = cur.fetchone()
            if row and contrasena == row[0]:
                conn.close()
                self.load_user_photo(usuario)
                return
            cur.execute("SELECT contrasena FROM colaborador WHERE usuario = %s", (usuario,))
            row2 = cur.fetchone()
            conn.close()
            if row2 and contrasena == row2[0]:
                self.load_user_photo(usuario)
                return
            self.load_default_user_photo()
        except Exception:
            self.load_default_user_photo()

    # ---------------- LOGIN ----------------
    def _get_role_for_user(self, usuario):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT rol FROM usuarios WHERE usuario = %s", (usuario,))
            r = cur.fetchone()
            if r and r[0]:
                conn.close()
                return r[0]
            cur.execute("SELECT rol FROM colaborador WHERE usuario = %s", (usuario,))
            r2 = cur.fetchone()
            conn.close()
            if r2 and r2[0]:
                return r2[0]
        except Exception:
            pass
        return None

    def iniciar_sesion(self):
        usuario = self.usuario_entry.get().strip()
        contrasena = self.contrasena_entry.get().strip()

        if not usuario or not contrasena or usuario == "Ingrese usuario" or contrasena == "Ingrese contraseña":
            self.mostrar_mensaje("❌ Debe completar Usuario y Contraseña")
            return

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT usuario, contrasena, nombre, rol, foto_path FROM usuarios WHERE usuario = %s", (usuario,))
            user = cur.fetchone()
            if not user:
                cur.execute("SELECT usuario, contrasena, nombre1, nombre2, apellido1, apellido2, rol, foto_path FROM colaborador WHERE LOWER(usuario) = LOWER(%s)", (usuario,))
                userc = cur.fetchone()
                if userc:
                    db_usuario = userc[0]
                    db_contrasena = userc[1]
                    nombre1 = userc[2] or ""
                    nombre2 = userc[3] or ""
                    apellido1 = userc[4] or ""
                    apellido2 = userc[5] or ""
                    nombre = " ".join([p for p in [nombre1, nombre2, apellido1, apellido2] if p]).strip()
                    rol = userc[6] if len(userc) > 6 else None
                    foto_path = userc[7] if len(userc) > 7 else None
                    user = (db_usuario, db_contrasena, nombre, rol, foto_path)
            conn.close()

            if not user:
                # Mostrar mensaje en label (rojo)
                self.mostrar_mensaje("❌ Usuario no encontrado")
    
                # Mostrar toast flotante bonito
                toast(self.root, "Usuario no encontrado")
    
                return

            db_usuario, db_contrasena, nombre, rol, foto_path = user

            if usuario and db_contrasena == contrasena:
                self.root.destroy()
                usuario_safe = usuario.strip()
                if rol and rol.lower() == "administrador":
                    subprocess.Popen([sys.executable, "Main.py", usuario_safe])
                    print(usuario)
                else:
                    subprocess.Popen([sys.executable, "Main1.py", usuario_safe])
                sys.exit()
            else:
                self.mostrar_mensaje("❌ Contraseña incorrecta")
                return

        except Exception as e:
            self.mostrar_mensaje(f"Error de conexión: {e}")

    def mostrar_mensaje(self, msg):
        self.msg_label.config(text=msg)
        self.msg_label.after(3000, lambda: self.msg_label.config(text=""))

# ---------------- RUN ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()