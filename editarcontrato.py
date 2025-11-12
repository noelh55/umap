import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2

# ---------------- CONFIGURACIÓN BASE DE DATOS ----------------
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

# ---------------- VENTANA EDITAR CONTRATO ----------------
class EditarContrato(tk.Toplevel):
    def __init__(self, master, contrato_id=None, nombre=None, descripcion=None):
        super().__init__(master)
        self.title("Editar Contrato")
        self.geometry("500x550")
        self.resizable(False, False)
        self.configure(bg="#ecf0f1")
        self.transient(master)
        self.grab_set()

        # --- Centrar ventana ---
        self.centrar_ventana()

        # --- Estilos modernos ---
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#ecf0f1", foreground="#2c3e50", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8, relief="flat")
        style.map("TButton", background=[("active", "#16a085"), ("!active", "#1abc9c")],
                  foreground=[("active", "white"), ("!active", "white")])
        style.configure("TEntry", font=("Segoe UI", 11))

        # --- Frame principal ---
        self.frame = tk.Frame(self, bg="#ffffff", bd=2, relief="flat")
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- Título ---
        title = tk.Label(
            self.frame,
            text="Editar Contrato",
            bg="#ffffff",
            fg="#2c3e50",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(pady=(10, 20))

        # ===================== NOMBRE DEL CONTRATO =====================
        nombre_frame = tk.Frame(self.frame, bg="#ffffff")
        nombre_frame.pack(fill="x", pady=5)

        tk.Label(nombre_frame, text="Nombre del contrato:", bg="#ffffff", fg="#2c3e50", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w")
        self.entry_nombre = ttk.Entry(nombre_frame)
        self.entry_nombre.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        nombre_frame.columnconfigure(1, weight=1)

        # --- Descripción ---
        label_desc = tk.Label(self.frame, text="Descripción / Detalles:", bg="#ffffff", fg="#2c3e50", font=("Segoe UI", 11))
        label_desc.pack(anchor="w", pady=(10, 0))
        self.text_descripcion = tk.Text(self.frame, height=6, font=("Segoe UI", 11), bd=1, relief="solid", wrap="word")
        self.text_descripcion.pack(fill="both", pady=8)

        # --- Botones principales ---
        btn_frame = tk.Frame(self.frame, bg="#ffffff")
        btn_frame.pack(pady=20, fill="x")

        # BOTÓN ACTUALIZAR
        btn_actualizar = tk.Button(
            btn_frame, text="🔄 Actualizar", bg="#1abc9c", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            command=self.actualizar
        )
        btn_actualizar.pack(side="left", expand=True, fill="x", padx=5, ipadx=5, ipady=5)

        btn_limpiar = tk.Button(
            btn_frame, text="🧹 Limpiar", bg="#3498db", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            command=self.limpiar
        )
        btn_limpiar.pack(side="left", expand=True, fill="x", padx=5, ipadx=5, ipady=5)

        btn_cerrar = tk.Button(
            btn_frame, text="❌ Cerrar", bg="#e74c3c", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            command=self.destroy
        )
        btn_cerrar.pack(side="left", expand=True, fill="x", padx=5, ipadx=5, ipady=5)

        # --- Cargar datos del contrato recibido ---
        self.contrato_id = contrato_id
        if nombre:
            self.entry_nombre.insert(0, nombre)
        if descripcion:
            self.text_descripcion.insert("1.0", descripcion)

    # ---------------- FUNCIONES PRINCIPALES ----------------

    def centrar_ventana(self):
        """Centra la ventana en pantalla."""
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def actualizar(self):
        """Actualiza un contrato existente en la base de datos."""
        nombre = self.entry_nombre.get().strip()
        descripcion = self.text_descripcion.get("1.0", tk.END).strip()

        if not self.contrato_id:
            messagebox.showwarning("Atención", "No se ha seleccionado ningún contrato.")
            return

        if not nombre:
            messagebox.showwarning("Atención", "Debe ingresar el nombre del contrato.")
            return

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute(
                "UPDATE contratos SET nombre = %s, descripcion = %s WHERE id = %s",
                (nombre, descripcion, self.contrato_id)
            )
            conn.commit()
            conn.close()

            messagebox.showinfo("Éxito", f"Contrato con ID {self.contrato_id} actualizado correctamente.")
            self.destroy()

        except psycopg2.errors.UniqueViolation:
            messagebox.showwarning("Atención", "Ya existe otro contrato con ese nombre.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el contrato:\n{e}")

    def limpiar(self):
        """Limpia los campos del formulario."""
        self.entry_nombre.delete(0, tk.END)
        self.text_descripcion.delete("1.0", tk.END)

# ---------------- EJEMPLO DE USO ----------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal

    # Ejemplo con datos simulados
    EditarContrato(root, contrato_id=1, nombre="Contrato de Servicios", descripcion="Prestación de servicios profesionales.")
    root.mainloop()