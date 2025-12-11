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

# ---------------- FUNCIÓN DE TOAST ----------------
def mostrar_toast(master, mensaje):
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

    def cerrar():
        toast.destroy()
    threading.Timer(2.0, cerrar).start()

# ---------------- VENTANA MOTIVO ----------------
class VentanaMotivo(tk.Toplevel):
    def __init__(self, master, cerrar_ventana_llamante=None):
        super().__init__(master)
        self.title("Gestión de Motivos")
        self.geometry("600x500")
        self.resizable(False, False)
        self.configure(bg="#ecf0f1")
        self.transient(master)
        self.grab_set()
        self.focus_set()

        self.motivo_id_seleccionado = None
        self.cerrar_ventana_llamante = cerrar_ventana_llamante
        if self.cerrar_ventana_llamante:
            self.cerrar_ventana_llamante.destroy()

        self.centrar_ventana()
        self._crear_ui()
        self.init_db()
        self.cargar_motivos()
        self.cargar_caracteres()

    # ---------------- FUNCIONES DE VENTANA ----------------
    def centrar_ventana(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def _crear_ui(self):
        frame = tk.Frame(self, bg="#ffffff", bd=2, relief="flat")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(frame, text="Gestión de Motivos", bg="#ffffff", fg="#2c3e50",
                 font=("Segoe UI", 18, "bold")).pack(pady=(10, 15))

        # Dropdown Caracter
        caracter_frame = tk.Frame(frame, bg="#ffffff")
        caracter_frame.pack(fill="x", pady=5)
        tk.Label(caracter_frame, text="Caracter:", bg="#ffffff").grid(row=0, column=0, sticky="w")
        self.combo_caracter = ttk.Combobox(caracter_frame, values=[], state="readonly")
        self.combo_caracter.grid(row=0, column=1, sticky="ew", padx=(5,0))
        caracter_frame.columnconfigure(1, weight=1)

        # Nombre
        nombre_frame = tk.Frame(frame, bg="#ffffff")
        nombre_frame.pack(fill="x", pady=5)
        tk.Label(nombre_frame, text="Nombre:", bg="#ffffff").grid(row=0, column=0, sticky="w")
        self.entry_nombre = ttk.Entry(nombre_frame)
        self.entry_nombre.grid(row=0, column=1, sticky="ew", padx=(5,0))
        nombre_frame.columnconfigure(1, weight=1)

        # Descripción
        desc_frame = tk.Frame(frame, bg="#ffffff")
        desc_frame.pack(fill="x", pady=5)
        tk.Label(desc_frame, text="Descripción:", bg="#ffffff").grid(row=0, column=0, sticky="w")
        self.entry_descripcion = ttk.Entry(desc_frame)
        self.entry_descripcion.grid(row=0, column=1, sticky="ew", padx=(5,0))
        desc_frame.columnconfigure(1, weight=1)

        # Tabla Motivos
        tabla_frame = tk.Frame(frame, bg="#ffffff")
        tabla_frame.pack(fill="both", expand=True, pady=(10, 5))
        tk.Label(tabla_frame, text="Motivos Registrados", bg="#ffffff", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.tree = ttk.Treeview(tabla_frame, columns=("ID","Caracter","Nombre","Descripción"), show="headings", height=6)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Caracter", text="Caracter")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Descripción", text="Descripción")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Caracter", width=120)
        self.tree.column("Nombre", width=150)
        self.tree.column("Descripción", width=200)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", self.mostrar_en_campos)
        vsb = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        # Botones
        btn_frame = tk.Frame(frame, bg="#ffffff")
        btn_frame.pack(pady=15, fill="x")
        self.btn_guardar = tk.Button(btn_frame, text="💾 Guardar", bg="#1abc9c", fg="white", command=self.guardar)
        self.btn_guardar.pack(side="left", expand=True, fill="x", padx=5)
        self.btn_editar = tk.Button(btn_frame, text="✏️ Editar", bg="#3498db", fg="white", command=self.habilitar_edicion, state="disabled")
        self.btn_editar.pack(side="left", expand=True, fill="x", padx=5)
        self.btn_actualizar = tk.Button(btn_frame, text="🔄 Actualizar", bg="#f39c12", fg="white", command=self.actualizar, state="disabled")
        self.btn_actualizar.pack(side="left", expand=True, fill="x", padx=5)
        tk.Button(btn_frame, text="❌ Cerrar", bg="#e74c3c", fg="white", command=self.destroy).pack(side="left", expand=True, fill="x", padx=5)

    # ---------------- FUNCIONES DB ----------------
    def init_db(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            # Tabla de caracteres si no existe
            cur.execute("""
                CREATE TABLE IF NOT EXISTS caracter (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT UNIQUE NOT NULL
                )
            """)
            # Tabla motivo
            cur.execute("""
                CREATE TABLE IF NOT EXISTS motivo (
                    id SERIAL PRIMARY KEY,
                    caracter_id INTEGER REFERENCES caracter(id),
                    nombre TEXT NOT NULL,
                    descripcion TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error BD", str(e))

    def cargar_caracteres(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT nombre FROM caracter ORDER BY nombre")
            resultados = [r[0] for r in cur.fetchall()]
            self.combo_caracter['values'] = resultados
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def cargar_motivos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                SELECT m.id, c.nombre, m.nombre, m.descripcion
                FROM motivo m
                LEFT JOIN caracter c ON c.id = m.caracter_id
                ORDER BY m.id
            """)
            for r in cur.fetchall():
                self.tree.insert("", "end", values=r)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---------------- FUNCIONES CRUD ----------------
    def limpiar(self):
        self.entry_nombre.delete(0, tk.END)
        self.entry_descripcion.delete(0, tk.END)
        self.combo_caracter.set("")
        self.btn_guardar.config(state="normal")
        self.btn_editar.config(state="disabled")
        self.btn_actualizar.config(state="disabled")
        self.motivo_id_seleccionado = None

    def guardar(self):
        caracter = self.combo_caracter.get()
        nombre = self.entry_nombre.get().strip()
        descripcion = self.entry_descripcion.get().strip()
        if not caracter or not nombre:
            messagebox.showwarning("Atención","Debe completar todos los campos")
            return
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT id FROM caracter WHERE nombre=%s", (caracter,))
            res = cur.fetchone()
            if not res:
                messagebox.showwarning("Atención","Caracter no válido")
                return
            caracter_id = res[0]
            cur.execute("INSERT INTO motivo(caracter_id,nombre,descripcion) VALUES (%s,%s,%s)",
                        (caracter_id, nombre, descripcion))
            conn.commit()
            conn.close()
            mostrar_toast(self, "Motivo guardado ✅")
            self.limpiar()
            self.cargar_motivos()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def mostrar_en_campos(self, event):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0])["values"]
        self.motivo_id_seleccionado, caracter, nombre, descripcion = item
        self.combo_caracter.set(caracter)
        self.entry_nombre.delete(0, tk.END)
        self.entry_nombre.insert(0, nombre)
        self.entry_descripcion.delete(0, tk.END)
        self.entry_descripcion.insert(0, descripcion)
        self.entry_nombre.config(state="disabled")
        self.entry_descripcion.config(state="disabled")
        self.combo_caracter.config(state="disabled")
        self.btn_editar.config(state="normal")
        self.btn_actualizar.config(state="normal")
        self.btn_guardar.config(state="disabled")

    def habilitar_edicion(self):
        if not self.motivo_id_seleccionado:
            messagebox.showwarning("Atención", "Debe seleccionar un motivo para editar")
            return
        self.entry_nombre.config(state="normal")
        self.entry_descripcion.config(state="normal")
        self.combo_caracter.config(state="readonly")
        self.btn_actualizar.config(state="normal")
        self.btn_editar.config(state="disabled")
        self.btn_guardar.config(state="disabled")

    def actualizar(self):
        if not self.motivo_id_seleccionado:
            messagebox.showwarning("Atención", "No hay motivo seleccionado")
            return
        caracter = self.combo_caracter.get()
        nombre = self.entry_nombre.get().strip()
        descripcion = self.entry_descripcion.get().strip()
        if not caracter or not nombre:
            messagebox.showwarning("Atención","Debe completar todos los campos")
            return
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT id FROM caracter WHERE nombre=%s", (caracter,))
            res = cur.fetchone()
            if not res:
                messagebox.showwarning("Atención","Caracter no válido")
                return
            caracter_id = res[0]
            cur.execute("""
                UPDATE motivo
                SET caracter_id=%s, nombre=%s, descripcion=%s
                WHERE id=%s
            """, (caracter_id, nombre, descripcion, self.motivo_id_seleccionado))
            conn.commit()
            conn.close()
            mostrar_toast(self, "Motivo actualizado ✅")
            self.limpiar()
            self.cargar_motivos()
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ---------------- EJEMPLO DE USO ----------------
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x200")
    root.title("Main Simulado")

    # Botón para abrir la ventana de Motivos
    def abrir_motivo():
        VentanaMotivo(root)

    ttk.Button(root, text="Abrir Gestión de Motivos", command=abrir_motivo).pack(pady=20)
    root.mainloop()