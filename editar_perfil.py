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

        # Ventana flotante
        self.transient(master)
        self.grab_set()
        self.focus_set()
        self.lift()

        self.foto_path_actual = None
        self.foto_img = None  
        self.nueva_foto_bytes = None  # ← NUEVA FOTO TEMPORAL
        self.origin = None    

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

        # --- Botón para cambiar foto (solo habilitado cuando editable=True)
        self.btn_cambiar_foto = tk.Button(
            self.frame, text="📁 Cambiar Foto", bg="#8e44ad", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            state="disabled", command=self.elegir_foto
        )
        self.btn_cambiar_foto.pack(pady=(0,10))

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
            tk.Label(datos, text=lbl + ":", bg="#ffffff", anchor="w").grid(
                row=i, column=0, sticky="w", pady=8, padx=(4, 8)
            )
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
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            command=self.solicitar_actualizacion
        )
        self.btn_solicitar.pack(side="left", expand=True, fill="x", padx=6, ipadx=4, ipady=6)

        self.btn_actualizar = tk.Button(
            btn_frame, text="💾 Actualizar", bg="#1abc9c", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            command=self.actualizar, state="disabled"
        )
        self.btn_actualizar.pack(side="left", expand=True, fill="x", padx=6, ipadx=4, ipady=6)

        self.btn_cerrar = tk.Button(
            btn_frame, text="❌ Cerrar", bg="#e74c3c", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            command=self.destroy
        )
        self.btn_cerrar.pack(side="left", expand=True, fill="x", padx=6, ipadx=4, ipady=6)

        self.init_db()
        self.load_user()

    # ---------------- BD ----------------
    def init_db(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo conectar:\n{e}")

    # ---------------- CARGAR USUARIO ----------------
    def load_user(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            row = None

            # Buscar en usuarios
            if str(self.user_id).isdigit():
                cur.execute("SELECT * FROM usuarios WHERE id=%s", (int(self.user_id),))
            else:
                cur.execute("SELECT * FROM usuarios WHERE usuario=%s", (self.user_id,))

            row = cur.fetchone()

            if row:
                self.origin = "usuarios"
            else:
                # Buscar en colaborador
                if str(self.user_id).isdigit():
                    cur.execute("SELECT * FROM colaborador WHERE id=%s", (int(self.user_id),))
                else:
                    cur.execute("SELECT * FROM colaborador WHERE usuario=%s", (self.user_id,))

                row = cur.fetchone()
                if row:
                    self.origin = "colaborador"

            cur.close()
            conn.close()

            if not row:
                messagebox.showerror("Error", "Usuario no encontrado")
                self.destroy()
                return

            # ----- MAPEO DE CAMPOS -----
            mapa = {
                "nombre": "nombre1",
                "nombre2": "nombre2",
                "apellido1": "apellido1",
                "apellido2": "apellido2",
                "usuario": "usuario",
                "contrasena": "contrasena",
                "rol": "rol",
                "unidad": "unidad"
            }

            # ----- CARGAR CAMPOS -----
            for key in self.fields:
                self.fields[key].config(state="normal")
                self.fields[key].delete(0, tk.END)

                if self.origin == "usuarios":
                    val = row.get(key, "")
                else:
                    columna = mapa.get(key, key)
                    val = row.get(columna, "")

                self.fields[key].insert(0, val if val else "")
                self.fields[key].config(state="disabled")

            # ----- FOTO -----
            if "foto_path" in row and row["foto_path"]:
                if os.path.exists(row["foto_path"]):
                    with open(row["foto_path"], "rb") as f:
                        self.mostrar_foto(f.read())
                        self.foto_path_actual = row["foto_path"]

            # Solo habilitar si hay fecha_aceptacion y estado de la solicitud es 'aprobada'
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT estado, fecha_aceptacion FROM solicitudes_actualizacion
                WHERE usuario=%s ORDER BY fecha_solicitud DESC LIMIT 1
            """, (self.user_id,))
            sol = cur.fetchone()
            cur.close()
            conn.close()

            if sol:
                estado_solicitud, fecha_aceptacion = sol
                if estado_solicitud == "aprobada":
                    self.habilitar_edicion()
                    self.lbl_estado.config(text="Solicitud aprobada. Puede editar sus datos.", fg="#27ae60")
                elif estado_solicitud == "rechazada":
                    self.lbl_estado.config(text="Solicitud rechazada. No puede editar.", fg="#c0392b")
                else:
                    self.lbl_estado.config(text="Datos bloqueados. Solicite actualización.", fg="#2c3e50")
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo cargar:\n{e}")

    # ---------------- MOSTRAR FOTO ----------------
    def mostrar_foto(self, foto_bytes):
        try:
            if not foto_bytes:
                return
            image = Image.open(io.BytesIO(foto_bytes)).convert("RGB")
            image = image.resize((150,150), Image.LANCZOS)

            mask = Image.new("L", (150,150), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0,0,150,150), fill=255)

            result = Image.new("RGBA",(150,150))
            result.paste(image,(0,0),mask=mask)

            self.foto_img = ImageTk.PhotoImage(result)
            self.foto_label.config(image=self.foto_img, text="")
        except Exception as e:
            print("Error foto:", e)

    # ---------------- CAMBIAR FOTO ----------------
    def elegir_foto(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar Foto",
            filetypes=[("Imagenes","*.jpg *.jpeg *.png")]
        )
        if not ruta:
            return

        with open(ruta,"rb") as f:
            self.nueva_foto_bytes = f.read()

        self.mostrar_foto(self.nueva_foto_bytes)

    # ---------------- SOLICITAR ACTUALIZACIÓN ----------------
    def solicitar_actualizacion(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO solicitudes_actualizacion (usuario, estado) VALUES (%s, %s)",
                (self.user_id, "pendiente")
            )

            tabla = "colaborador" if self.origin=="colaborador" else "usuarios"

            conn.commit()
            cur.close()
            conn.close()

            self.lbl_estado.config(text="Solicitud enviada. Espere aprobación del administrador.", fg="#f39c12")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo enviar:\n{e}")

    # ---------------- HABILITAR EDICIÓN ----------------
    def habilitar_edicion(self):
        for ent in self.fields.values():
            ent.config(state="normal")

        self.btn_actualizar.config(state="normal")
        self.btn_cambiar_foto.config(state="normal")

    # ---------------- ACTUALIZAR ----------------
    def actualizar(self):
        try:
            datos = {k: v.get().strip() for k,v in self.fields.items()}

            tabla = "colaborador" if self.origin=="colaborador" else "usuarios"

            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            cur.execute(f"""
                UPDATE {tabla}
                SET usuario=%s, contrasena=%s, nombre1=%s, nombre2=%s,
                    apellido1=%s, apellido2=%s, rol=%s, unidad=%s,
                    editable=FALSE
                WHERE usuario=%s
            """, (
                datos["usuario"], datos["contrasena"], datos["nombre1"], datos["nombre2"],
                datos["apellido1"], datos["apellido2"], datos["rol"], datos["unidad"],
                self.user_id
            ))

            # GUARDAR FOTO NUEVA (si la seleccionó)
            if self.nueva_foto_bytes:
                foto_path = f"fotos/{datos['usuario']}.jpg"
                os.makedirs("fotos", exist_ok=True)
                with open(foto_path, "wb") as f:
                    f.write(self.nueva_foto_bytes)

                cur.execute(f"UPDATE {tabla} SET foto_path=%s WHERE usuario=%s",
                    (foto_path, self.user_id))

            conn.commit()

            # Después de guardar cambios:
            self.btn_actualizar.config(state="disabled")
            self.btn_cambiar_foto.config(state="disabled")
            self.lbl_estado.config(text="Perfil actualizado. Solicite otra actualización para más cambios.", fg="#27ae60")

            # Actualizar editable en BD
            cur.execute("UPDATE colaborador SET editable=FALSE WHERE usuario=%s", (self.user_id,))

            cur.close()
            conn.close()

            self.btn_actualizar.config(state="disabled")
            self.btn_cambiar_foto.config(state="disabled")
            self.lbl_estado.config(text="Perfil actualizado correctamente.", fg="#27ae60")

        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo actualizar:\n{e}")

# ---------------- EJEMPLO ----------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    EditarPerfil(root, "noel")
    root.mainloop()