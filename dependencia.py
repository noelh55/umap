import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import subprocess
import os
from editardependencia import EditarDependencia


# ---------------- CONFIGURACIÓN BASE DE DATOS ----------------
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

# ---------------- VENTANA DE DEPENDENCIAS ----------------
class VentanaDependencia(tk.Toplevel):
    def __init__(self, master, combobox_dependencias=None):
        super().__init__(master)
        self.title("Formulario de Dependencias")
        self.geometry("520x550")
        self.resizable(False, False)
        self.configure(bg="#ecf0f1")
        self.transient(master)
        self.grab_set()
        self.combobox_dependencias = combobox_dependencias

        self.init_db()
        self.crear_widgets()
        self.centrar_ventana()

    # ---------------- CREAR WIDGETS ----------------
    def crear_widgets(self):
        # Frame principal
        self.frame = tk.Frame(self, bg="#ffffff", bd=2, relief="flat")
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Estilo
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#ffffff", foreground="#2c3e50", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8, relief="flat")
        style.map("TButton",
                  background=[("active", "#16a085"), ("!active", "#1abc9c")],
                  foreground=[("active", "white"), ("!active", "white")])
        style.configure("TEntry", font=("Segoe UI", 11))

        # ---------------- TÍTULO ----------------
        ttk.Label(self.frame, text="Formulario de Dependencias",
                  font=("Segoe UI", 18, "bold"), background="#ffffff").pack(pady=(10, 20))

        # ---------------- ID + NOMBRE ----------------
        nombre_frame = tk.Frame(self.frame, bg="#ffffff")
        nombre_frame.pack(fill="x", pady=5)

        #tk.Label(nombre_frame, text="ID:", bg="#ffffff", fg="#2c3e50",
                 #font=("Segoe UI", 11)).grid(row=0, column=0, padx=(0, 5), sticky="w")
        #self.entry_id = ttk.Entry(nombre_frame, width=8, state="readonly")
        #self.entry_id.grid(row=0, column=1, padx=(0, 15))
        #self.generar_id()

        tk.Label(nombre_frame, text="Nombre de la dependencia:", bg="#ffffff", fg="#2c3e50",
                 font=("Segoe UI", 11)).grid(row=0, column=2, sticky="w")
        self.entry_nombre = ttk.Entry(nombre_frame)
        self.entry_nombre.grid(row=0, column=3, sticky="ew", padx=(5, 0))
        nombre_frame.columnconfigure(3, weight=1)

        # ---------------- DESCRIPCIÓN ----------------
        tk.Label(self.frame, text="Descripción:", bg="#ffffff", fg="#2c3e50",
                 font=("Segoe UI", 11)).pack(anchor="w", pady=(10, 0))
        self.text_descripcion = tk.Text(self.frame, height=6, font=("Segoe UI", 11),
                                        bd=1, relief="solid", wrap="word")
        self.text_descripcion.pack(fill="both", pady=8)

        # ---------------- BOTONES PRINCIPALES ----------------
        btn_frame = tk.Frame(self.frame, bg="#ffffff")
        btn_frame.pack(pady=15, fill="x")

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

        # ---------------- VER DEPENDENCIAS ----------------
        btn_ver = tk.Button(
            self.frame, text="👁️ Ver Dependencias Registradas", bg="#16a085", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            command=self.ver_dependencias
        )
        btn_ver.pack(fill="x", pady=(10, 5), ipadx=5, ipady=6)

    # ---------------- BASE DE DATOS ----------------
    def init_db(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dependencias (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT UNIQUE NOT NULL,
                    descripcion TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo inicializar la tabla:\n{e}")

    # ---------------- CENTRAR VENTANA ----------------
    def centrar_ventana(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ---------------- GENERAR ID ----------------
    def generar_id(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(MAX(id), 0)+1 FROM dependencias")
            next_id = cur.fetchone()[0]
            conn.close()
            self.entry_id.config(state="normal")
            self.entry_id.delete(0, tk.END)
            self.entry_id.insert(0, str(next_id))
            self.entry_id.config(state="readonly")
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo generar ID:\n{e}")

    # ---------------- GUARDAR ----------------
    def guardar(self):
        nombre = self.entry_nombre.get().strip()
        descripcion = self.text_descripcion.get("1.0", tk.END).strip()

        if not nombre:
            messagebox.showwarning("Atención", "Debe ingresar el nombre de la dependencia.")
            return

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO dependencias(nombre, descripcion) VALUES (%s, %s) RETURNING id",
                (nombre, descripcion)
            )
            dep_id = cur.fetchone()[0]
            conn.commit()
            conn.close()

            messagebox.showinfo("Éxito", f"Dependencia guardada correctamente.\nID asignado: {dep_id}")
            self.limpiar()
            self.generar_id()

            if self.combobox_dependencias:
                current_values = list(self.combobox_dependencias['values'])
                if nombre not in current_values:
                    current_values.append(nombre)
                self.combobox_dependencias['values'] = current_values
                self.combobox_dependencias.set(nombre)

        except psycopg2.errors.UniqueViolation:
            messagebox.showwarning("Atención", "Esta dependencia ya existe.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar en la base de datos:\n{e}")

    # ---------------- LIMPIAR ----------------
    def limpiar(self):
        self.entry_nombre.delete(0, tk.END)
        self.text_descripcion.delete("1.0", tk.END)

    # ---------------- VER DEPENDENCIAS ----------------
    def ver_dependencias(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT id, nombre, descripcion FROM dependencias ORDER BY id")
            deps = cur.fetchall()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudieron obtener las dependencias:\n{e}")
            return

        if not deps:
            messagebox.showinfo("Información", "No hay dependencias registradas.")
            return

        ver_win = tk.Toplevel(self)
        ver_win.title("Lista de Dependencias")
        ver_win.geometry("500x350")
        ver_win.configure(bg="#ecf0f1")
        ver_win.transient(self)
        ver_win.grab_set()

        tk.Label(
            ver_win, text="Dependencias Registradas",
            bg="#ecf0f1", fg="#2c3e50", font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        frame_tabla = tk.Frame(ver_win, bg="#ffffff", bd=1, relief="solid")
        frame_tabla.pack(fill="both", expand=True, padx=10, pady=10)

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

        for d in deps:
            tree.insert("", "end", values=d)

        # --- Botones de acción ---
        btn_frame = tk.Frame(ver_win, bg="#ecf0f1")
        btn_frame.pack(fill="x", pady=10)

        def editar_dependencia():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Atención", "Debe seleccionar una dependencia para editar.")
                return
            item = tree.item(selected[0], "values")
            dep_id, nombre, descripcion = item

            ver_win.destroy()
            self.destroy()

            from editardependencia import EditarDependencia
            EditarDependencia(self.master, dep_id, nombre, descripcion)

        btn_editar = tk.Button(
            btn_frame, text="✏️ Editar Dependencia", bg="#1abc9c", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            command=editar_dependencia
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

    combo = ttk.Combobox(root, values=["Finanzas", "Infraestructura"])
    combo.pack(pady=20)

    ttk.Button(root, text="Agregar Dependencia", command=lambda: VentanaDependencia(root, combobox_dependencias=combo)).pack(pady=10)

    root.mainloop()