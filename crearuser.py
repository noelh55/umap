import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import psycopg2
import os

# ---------- CONFIG BD ----------
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "database_umap"
DB_USER = "postgres"
DB_PASS = "umap"

# ---------- CONEXIÓN BD ----------
def conectar_bd():
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
        )
        return conn
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo conectar a la base de datos:\n{e}")
        return None

# ---------- CLASE PRINCIPAL ----------
class CrearUsuarioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Crear Usuario - UMAP")
        self.root.geometry("550x600")
        self.root.minsize(500, 550)
        self.root.configure(bg="#f4f6f9")

        self.foto_path = None  # Ruta de la foto seleccionada

        # --- Frame principal ---
        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="🧍 Registro de Nuevo Usuario", font=("Segoe UI", 16, "bold")).pack(pady=10)

        # --- Formulario ---
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill="both", expand=True, pady=10)
        form_frame.columnconfigure(0, weight=1)
        form_frame.columnconfigure(1, weight=2)

        # Variables
        self.usuario_var = tk.StringVar()
        self.contrasena_var = tk.StringVar()
        self.nombre_var = tk.StringVar()
        self.rol_var = tk.StringVar()
        self.unidad_var = tk.StringVar()

        # Usuario
        ttk.Label(form_frame, text="👤 Usuario *:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self.usuario_var).grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Contraseña
        ttk.Label(form_frame, text="🔑 Contraseña *:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.pass_entry = ttk.Entry(form_frame, textvariable=self.contrasena_var, show="*")
        self.pass_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Botón mostrar/ocultar contraseña
        self.mostrar_pass = False
        self.ojo_btn = tk.Button(form_frame, text="👁️", bd=0, command=self.toggle_contrasena)
        self.ojo_btn.grid(row=1, column=2, padx=5)

        # Nombre
        ttk.Label(form_frame, text="📛 Nombre completo *:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self.nombre_var).grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        # Rol
        ttk.Label(form_frame, text="⚙️ Rol *:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        ttk.Combobox(form_frame, textvariable=self.rol_var, values=["Administrador", "Usuario"], state="readonly").grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        # Unidad
        ttk.Label(form_frame, text="🏢 Unidad *:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self.unidad_var).grid(row=4, column=1, sticky="ew", padx=5, pady=5)

        # --- FOTO DE PERFIL ---
        ttk.Label(form_frame, text="📸 Foto:").grid(row=5, column=0, sticky="ne", padx=5, pady=5)

        self.foto_frame = tk.Frame(form_frame, width=150, height=150, bg="#e0e0e0", relief="ridge", bd=2)
        self.foto_frame.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        self.foto_frame.grid_propagate(False)

        self.foto_label = tk.Label(self.foto_frame, text="Toca para subir foto", bg="#e0e0e0", fg="gray")
        self.foto_label.place(relx=0.5, rely=0.5, anchor="center")
        self.foto_frame.bind("<Button-1>", self.seleccionar_foto)
        self.foto_label.bind("<Button-1>", self.seleccionar_foto)

        # --- Botones ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15, anchor="e")

        ttk.Button(btn_frame, text="💾 Crear", command=self.crear_usuario).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="🧹 Limpiar", command=self.limpiar_formulario).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", command=self.root.destroy).grid(row=0, column=2, padx=5)

    # -------- Mostrar / Ocultar contraseña --------
    def toggle_contrasena(self):
        if self.mostrar_pass:
            self.pass_entry.config(show="*")
            self.ojo_btn.config(text="👁️")
            self.mostrar_pass = False
        else:
            self.pass_entry.config(show="")
            self.ojo_btn.config(text="❌")
            self.mostrar_pass = True

    # -------- Seleccionar foto --------
    def seleccionar_foto(self, event=None):
        ruta = filedialog.askopenfilename(
            title="Seleccionar foto",
            filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png *.gif")]
        )
        if ruta:
            self.foto_path = ruta
            img = Image.open(ruta)
            img = img.resize((150, 150))
            self.user_img = ImageTk.PhotoImage(img)
            self.foto_label.config(image=self.user_img, text="")
            self.foto_label.image = self.user_img  # prevenir que se borre por garbage collector

    # -------- Crear usuario --------
    def crear_usuario(self):
        usuario = self.usuario_var.get().strip()
        contrasena = self.contrasena_var.get().strip()
        nombre = self.nombre_var.get().strip()
        rol = self.rol_var.get().strip()
        unidad = self.unidad_var.get().strip()
        foto = self.foto_path

        if not usuario or not contrasena or not nombre or not rol or not unidad:
            messagebox.showwarning("Campos vacíos", "❌ Todos los campos son obligatorios.")
            return

        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO usuarios (usuario, contrasena, nombre, rol, foto_path, unidad)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (usuario, contrasena, nombre, rol, foto, unidad))
                conn.commit()
                cur.close()
                conn.close()
                messagebox.showinfo("Éxito", "✅ Usuario creado correctamente.")
                self.limpiar_formulario()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear el usuario:\n{e}")

    # -------- Limpiar formulario --------
    def limpiar_formulario(self):
        self.usuario_var.set("")
        self.contrasena_var.set("")
        self.nombre_var.set("")
        self.rol_var.set("")
        self.unidad_var.set("")
        self.foto_path = None
        self.foto_label.config(image="", text="Toca para subir foto", fg="gray", bg="#e0e0e0")

# ---------- MAIN ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = CrearUsuarioApp(root)
    root.mainloop()