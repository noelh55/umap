import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw
import psycopg2
import psycopg2.extras
import io
import os
import sys
import subprocess

# ---------------- CONFIGURACIÓN BASE DE DATOS ----------------
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

# ---------------- VENTANA EDITAR PERFIL ----------------
class EditarPerfil(tk.Toplevel):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.master = master
        self.user_id = user_id
        self.title("Perfil de Usuario")
        self.geometry("520x700")
        self.resizable(False, False)
        self.configure(bg="#ecf0f1")

        # ✅ Ventana flotante
        self.transient(master)
        self.grab_set()
        self.focus_set()
        self.lift()

        self.foto_path_actual = None
        self.foto_img = None  # 🔹 Guardará la imagen en memoria

        # Centrar ventana
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (520 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"520x700+{x}+{y}")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#ecf0f1", foreground="#2c3e50", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#2c3e50")
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6, relief="flat")
        style.configure("TEntry", font=("Segoe UI", 10))

        self.frame = tk.Frame(self, bg="#ffffff", bd=2, relief="flat")
        self.frame.pack(fill="both", expand=True, padx=16, pady=16)

        label = ttk.Label(self.frame, text="Perfil de Usuario", style="Header.TLabel")
        label.pack(pady=(10, 6))

        self.foto_frame = tk.Frame(self.frame, width=150, height=150, bg="#e0e0e0", relief="ridge", bd=2)
        self.foto_frame.pack(pady=(5, 15))
        self.foto_frame.pack_propagate(False)

        self.foto_label = tk.Label(self.foto_frame, text="📷 Foto Usuario", bg="#e0e0e0", fg="gray")
        self.foto_label.place(relx=0.5, rely=0.5, anchor="center")

        datos = tk.Frame(self.frame, bg="#ffffff")
        datos.pack(fill="both", expand=True, padx=6, pady=4)

        self.fields = {}
        labels = [
            ("Usuario", "usuario"),
            ("Contraseña", "contrasena"),
            ("Nombre 1", "nombre"),
            ("Nombre 2", "nombre2"),
            ("Apellido 1", "apellido1"),
            ("Apellido 2", "apellido2"),
            ("Rol", "rol"),
            ("Unidad", "unidad")
        ]

        for i, (lbl, key) in enumerate(labels):
            tk.Label(datos, text=lbl + ":", bg="#ffffff", anchor="w").grid(row=i, column=0, sticky="w", pady=8, padx=(4, 8))
            ent = ttk.Entry(datos, state="disabled", width=28)
            ent.grid(row=i, column=1, sticky="ew", padx=(0, 6), ipady=5)
            datos.columnconfigure(1, weight=1)
            self.fields[key] = ent

        self.lbl_estado = tk.Label(self.frame, text="", bg="#ffffff", fg="#2c3e50", font=("Segoe UI", 9, "italic"))
        self.lbl_estado.pack(anchor="w", padx=8, pady=(8, 0))

        btn_frame = tk.Frame(self.frame, bg="#ffffff")
        btn_frame.pack(fill="x", pady=12, padx=4)

        self.btn_solicitar = tk.Button(
            btn_frame, text="📨 Solicitar Actualización", bg="#3498db", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", command=self.solicitar_actualizacion
        )
        self.btn_solicitar.pack(side="left", expand=True, fill="x", padx=6, ipadx=4, ipady=6)

        self.btn_actualizar = tk.Button(
            btn_frame, text="💾 Actualizar", bg="#1abc9c", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", command=self.actualizar, state="disabled"
        )
        self.btn_actualizar.pack(side="left", expand=True, fill="x", padx=6, ipadx=4, ipady=6)

        self.btn_cerrar = tk.Button(
            btn_frame, text="❌ Cerrar", bg="#e74c3c", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", command=self.destroy
        )
        self.btn_cerrar.pack(side="left", expand=True, fill="x", padx=6, ipadx=4, ipady=6)

        self.init_db()
        self.load_user()

    # ---------------- FUNCIONES BD ----------------
    def init_db(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo conectar a la base de datos:\n{e}")

    def load_user(self):
        """Carga datos del usuario y su estado editable."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            if str(self.user_id).isdigit():
                cur.execute("SELECT * FROM usuarios WHERE id = %s", (int(self.user_id),))
            else:
                cur.execute("SELECT * FROM usuarios WHERE usuario = %s", (self.user_id,))

            row = cur.fetchone()
            cur.close()
            conn.close()

            if not row:
                messagebox.showerror("Error", f"Usuario '{self.user_id}' no encontrado.")
                self.destroy()
                return

            for key in self.fields:
                self.fields[key].config(state="normal")
                self.fields[key].delete(0, tk.END)
                self.fields[key].insert(0, row.get(key, ""))
                self.fields[key].config(state="disabled")

            # 🔹 Mostrar la foto si existe (desde foto_path)
            if "foto_path" in row and row["foto_path"]:
                try:
                    if os.path.exists(row["foto_path"]):
                        with open(row["foto_path"], "rb") as f:
                            self.mostrar_foto(f.read())
                except Exception as e:
                    print(f"⚠ No se pudo mostrar la foto: {e}")


            # 🔹 Verificar si está editable
            if "editable" in row and row["editable"]:
                self.habilitar_edicion()
            else:
                self.lbl_estado.config(text="Los datos están bloqueados. Solicite actualización.", fg="#2c3e50")
                self.btn_actualizar.config(state="disabled")
                self.btn_solicitar.config(state="normal")

        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo cargar el perfil:\n{e}")

    # ---------------- MOSTRAR FOTO ----------------
    def mostrar_foto(self, foto_bytes):
        """Muestra la foto circular del usuario desde la base de datos."""
        try:
            image = Image.open(io.BytesIO(foto_bytes)).convert("RGB")
            image = image.resize((150, 150), Image.LANCZOS)

            # 🔹 Crear máscara circular
            mask = Image.new("L", (150, 150), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 150, 150), fill=255)

            result = Image.new("RGBA", (150, 150))
            result.paste(image, (0, 0), mask=mask)

            self.foto_img = ImageTk.PhotoImage(result)
            self.foto_label.config(image=self.foto_img, text="")
        except Exception as e:
            print(f"Error al mostrar foto: {e}")

    def solicitar_actualizacion(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("INSERT INTO solicitudes_actualizacion (usuario, estado) VALUES (%s, %s)", (self.user_id, 'pendiente'))
            cur.execute("UPDATE usuarios SET editable = FALSE WHERE usuario = %s", (self.user_id,))
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo("Solicitud enviada", "Se ha enviado la solicitud al administrador.")
            self.lbl_estado.config(text="Solicitud pendiente de aprobación.", fg="#f39c12")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo enviar la solicitud:\n{e}")

    def habilitar_edicion(self):
        for ent in self.fields.values():
            ent.config(state="normal")
        self.btn_actualizar.config(state="normal")
        self.lbl_estado.config(text="Edite los datos y presione Actualizar.", fg="#16a085")

    def actualizar(self):
        try:
            datos = {k: v.get().strip() for k, v in self.fields.items()}
            if not datos["usuario"] or not datos["nombre"]:
                messagebox.showwarning("Atención", "Usuario y Nombre 1 son obligatorios.")
                return
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                UPDATE usuarios
                SET usuario = %s, contrasena = %s, nombre = %s, nombre2 = %s,
                    apellido1 = %s, apellido2 = %s, rol = %s, unidad = %s, editable = FALSE
                WHERE usuario = %s
            """, (datos["usuario"], datos["contrasena"], datos["nombre"], datos["nombre2"],
                  datos["apellido1"], datos["apellido2"], datos["rol"], datos["unidad"], self.user_id))
            conn.commit()
            cur.close()
            conn.close()

            self.btn_actualizar.config(state="disabled")
            self.btn_solicitar.config(state="disabled")
            self.lbl_estado.config(text="Perfil actualizado correctamente.", fg="#27ae60")
            self.toast("Perfil actualizado correctamente.", 2200)

        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo actualizar el perfil:\n{e}")

    def toast(self, text, duration=2000):
        try:
            toast = tk.Toplevel(self.master)
            toast.overrideredirect(True)
            toast.attributes("-topmost", True)
            frm = tk.Frame(toast, bg="#333333")
            frm.pack(fill="both", expand=True)
            tk.Label(frm, text=text, bg="#333333", fg="white", font=("Segoe UI", 9)).pack(padx=12, pady=8)
            toast.update_idletasks()
            x = toast.winfo_screenwidth() - 220
            y = toast.winfo_screenheight() - 80
            toast.geometry(f"+{x}+{y}")
            toast.after(duration, toast.destroy)
        except Exception:
            messagebox.showinfo("Info", text)

# ---------------- EJEMPLO DE USO ----------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    user_id_test = "noel"
    try:
        EditarPerfil(root, user_id=user_id_test)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el formulario:\n{e}")