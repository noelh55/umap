import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import threading

# ---------------- CONFIGURACIÓN BASE DE DATOS ----------------
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}


# ---------------- FUNCIÓN DE TOAST (NOTIFICACIÓN FLOTANTE) ----------------
def mostrar_toast(master, mensaje):
    """Muestra un mensaje tipo toast animado."""
    toast = tk.Toplevel(master)
    toast.overrideredirect(True)
    toast.configure(bg="#27ae60")
    toast.attributes("-topmost", True)
    toast.wm_attributes("-alpha", 0.92)

    label = tk.Label(toast, text=mensaje, bg="#27ae60", fg="white",
                     font=("Segoe UI", 11, "bold"), padx=20, pady=10)
    label.pack()

    master.update_idletasks()
    x = master.winfo_x() + master.winfo_width() - 250
    y = master.winfo_y() + master.winfo_height() - 100
    toast.geometry(f"230x50+{x}+{y}")

    # Desaparece luego de 2 segundos
    def cerrar():
        toast.destroy()

    threading.Timer(2.0, cerrar).start()


# ---------------- VENTANA DE CONTRATOS ----------------
class VentanaContrato(tk.Toplevel):
    def __init__(self, master, combobox_contratos=None):
        super().__init__(master)
        self.title("Gestión de Contratos")
        self.geometry("600x550")
        self.resizable(False, False)
        self.configure(bg="#ecf0f1")
        self.transient(master)
        self.grab_set()
        self.combobox_contratos = combobox_contratos
        self.contrato_id_seleccionado = None

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
        title = tk.Label(self.frame, text="Gestión de Contratos", bg="#ffffff", fg="#2c3e50",
                         font=("Segoe UI", 18, "bold"))
        title.pack(pady=(10, 15))

        # --- Nombre del contrato ---
        nombre_frame = tk.Frame(self.frame, bg="#ffffff")
        nombre_frame.pack(fill="x", pady=5)

        tk.Label(nombre_frame, text="Nombre del contrato:", bg="#ffffff", fg="#2c3e50",
                 font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w")
        self.entry_nombre = ttk.Entry(nombre_frame, state="normal")
        self.entry_nombre.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        nombre_frame.columnconfigure(1, weight=1)

        # --- Descripción ---
        desc_frame = tk.Frame(self.frame, bg="#ffffff")
        desc_frame.pack(fill="x", pady=5)

        tk.Label(desc_frame, text="Descripción:", bg="#ffffff", fg="#2c3e50",
                 font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w")
        self.entry_descripcion = ttk.Entry(desc_frame, state="normal")
        self.entry_descripcion.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        desc_frame.columnconfigure(1, weight=1)

        # ===================== TABLA DE CONTRATOS =====================
        tabla_frame = tk.Frame(self.frame, bg="#ffffff")
        tabla_frame.pack(fill="both", expand=True, pady=(10, 5))

        tk.Label(tabla_frame, text="Contratos Registrados", bg="#ffffff", fg="#2c3e50",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=5, pady=(0, 5))

        self.tree = ttk.Treeview(tabla_frame, columns=("ID", "Nombre", "Descripción"),
                                 show="headings", height=6)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Descripción", text="Descripción")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Nombre", width=180)
        self.tree.column("Descripción", width=250)

        vsb = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self.mostrar_en_campos)

        # ===================== BOTONES DEBAJO DE LA TABLA =====================
        btn_frame = tk.Frame(self.frame, bg="#ffffff")
        btn_frame.pack(pady=15, fill="x")

        self.btn_guardar = tk.Button(btn_frame, text="💾 Guardar", bg="#1abc9c", fg="white",
                                     font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                                     command=self.guardar)
        self.btn_guardar.pack(side="left", expand=True, fill="x", padx=5, ipadx=5, ipady=5)

        self.btn_editar = tk.Button(btn_frame, text="✏️ Editar", bg="#3498db", fg="white",
                            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                            command=self.habilitar_edicion, state="disabled")
        self.btn_editar.pack(side="left", expand=True, fill="x", padx=5, ipadx=5, ipady=5)

        self.btn_actualizar = tk.Button(btn_frame, text="🔄 Actualizar", bg="#f39c12", fg="white",
                                        font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                                        command=self.actualizar, state="disabled")
        self.btn_actualizar.pack(side="left", expand=True, fill="x", padx=5, ipadx=5, ipady=5)

        btn_cerrar = tk.Button(btn_frame, text="❌ Cerrar", bg="#e74c3c", fg="white",
                               font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                               command=self.destroy)
        btn_cerrar.pack(side="left", expand=True, fill="x", padx=5, ipadx=5, ipady=5)


        # --- Inicializar ---
        self.init_db()
        self.cargar_contratos()

    # ---------------- FUNCIONES ----------------
    def init_db(self):
        """Crea la tabla si no existe."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contratos (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT UNIQUE NOT NULL,
                    descripcion TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo inicializar la tabla de contratos:\n{e}")

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

    def guardar(self):
        """Guarda un nuevo contrato."""
        nombre = self.entry_nombre.get().strip()
        descripcion = self.entry_descripcion.get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "Debe ingresar el nombre del contrato.")
            return
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("INSERT INTO contratos(nombre, descripcion) VALUES (%s, %s) RETURNING id",
                        (nombre, descripcion))
            conn.commit()
            conn.close()

            mostrar_toast(self, "Contrato guardado correctamente ✅")
            self.limpiar()
            self.cargar_contratos()

            if self.combobox_contratos:
                current_values = list(self.combobox_contratos['values'])
                if nombre not in current_values:
                    current_values.append(nombre)
                self.combobox_contratos['values'] = current_values
                self.combobox_contratos.set(nombre)

        except psycopg2.errors.UniqueViolation:
            messagebox.showwarning("Atención", "Este contrato ya existe.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar en la base de datos:\n{e}")

    def mostrar_reporte(self):
        from reportec import ReporteEmpleados
        ReporteEmpleados(self.root)  # Pasa el root principal como master
        self.destroy()

    def limpiar(self):
        self.entry_nombre.config(state="normal")
        self.entry_descripcion.config(state="normal")
        self.entry_nombre.delete(0, tk.END)
        self.entry_descripcion.delete(0, tk.END)
        self.btn_actualizar.config(state="disabled")
        self.btn_guardar.config(state="normal")
        self.btn_editar.config(state="normal")
        self.contrato_id_seleccionado = None

    def cargar_contratos(self):
        """Carga los contratos en la tabla."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT id, nombre, descripcion FROM contratos ORDER BY id")
            for c in cur.fetchall():
                self.tree.insert("", "end", values=c)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los contratos:\n{e}")

    def mostrar_en_campos(self, event):
        """Muestra los datos seleccionados en los campos."""
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0], "values")
        self.contrato_id_seleccionado, nombre, descripcion = item

        self.entry_nombre.config(state="normal")
        self.entry_descripcion.config(state="normal")
        self.entry_nombre.delete(0, tk.END)
        self.entry_descripcion.delete(0, tk.END)
        self.entry_nombre.insert(0, nombre)
        self.entry_descripcion.insert(0, descripcion)
        self.entry_nombre.config(state="disabled")
        self.entry_descripcion.config(state="disabled")

        self.btn_editar.config(state="normal")
        self.btn_actualizar.config(state="disabled")
        self.btn_guardar.config(state="disabled")

    def habilitar_edicion(self):
        """Habilita edición en los campos."""
        if not self.contrato_id_seleccionado:
            messagebox.showwarning("Atención", "Debe seleccionar un contrato para editar.")
            return
        self.entry_nombre.config(state="normal")
        self.entry_descripcion.config(state="normal")
        self.btn_actualizar.config(state="normal")
        self.btn_guardar.config(state="disabled")
        self.btn_editar.config(state="disabled")

    def actualizar(self):
        """Actualiza los datos del contrato seleccionado."""
        if not self.contrato_id_seleccionado:
            messagebox.showwarning("Atención", "No hay contrato seleccionado.")
            return

        nombre = self.entry_nombre.get().strip()
        descripcion = self.entry_descripcion.get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "Debe ingresar el nombre del contrato.")
            return

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                UPDATE contratos
                SET nombre = %s, descripcion = %s
                WHERE id = %s
            """, (nombre, descripcion, self.contrato_id_seleccionado))
            conn.commit()
            conn.close()

            mostrar_toast(self, "Actualizado correctamente ✅")
            self.limpiar()
            self.cargar_contratos()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el contrato:\n{e}")

# ---------------- EJEMPLO DE USO ----------------
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x200")
    root.title("Main Simulado")

    combo = ttk.Combobox(root, values=["Contrato Temporal", "Contrato Permanente"])
    combo.pack(pady=20)

    def abrir_contrato():
        VentanaContrato(root, combobox_contratos=combo)

    ttk.Button(root, text="Abrir Gestión de Contratos", command=abrir_contrato).pack(pady=10)

    root.mainloop()