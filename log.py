import sys
import os
import subprocess
import psycopg2
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cargo import VentanaCargo

# ---------------- CONFIGURACIÓN BASE DE DATOS ----------------
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

REMEMBER_FILE = "remember.txt"

# ---------------- FUNCIONES ----------------
def toast(root, text):
    toast_win = tk.Toplevel(root)
    toast_win.overrideredirect(True)
    toast_win.configure(bg="#333333")
    toast_win.attributes("-topmost", True)
    toast_label = tk.Label(toast_win, text=text, fg="white", bg="#333333", font=("Arial", 12))
    toast_label.pack(ipadx=10, ipady=5)
    x = root.winfo_x() + root.winfo_width() // 2 - 100
    y = root.winfo_y() + root.winfo_height() // 2 - 50
    toast_win.geometry(f"200x50+{x}+{y}")
    toast_win.after(2000, toast_win.destroy)

# ---------------- LOGIN APP ----------------
class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Municipal")
        self.root.attributes("-fullscreen", True)
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        self.mostrar_contrasena = False

        # --- FONDO ---
        self.bg_image = Image.open("fondo.jpg")
        self.bg_image = self.bg_image.resize((root.winfo_screenwidth(), root.winfo_screenheight()))
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = tk.Label(root, image=self.bg_photo)
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
        self.logo_muni_img = Image.open("muni.jpg").resize((240, 240))
        self.logo_muni = ImageTk.PhotoImage(self.logo_muni_img)
        self.logo_muni_label = tk.Label(self.info_frame, image=self.logo_muni, bg="#ffffff")
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
        self.user_image_label.pack(pady=(5, 20))
        self.user_photo = None
        self.load_default_user_photo()

        # --- CAMPOS ---
        self.usuario_entry = tk.Entry(self.card_frame, font=("Arial", 12), fg="#7f8c8d")
        self.usuario_entry.pack(pady=10, fill="x", padx=60)
        self.usuario_entry.insert(0, "Ingrese usuario")
        self.usuario_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(self.usuario_entry, "Ingrese usuario"))
        self.usuario_entry.bind("<FocusOut>", lambda e: self.restore_placeholder(self.usuario_entry, "Ingrese usuario"))
        self.usuario_entry.bind("<KeyRelease>", lambda e: self.verificar_campos())

        self.contrasena_entry = tk.Entry(self.card_frame, font=("Arial", 12), fg="#7f8c8d")
        self.contrasena_entry.pack(pady=10, fill="x", padx=60)
        self.contrasena_entry.insert(0, "Ingrese contraseña")
        self.contrasena_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(self.contrasena_entry, "Ingrese contraseña", True))
        self.contrasena_entry.bind("<FocusOut>", lambda e: self.restore_placeholder(self.contrasena_entry, "Ingrese contraseña", True))
        self.contrasena_entry.bind("<KeyRelease>", lambda e: self.verificar_campos())

        # --- RECORDARME ---
        self.remember_check = tk.Checkbutton(self.card_frame, text="Recordarme", bg="#eef3fb", font=("Arial", 9))
        self.remember_check.pack(pady=(5, 5))

        # --- MENSAJE ---
        self.msg_label = tk.Label(self.card_frame, text="", fg="red", bg="#eef3fb", font=("Arial", 9))
        self.msg_label.pack(pady=(5, 0))

        # --- BOTÓN LOGIN ---
        self.login_btn = tk.Button(self.card_frame, text="Iniciar Sesión", bg="#74aceb", fg="white",
                                   font=("Arial", 12, "bold"), bd=0, height=2, command=self.iniciar_sesion,
                                   relief="flat", highlightthickness=0, width=15)
        self.login_btn.place(relx=0.5, y=370, anchor="center")

        # --- BOTÓN SALIR ---
        self.salir_label = tk.Label(self.card_frame, text="Salir", fg="#555555", bg="#eef3fb",
                                    font=("Arial", 9, "underline"), cursor="hand2")
        self.salir_label.place(relx=0.5, y=415, anchor="center")
        self.salir_label.bind("<Button-1>", lambda e: self.root.destroy())

        # Cargar usuario recordado
        if os.path.exists(REMEMBER_FILE):
            try:
                with open(REMEMBER_FILE, "r") as f:
                    remembered_user = f.read().strip()
                    if remembered_user:
                        self.usuario_entry.delete(0, tk.END)
                        self.usuario_entry.insert(0, remembered_user)
                        self.remember_check.select()
                        self.load_user_photo(remembered_user)
            except:
                pass

        self.root.bind("<Escape>", lambda e: root.destroy())

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

    def load_default_user_photo(self):
        default_img = Image.new("RGB", (100, 100), "#bdc3c7")
        mask = Image.new("L", (100, 100), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 100, 100), fill=255)
        default_img.putalpha(mask)
        circle_img = ImageTk.PhotoImage(default_img)
        self.user_image_label.config(image=circle_img)
        self.user_image_label.image = circle_img

    def mostrar_mensaje(self, texto):
        self.msg_label.config(text=texto)
        self.msg_label.after(5000, lambda: self.msg_label.config(text=""))

    def load_user_photo(self, username):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT foto_path FROM usuarios WHERE usuario = %s", (username,))
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

    def verificar_campos(self):
        usuario = self.usuario_entry.get().strip()
        contrasena = self.contrasena_entry.get().strip()
        if usuario and contrasena and usuario != "Ingrese usuario" and contrasena != "Ingrese contraseña":
            self.load_user_photo(usuario)
        else:
            self.load_default_user_photo()

    # ---------------- LOGIN ----------------
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
            conn.close()

            if not user:
                self.mostrar_mensaje("❌ Usuario no encontrado")
                return

            db_usuario, db_contrasena, nombre, rol, foto_path = user

            # Verificar contraseña **sin bcrypt**
            if contrasena == db_contrasena:
                if self.remember_check.select():
                    with open(REMEMBER_FILE, "w") as f:
                        f.write(usuario)
                self.root.destroy()
                if rol.lower() == "administrador":
                    subprocess.Popen([sys.executable, "Main.py", usuario])
                else:
                    subprocess.Popen([sys.executable, "Main1.py", usuario])
                sys.exit()
            else:
                self.mostrar_mensaje("❌ Contraseña incorrecta")

        except Exception as e:
            self.mostrar_mensaje(f"Error de conexión: {e}")

# ---------------- RUN ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()