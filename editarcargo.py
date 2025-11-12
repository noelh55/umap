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

# ---------------- VENTANA EDITAR CARGO ----------------
class EditarCargo(tk.Toplevel):
    def __init__(self, master, cargo_id=None, nombre=None, descripcion=None):
        super().__init__(master)
        self.title("Editar Cargo")
        self.geometry("500x550")
        self.resizable(False, False)
        self.configure(bg="#ecf0f1")
        self.transient(master)
        self.grab_set()

        self.centrar_ventana()

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#ecf0f1", foreground="#2c3e50", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8, relief="flat")
        style.map("TButton", background=[("active", "#16a085"), ("!active", "#1abc9c")],
                  foreground=[("active", "white"), ("!active", "white")])
        style.configure("TEntry", font=("Segoe UI", 11))

        self.frame = tk.Frame(self, bg="#ffffff", bd=2, relief="flat")
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)

        title = tk.Label(self.frame, text="Editar Cargo", bg="#ffffff", fg="#2c3e50",
                         font=("Segoe UI", 18, "bold"))
        title.pack(pady=(10, 20))

        id_nombre_frame = tk.Frame(self.frame, bg="#ffffff")
        id_nombre_frame.pack(fill="x", pady=5)

        tk.Label(id_nombre_frame, text="Nombre del cargo:", bg="#ffffff", fg="#2c3e50",
                 font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w")
        self.entry_nombre = ttk.Entry(id_nombre_frame)
        self.entry_nombre.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        id_nombre_frame.columnconfigure(1, weight=1)

        label_desc = tk.Label(self.frame, text="Descripción:", bg="#ffffff", fg="#2c3e50", font=("Segoe UI", 11))
        label_desc.pack(anchor="w", pady=(10, 0))
        self.text_descripcion = tk.Text(self.frame, height=6, font=("Segoe UI", 11),
                                        bd=1, relief="solid", wrap="word")
        self.text_descripcion.pack(fill="both", pady=8)

        btn_frame = tk.Frame(self.frame, bg="#ffffff")
        btn_frame.pack(pady=20, fill="x")

        btn_actualizar = tk.Button(btn_frame, text="🔄 Actualizar", bg="#1abc9c", fg="white",
                                   font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                                   command=self.actualizar)
        btn_actualizar.pack(side="left", expand=True, fill="x", padx=5, ipadx=5, ipady=5)

        btn_limpiar = tk.Button(btn_frame, text="🧹 Limpiar", bg="#3498db", fg="white",
                                font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                                command=self.limpiar)
        btn_limpiar.pack(side="left", expand=True, fill="x", padx=5, ipadx=5, ipady=5)

        btn_cerrar = tk.Button(btn_frame, text="❌ Cerrar", bg="#e74c3c", fg="white",
                               font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                               command=self.destroy)
        btn_cerrar.pack(side="left", expand=True, fill="x", padx=5, ipadx=5, ipady=5)

        # Cargar datos
        self.cargo_id = cargo_id
        if nombre:
            self.entry_nombre.insert(0, nombre)
        if descripcion:
            self.text_descripcion.insert("1.0", descripcion)

        # Evento doble clic
        self.bind("<Double-1>", self.mostrar_detalles)

    def centrar_ventana(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        ws, hs = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = (ws // 2) - (w // 2), (hs // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def actualizar(self):
        nombre = self.entry_nombre.get().strip()
        descripcion = self.text_descripcion.get("1.0", tk.END).strip()

        if not self.cargo_id:
            messagebox.showwarning("Atención", "No se ha seleccionado ningún cargo.")
            return
        if not nombre:
            messagebox.showwarning("Atención", "Debe ingresar el nombre del cargo.")
            return

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("UPDATE cargos SET nombre=%s, descripcion=%s WHERE id=%s",
                        (nombre, descripcion, self.cargo_id))
            conn.commit()
            conn.close()

            messagebox.showinfo("Éxito", f"Cargo con ID {self.cargo_id} actualizado correctamente.")
            self.destroy()
        except psycopg2.errors.UniqueViolation:
            messagebox.showwarning("Atención", "Ya existe otro cargo con ese nombre.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el cargo:\n{e}")

    def limpiar(self):
        self.entry_nombre.delete(0, tk.END)
        self.text_descripcion.delete("1.0", tk.END)

    def mostrar_detalles(self, event):
        """Ventana flotante con la información desglosada"""
        win = tk.Toplevel(self)
        win.title("Detalles del Cargo")
        win.configure(bg="#ffffff")
        win.geometry("350x250")
        win.transient(self)
        win.grab_set()
        win.update_idletasks()
        ws, hs = win.winfo_screenwidth(), win.winfo_screenheight()
        x, y = (ws // 2) - 175, (hs // 2) - 125
        win.geometry(f"+{x}+{y}")

        ttk.Label(win, text=f"🆔 ID: {self.cargo_id}", background="#ffffff",
                  font=("Segoe UI", 11, "bold")).pack(pady=10)
        ttk.Label(win, text=f"📋 Nombre: {self.entry_nombre.get()}", background="#ffffff",
                  font=("Segoe UI", 11)).pack(pady=5)
        ttk.Label(win, text="📝 Descripción:", background="#ffffff",
                  font=("Segoe UI", 11, "bold")).pack(pady=(10, 0))
        desc = self.text_descripcion.get("1.0", tk.END).strip()
        tk.Message(win, text=desc or "(Sin descripción)", width=300, bg="#ffffff",
                   font=("Segoe UI", 10)).pack(pady=5)

        tk.Button(win, text="Cerrar", bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", cursor="hand2", command=win.destroy).pack(pady=10)