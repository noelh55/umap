import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import psycopg2
import psycopg2.extras
import io
import os

# ---------------- CONFIGURACIÓN BASE DE DATOS ----------------
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

# ---------------- FORMULARIO EDITAR PERFIL ----------------
class EditarP(tk.Toplevel):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.master = master
        self.user_id = user_id
        self.title("Editar Usuario")
        self.geometry("520x700")
        self.configure(bg="#ecf0f1")
        self.resizable(False, False)

        # Ventana flotante modal
        self.transient(master)
        self.grab_set()
        self.focus_set()
        self.lift()

        # Centrar ventana
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (520 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"520x700+{x}+{y}")
        self.update()
        self.lift()
        self.focus_force()

        # Estilos
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#ecf0f1", foreground="#2c3e50", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#2c3e50")
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6, relief="flat")

        # Frame contenedor
        self.frame = tk.Frame(self, bg="#ffffff", bd=2, relief="flat")
        self.frame.pack(fill="both", expand=True, padx=16, pady=16)

        label = ttk.Label(self.frame, text="Editar Perfil de Usuario", style="Header.TLabel")
        label.pack(pady=(10, 6))

        # --- FOTO ---
        self.foto_frame = tk.Frame(self.frame, width=150, height=150, bg="#e0e0e0", relief="ridge", bd=2)
        self.foto_frame.pack(pady=(5, 15))
        self.foto_frame.pack_propagate(False)

        self.foto_label = tk.Label(self.foto_frame, text="📷 Foto Usuario", bg="#e0e0e0", fg="gray")
        self.foto_label.place(relx=0.5, rely=0.5, anchor="center")

        # --- CAMPOS ---
        datos = tk.Frame(self.frame, bg="#ffffff")
        datos.pack(fill="both", expand=True, padx=6, pady=4)

        self.fields = {}
        labels = [
            ("Usuario", "usuario"),
            ("Contraseña", "contrasena"),
            ("Nombre 1", "nombre1"),
            ("Nombre 2", "nombre2"),
            ("Apellido 1", "apellido1"),
            ("Apellido 2", "apellido2"),
            ("Rol", "rol"),
            ("Unidad", "unidad")
        ]

        for i, (lbl, key) in enumerate(labels):
            tk.Label(datos, text=lbl + ":", bg="#ffffff", anchor="w").grid(row=i, column=0, sticky="w", pady=8, padx=(4, 8))
            ent = ttk.Entry(datos, width=28)
            ent.grid(row=i, column=1, sticky="ew", padx=(0, 6), ipady=5)
            datos.columnconfigure(1, weight=1)
            self.fields[key] = ent

        # --- BOTONES ---
        btn_frame = tk.Frame(self.frame, bg="#ffffff")
        btn_frame.pack(fill="x", pady=15, padx=4)

        self.btn_actualizar = tk.Button(
            btn_frame, text="💾 Actualizar", bg="#1abc9c", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", command=self.actualizar
        )
        self.btn_actualizar.pack(side="left", expand=True, fill="x", padx=6, ipadx=4, ipady=6)

        self.btn_cerrar = tk.Button(
            btn_frame, text="❌ Cerrar", bg="#e74c3c", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", command=self.destroy
        )
        self.btn_cerrar.pack(side="left", expand=True, fill="x", padx=6, ipadx=4, ipady=6)

        # Cargar datos
        self.load_user()

    # ---------------- CARGAR DATOS ----------------
    def load_user(self):
        """Carga los datos del usuario seleccionado."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT * FROM colaborador WHERE id = %s", (self.user_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()

            if not row:
                messagebox.showerror("Error", f"Usuario con ID {self.user_id} no encontrado.")
                self.destroy()
                return

            # Rellenar campos
            for key in self.fields:
                self.fields[key].delete(0, tk.END)
                if key in row and row[key] is not None:
                    self.fields[key].insert(0, str(row[key]))

            # Mostrar la foto si existe
            if "foto_path" in row and row["foto_path"]:
                try:
                    if os.path.exists(row["foto_path"]):
                        with open(row["foto_path"], "rb") as f:
                            self.mostrar_foto(f.read())
                except Exception as e:
                    print(f"⚠ No se pudo mostrar la foto: {e}")

        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo cargar el usuario:\n{e}")

    # ---------------- MOSTRAR FOTO ----------------
    def mostrar_foto(self, foto_bytes):
        """Muestra la foto circular del usuario desde el archivo."""
        try:
            image = Image.open(io.BytesIO(foto_bytes)).convert("RGB")
            image = image.resize((150, 150), Image.LANCZOS)

            # Crear máscara circular
            mask = Image.new("L", (150, 150), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 150, 150), fill=255)

            result = Image.new("RGBA", (150, 150))
            result.paste(image, (0, 0), mask=mask)

            self.foto_img = ImageTk.PhotoImage(result)
            self.foto_label.config(image=self.foto_img, text="")
        except Exception as e:
            print(f"Error al mostrar foto: {e}")

    # ---------------- ACTUALIZAR ----------------
    def actualizar(self):
        """Actualiza los datos del usuario en la base de datos."""
        try:
            datos = {k: v.get().strip() for k, v in self.fields.items()}
            if not datos["usuario"] or not datos["nombre1"]:
                messagebox.showwarning("Atención", "Usuario y Nombre 1 son obligatorios.")
                return

            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                UPDATE colaborador
                SET usuario = %s, contrasena = %s, nombre1 = %s, nombre2 = %s,
                    apellido1 = %s, apellido2 = %s, rol = %s, unidad = %s
                WHERE id = %s
            """, (datos["usuario"], datos["contrasena"], datos["nombre1"], datos["nombre2"],
                  datos["apellido1"], datos["apellido2"], datos["rol"], datos["unidad"], self.user_id))
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Actualización exitosa", "Los datos del usuario se actualizaron correctamente.")
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo actualizar el perfil:\n{e}")

# ---------------- PRUEBA INDIVIDUAL ----------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    EditarP(root, user_id=1)  # Cambia el ID según tu base de datos
    root.mainloop()