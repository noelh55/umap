import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import threading

DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

def mostrar_toast(master, mensaje):
    toast = tk.Toplevel(master)
    toast.overrideredirect(True)
    toast.configure(bg="#27ae60")
    toast.attributes("-topmost", True)
    toast.wm_attributes("-alpha", 0.92)
    tk.Label(toast, text=mensaje, bg="#27ae60", fg="white",
             font=("Segoe UI", 11, "bold"), padx=20, pady=10).pack()
    master.update_idletasks()
    x = master.winfo_x() + master.winfo_width() - 250
    y = master.winfo_y() + master.winfo_height() - 100
    toast.geometry(f"230x50+{x}+{y}")
    threading.Timer(2.0, toast.destroy).start()

class VentanaCaracter(tk.Toplevel):
    def __init__(self, master, cerrar_ventana_llamante=None):
        super().__init__(master)
        self.title("Gestión de Caracteres")
        self.geometry("600x500")
        self.resizable(False, False)
        self.configure(bg="#ecf0f1")
        self.transient(master)
        self.grab_set()
        self.focus_set()
        self.caracter_id_seleccionado = None
        self.cerrar_ventana_llamante = cerrar_ventana_llamante

        self.centrar_ventana()
        self._crear_ui()
        self.init_db()
        self.cargar_caracteres()

        if self.cerrar_ventana_llamante:
            self.cerrar_ventana_llamante.destroy()

    def centrar_ventana(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        ws, hs = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = (ws - w)//2, (hs - h)//2
        self.geometry(f"+{x}+{y}")

    def _crear_ui(self):
        frame = tk.Frame(self, bg="#ffffff", bd=2, relief="flat")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(frame, text="Gestión de Caracteres", bg="#ffffff", fg="#2c3e50",
                 font=("Segoe UI", 18, "bold")).pack(pady=(10,15))

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

        # Tabla
        tabla_frame = tk.Frame(frame, bg="#ffffff")
        tabla_frame.pack(fill="both", expand=True, pady=(10,5))
        tk.Label(tabla_frame, text="Caracteres Registrados", bg="#ffffff", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.tree = ttk.Treeview(tabla_frame, columns=("ID","Nombre","Descripción"), show="headings", height=6)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Descripción", text="Descripción")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Nombre", width=180)
        self.tree.column("Descripción", width=250)
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

    def init_db(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS caracter (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT UNIQUE NOT NULL,
                    descripcion TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error BD", str(e))

    def guardar(self):
        nombre = self.entry_nombre.get().strip()
        descripcion = self.entry_descripcion.get().strip()
        if not nombre:
            messagebox.showwarning("Atención","Debe ingresar nombre")
            return
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("INSERT INTO caracter(nombre, descripcion) VALUES (%s,%s)", (nombre, descripcion))
            conn.commit()
            conn.close()
            mostrar_toast(self, "Caracter guardado ✅")
            self.limpiar()
            self.cargar_caracteres()
        except psycopg2.errors.UniqueViolation:
            messagebox.showwarning("Atención","Este caracter ya existe")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def limpiar(self):
        self.entry_nombre.config(state="normal")
        self.entry_descripcion.config(state="normal")
        self.entry_nombre.delete(0, tk.END)
        self.entry_descripcion.delete(0, tk.END)
        self.btn_guardar.config(state="normal")
        self.btn_editar.config(state="disabled")
        self.btn_actualizar.config(state="disabled")
        self.caracter_id_seleccionado = None

    def cargar_caracteres(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT id, nombre, descripcion FROM caracter ORDER BY id")
            for r in cur.fetchall():
                self.tree.insert("", "end", values=r)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def mostrar_en_campos(self, event):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0])["values"]
        self.caracter_id_seleccionado, nombre, descripcion = item
        self.entry_nombre.delete(0, tk.END)
        self.entry_nombre.insert(0, nombre)
        self.entry_descripcion.delete(0, tk.END)
        self.entry_descripcion.insert(0, descripcion)
        self.entry_nombre.config(state="disabled")
        self.entry_descripcion.config(state="disabled")
        self.btn_editar.config(state="normal")
        self.btn_actualizar.config(state="normal")
        self.btn_guardar.config(state="disabled")

    def habilitar_edicion(self):
        if not self.caracter_id_seleccionado:
            messagebox.showwarning("Atención", "Debe seleccionar un caracter para editar")
            return
        self.entry_nombre.config(state="normal")
        self.entry_descripcion.config(state="normal")
        self.btn_actualizar.config(state="normal")
        self.btn_editar.config(state="disabled")
        self.btn_guardar.config(state="disabled")

    def actualizar(self):
        if not self.caracter_id_seleccionado:
            messagebox.showwarning("Atención", "No hay caracter seleccionado")
            return
        nombre = self.entry_nombre.get().strip()
        descripcion = self.entry_descripcion.get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "Debe ingresar nombre")
            return
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                UPDATE caracter
                SET nombre=%s, descripcion=%s
                WHERE id=%s
            """, (nombre, descripcion, self.caracter_id_seleccionado))
            conn.commit()
            conn.close()
            mostrar_toast(self, "Actualizado ✅")
            self.limpiar()
            self.cargar_caracteres()
        except psycopg2.errors.UniqueViolation:
            messagebox.showwarning("Atención","Este caracter ya existe")
        except Exception as e:
            messagebox.showerror("Error", str(e))

# ---------------- EJEMPLO DE USO ----------------
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x200")
    root.title("Main Simulado")

    combo = ttk.Combobox(root, values=["Gerente", "Analista"])
    combo.pack(pady=20)

    def abrir_caracter():
        VentanaCaracter(root)

    ttk.Button(root, text="Abrir Gestión de Caracteres", command=abrir_caracter).pack(pady=10)
    root.mainloop()