import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from editarcontrato import EditarContrato  

# ---------------- CONFIGURACIÓN BASE DE DATOS ----------------
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

# ---------------- VENTANA DE CONTRATOS ----------------
class VentanaContrato(tk.Toplevel):
    def __init__(self, master, combobox_contratos=None):
        super().__init__(master)
        self.title("Formulario de Contratos")
        self.geometry("500x550")
        self.resizable(False, False)
        self.configure(bg="#ecf0f1")
        self.transient(master)
        self.grab_set()
        self.combobox_contratos = combobox_contratos

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
            text="Formulario de Contratos",
            bg="#ffffff",
            fg="#2c3e50",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(pady=(10, 20))

        # ===================== ID + NOMBRE DEL CONTRATO =====================
        id_nombre_frame = tk.Frame(self.frame, bg="#ffffff")
        id_nombre_frame.pack(fill="x", pady=5)

        # Nombre del contrato
        tk.Label(id_nombre_frame, text="Nombre del contrato:", bg="#ffffff", fg="#2c3e50",
                 font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w")
        self.entry_nombre = ttk.Entry(id_nombre_frame)
        self.entry_nombre.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        id_nombre_frame.columnconfigure(1, weight=1)

        # --- Descripción ---
        label_desc = tk.Label(self.frame, text="Descripción:", bg="#ffffff", fg="#2c3e50", font=("Segoe UI", 11))
        label_desc.pack(anchor="w", pady=(10, 0))
        self.text_descripcion = tk.Text(self.frame, height=6, font=("Segoe UI", 11), bd=1, relief="solid", wrap="word")
        self.text_descripcion.pack(fill="both", pady=8)

        # --- Botones principales ---
        btn_frame = tk.Frame(self.frame, bg="#ffffff")
        btn_frame.pack(pady=20, fill="x")

        btn_guardar = tk.Button(
            btn_frame, text="💾 Guardar", bg="#1abc9c", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            command=self.guardar
        )
        btn_guardar.pack(side="left", expand=True, fill="x", padx=5, ipadx=5, ipady=5)

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

        # --- Botón para ver contratos registrados ---
        btn_ver = tk.Button(
            self.frame, text="👁️ Ver Contratos Registrados",
            bg="#16a085", fg="white", font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2", command=self.ver_contratos
        )
        btn_ver.pack(fill="x", pady=(10, 5), ipadx=5, ipady=6)

        # --- Inicializar base de datos ---
        self.init_db()

    # ---------------- FUNCIONES PRINCIPALES ----------------
    def init_db(self):
        """Crea la tabla de contratos si no existe."""
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
        """Guarda un nuevo contrato en la base de datos."""
        nombre = self.entry_nombre.get().strip()
        descripcion = self.text_descripcion.get("1.0", tk.END).strip()

        if not nombre:
            messagebox.showwarning("Atención", "Debe ingresar el nombre del contrato.")
            return

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO contratos(nombre, descripcion) VALUES (%s, %s) RETURNING id",
                (nombre, descripcion)
            )
            contrato_id = cur.fetchone()[0]
            conn.commit()
            conn.close()

            messagebox.showinfo("Éxito", f"Contrato guardado correctamente.\nID asignado: {contrato_id}")
            self.limpiar()

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

    def limpiar(self):
        """Limpia los campos del formulario."""
        self.entry_nombre.delete(0, tk.END)
        self.text_descripcion.delete("1.0", tk.END)

    def ver_contratos(self):
        """Muestra la lista de contratos registrados."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT id, nombre, descripcion FROM contratos ORDER BY id")
            contratos = cur.fetchall()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudieron obtener los contratos:\n{e}")
            return

        if not contratos:
            messagebox.showinfo("Información", "No hay contratos registrados.")
            return

        # --- Ventana de lista ---
        ver_win = tk.Toplevel(self)
        ver_win.title("Lista de Contratos")
        ver_win.geometry("500x350")
        ver_win.configure(bg="#ecf0f1")
        ver_win.transient(self)
        ver_win.grab_set()

        # Centrar ventana de lista
        ver_win.update_idletasks()
        w = ver_win.winfo_width()
        h = ver_win.winfo_height()
        ws = ver_win.winfo_screenwidth()
        hs = ver_win.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        ver_win.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(
            ver_win, text="Contratos Registrados",
            bg="#ecf0f1", fg="#2c3e50", font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        frame_tabla = tk.Frame(ver_win, bg="#ffffff", bd=1, relief="solid")
        frame_tabla.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Tabla ---
        tree = ttk.Treeview(frame_tabla, columns=("ID", "Nombre", "Descripción"), show="headings", height=10)
        tree.heading("ID", text="ID")
        tree.heading("Nombre", text="Nombre")
        tree.heading("Descripción", text="Descripción")
        tree.column("ID", width=50, anchor="center")
        tree.column("Nombre", width=150)
        tree.column("Descripción", width=260)

        vsb = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        for c in contratos:
            tree.insert("", "end", values=c)

        # --- Doble clic para editar ---
        def doble_click(event):
            item = tree.selection()
            if not item:
                return
            values = tree.item(item[0], "values")
            contrato_id, nombre, descripcion = values
            ver_win.destroy()
            self.destroy()
            EditarContrato(self.master, contrato_id, nombre, descripcion)

        tree.bind("<Double-1>", doble_click)

        # --- Botones de acción ---
        btn_frame = tk.Frame(ver_win, bg="#ecf0f1")
        btn_frame.pack(fill="x", pady=10)

        def editar_contrato():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Atención", "Debe seleccionar un contrato para editar.")
                return
            item = tree.item(selected[0], "values")
            contrato_id, nombre, descripcion = item
            ver_win.destroy()
            self.destroy()
            EditarContrato(self.master, contrato_id, nombre, descripcion)

        btn_editar = tk.Button(
            btn_frame, text="✏️ Editar Contrato", bg="#1abc9c", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            command=editar_contrato
        )
        btn_editar.pack(side="left", expand=True, fill="x", padx=5, ipadx=5, ipady=5)

        btn_cerrar = tk.Button(
            btn_frame, text="❌ Cerrar", bg="#e74c3c", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            command=ver_win.destroy
        )
        btn_cerrar.pack(side="left", expand=True, fill="x", padx=5, ipadx=5, ipady=5)


# ---------------- EJEMPLO DE USO ----------------
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x200")
    root.title("Main Simulado")

    combo = ttk.Combobox(root, values=["Contrato Temporal", "Contrato Permanente"])
    combo.pack(pady=20)

    def abrir_contrato():
        VentanaContrato(root, combobox_contratos=combo)

    ttk.Button(root, text="Agregar Contrato", command=abrir_contrato).pack(pady=10)

    root.mainloop()