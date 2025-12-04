import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import psycopg2.errors

# ───────────────────────────────────────────────
#  CONFIGURACIÓN BASE DE DATOS
# ───────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "tu_base",
    "user": "postgres",
    "password": "tu_password"
}

# ───────────────────────────────────────────────
#  FUNCIÓN TOAST (Notificación flotante)
# ───────────────────────────────────────────────
def mostrar_toast(parent, mensaje):
    toast = tk.Toplevel(parent)
    toast.overrideredirect(True)
    toast.config(bg="#2ecc71")
    toast.attributes("-topmost", True)

    tk.Label(toast, text=mensaje, fg="white", bg="#2ecc71",
             font=("Segoe UI", 11, "bold"), padx=20, pady=10).pack()

    # Posición abajo a la derecha de la ventana principal
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_w = parent.winfo_width()
    parent_h = parent.winfo_height()

    toast.geometry(f"+{parent_x + parent_w - 250}+{parent_y + parent_h - 80}")

    toast.after(2000, toast.destroy)

# ───────────────────────────────────────────────
#  VENTANA DE MOTIVOS
# ───────────────────────────────────────────────
class VentanaMotivos(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Gestión de Motivos por Carácter")
        self.geometry("650x600")
        self.resizable(False, False)
        self.configure(bg="#ecf0f1")
        self.transient(master)
        self.grab_set()
        self.motivo_id = None

        # Animación fade-in
        self.attributes("-alpha", 0.0)
        self.after(10, self.animar_apertura)

        # Centrar ventana
        self.centrar_ventana()

        # ─── Estilos ─────────────────────────────
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#ecf0f1", foreground="#2c3e50", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8, relief="flat")
        style.map("TButton", background=[("active", "#16a085"), ("!active", "#1abc9c")],
                  foreground=[("active", "white"), ("!active", "white")])
        style.configure("TEntry", font=("Segoe UI", 11))

        # ─── FRAME PRINCIPAL ─────────────────────
        main = tk.Frame(self, bg="#ffffff", bd=2)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(main, text="Gestión de Motivos por Carácter", bg="#ffffff",
                 fg="#2c3e50", font=("Segoe UI", 18, "bold")).pack(pady=10)

        # ─── Carácter ─────────────────────────────
        frame_car = tk.Frame(main, bg="#ffffff")
        frame_car.pack(fill="x", pady=5)

        tk.Label(frame_car, text="Carácter:", bg="#ffffff",
                 fg="#2c3e50", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w")

        self.combo_caracter = ttk.Combobox(frame_car, values=["A", "B", "C", "D", "E"],
                                           state="readonly", font=("Segoe UI", 11))
        self.combo_caracter.grid(row=0, column=1, sticky="ew", padx=5)
        self.combo_caracter.current(0)
        self.combo_caracter.bind("<<ComboboxSelected>>", self.cargar_motivos)
        frame_car.columnconfigure(1, weight=1)

        # ─── Motivo ───────────────────────────────
        frame_mot = tk.Frame(main, bg="#ffffff")
        frame_mot.pack(fill="x", pady=5)

        tk.Label(frame_mot, text="Motivo:", bg="#ffffff",
                 fg="#2c3e50", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w")

        self.entry_motivo = ttk.Entry(frame_mot)
        self.entry_motivo.grid(row=0, column=1, sticky="ew", padx=5)
        frame_mot.columnconfigure(1, weight=1)

        # ─── Descripción ─────────────────────────
        frame_desc = tk.Frame(main, bg="#ffffff")
        frame_desc.pack(fill="x", pady=5)

        tk.Label(frame_desc, text="Descripción:", bg="#ffffff",
                 fg="#2c3e50", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w")

        self.entry_desc = ttk.Entry(frame_desc)
        self.entry_desc.grid(row=0, column=1, sticky="ew", padx=5)
        frame_desc.columnconfigure(1, weight=1)

        # ─── Tabla ───────────────────────────────
        tabla_frame = tk.Frame(main, bg="#ffffff")
        tabla_frame.pack(fill="both", expand=True, pady=10)

        self.tree = ttk.Treeview(tabla_frame,
                                 columns=("ID", "Motivo", "Descripción"),
                                 show="headings", height=7)

        self.tree.heading("ID", text="ID")
        self.tree.heading("Motivo", text="Motivo")
        self.tree.heading("Descripción", text="Descripción")

        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Motivo", width=200)
        self.tree.column("Descripción", width=260)

        vsb = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self.mostrar_en_campos)

        # ─── Botones ─────────────────────────────
        botones = tk.Frame(main, bg="#ffffff")
        botones.pack(fill="x", pady=10)

        tk.Button(botones, text="💾 Guardar", bg="#1abc9c", fg="white",
                  relief="flat", cursor="hand2", command=self.guardar).pack(
                      side="left", expand=True, fill="x", padx=5, ipady=5)

        tk.Button(botones, text="✏️ Editar", bg="#3498db", fg="white",
                  relief="flat", cursor="hand2", command=self.editar).pack(
                      side="left", expand=True, fill="x", padx=5, ipady=5)

        tk.Button(botones, text="🔄 Actualizar", bg="#f39c12", fg="white",
                  relief="flat", cursor="hand2", command=self.actualizar).pack(
                      side="left", expand=True, fill="x", padx=5, ipady=5)

        tk.Button(botones, text="❌ Cerrar", bg="#e74c3c", fg="white",
                  relief="flat", cursor="hand2", command=self.destroy).pack(
                      side="left", expand=True, fill="x", padx=5, ipady=5)

        # ─── Inicializar DB y cargar datos ───────
        self.init_db()
        self.cargar_motivos()

    # ─────────────────────────────────────────────
    #   ANIMACIÓN
    # ─────────────────────────────────────────────
    def animar_apertura(self):
        alpha = self.attributes("-alpha")
        if alpha < 1:
            alpha += 0.07
            self.attributes("-alpha", alpha)
            self.after(10, self.animar_apertura)

    # ─────────────────────────────────────────────
    #   CENTRAR VENTANA
    # ─────────────────────────────────────────────
    def centrar_ventana(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ─────────────────────────────────────────────
    #   CREAR TABLA SI NO EXISTE
    # ─────────────────────────────────────────────
    def init_db(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS motivos (
                    id SERIAL PRIMARY KEY,
                    caracter VARCHAR(5) NOT NULL,
                    motivo TEXT NOT NULL,
                    descripcion TEXT,
                    UNIQUE(caracter, motivo)
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear tabla motivos:\n{e}")

    # ─────────────────────────────────────────────
    #   CARGAR MOTIVOS
    # ─────────────────────────────────────────────
    def cargar_motivos(self, event=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        caracter = self.combo_caracter.get()

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                SELECT id, motivo, descripcion
                FROM motivos
                WHERE caracter = %s
                ORDER BY motivo
            """, (caracter,))
            for row in cur.fetchall():
                self.tree.insert("", "end", values=row)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar motivos:\n{e}")

    # ─────────────────────────────────────────────
    #   MOSTRAR CAMPOS AL SELECCIONAR
    # ─────────────────────────────────────────────
    def mostrar_en_campos(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0], "values")
        self.motivo_id, motivo, desc = item

        self.entry_motivo.delete(0, tk.END)
        self.entry_desc.delete(0, tk.END)

        self.entry_motivo.insert(0, motivo)
        self.entry_desc.insert(0, desc)

    # ─────────────────────────────────────────────
    #   GUARDAR NUEVO MOTIVO
    # ─────────────────────────────────────────────
    def guardar(self):
        caracter = self.combo_caracter.get()
        motivo = self.entry_motivo.get().strip()
        desc = self.entry_desc.get().strip()

        if not motivo:
            messagebox.showwarning("Atención", "Debe ingresar un motivo.")
            return

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO motivos(caracter, motivo, descripcion)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (caracter, motivo, desc))
            conn.commit()
            conn.close()

            mostrar_toast(self, "Motivo guardado ✓")
            self.cargar_motivos()
            self.entry_motivo.delete(0)
            self.entry_desc.delete(0)

        except psycopg2.errors.UniqueViolation:
            messagebox.showwarning("Atención", "Este motivo ya existe en este carácter.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    # ─────────────────────────────────────────────
    #   EDITAR
    # ─────────────────────────────────────────────
    def editar(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un motivo para editar.")
            return
        self.mostrar_en_campos(None)

    # ─────────────────────────────────────────────
    #   ACTUALIZAR
    # ─────────────────────────────────────────────
    def actualizar(self):
        if not self.motivo_id:
            messagebox.showwarning("Atención", "No hay motivo seleccionado.")
            return

        caracter = self.combo_caracter.get()
        motivo = self.entry_motivo.get().strip()
        desc = self.entry_desc.get().strip()

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                UPDATE motivos
                SET caracter = %s, motivo = %s, descripcion = %s
                WHERE id = %s
            """, (caracter, motivo, desc, self.motivo_id))
            conn.commit()
            conn.close()

            mostrar_toast(self, "Motivo actualizado ✓")
            self.cargar_motivos()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar:\n{e}")