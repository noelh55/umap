import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from editar_perfil import DB_CONFIG
from AdminSolicitudes import AdminSolicitudes

class AdminUsuarios(tk.Toplevel):
    def __init__(self, master=None, usuario_actual=None):
        super().__init__(master)
        self.title("Administración de Usuarios")
        self.geometry("700x450")
        self.configure(bg="#f7f9fb")
        self.usuario_actual = usuario_actual

        # --- Ventana flotante ---
        self.transient(master)
        self.grab_set()
        self.focus_set()
        self.lift()

        # --- Centrar la ventana ---
        self.update_idletasks()
        if master:
            master_x = master.winfo_x()
            master_y = master.winfo_y()
            master_w = master.winfo_width()
            master_h = master.winfo_height()
            w, h = 700, 450
            x = master_x + (master_w // 2) - (w // 2)
            y = master_y + (master_h // 2) - (h // 2)
        else:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            w, h = 700, 450
            x = (screen_w // 2) - (w // 2)
            y = (screen_h // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        # --- Etiqueta título ---
        ttk.Label(self, text="Usuarios Registrados", font=("Segoe UI", 14, "bold")).pack(pady=10)

        # --- Tabla de usuarios ---
        self.tree = ttk.Treeview(self, columns=("id", "usuario", "nombre", "rol", "unidad"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("usuario", text="Usuario")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("rol", text="Rol")
        self.tree.heading("unidad", text="Unidad")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Botones ---
        btn_frame = tk.Frame(self, bg="#f7f9fb")
        btn_frame.pack(pady=10)

        self.btn_editar = tk.Button(btn_frame, text="✏️ Editar", bg="#1abc9c", fg="white",
                                    font=("Segoe UI", 10, "bold"), relief="flat",
                                    command=self.abrir_editar_usuario, state="disabled")
        self.btn_editar.pack(side="left", padx=5)

        self.btn_solicitudes = tk.Button(btn_frame, text="📨 Solicitudes", bg="#3498db", fg="white",
                                         font=("Segoe UI", 10, "bold"), relief="flat",
                                         command=self.ver_solicitudes)
        self.btn_solicitudes.pack(side="left", padx=5)

        tk.Button(btn_frame, text="↩ Cerrar", bg="#e74c3c", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  command=self.destroy).pack(side="left", padx=5)

        # Evento: seleccionar fila
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Cargar usuarios
        self.cargar_usuarios()

    # ------------------------------------------------------------
    # CARGAR USUARIOS
    # ------------------------------------------------------------
    def cargar_usuarios(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT id, usuario, nombre, rol, unidad FROM usuarios ORDER BY id")
            for usuario_id, usuario, nombre, rol, unidad in cur.fetchall():
                self.tree.insert("", "end", values=(usuario_id, usuario, nombre, rol, unidad))
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los usuarios:\n{e}")

    # ------------------------------------------------------------
    # HABILITAR BOTÓN EDITAR
    # ------------------------------------------------------------
    def on_tree_select(self, event):
        sel = self.tree.selection()
        if sel:
            self.btn_editar.config(state="normal")
        else:
            self.btn_editar.config(state="disabled")

    # ------------------------------------------------------------
    # ABRIR FORMULARIO EDITAR PERFIL
    # ------------------------------------------------------------
    def abrir_editar_usuario(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un usuario.")
            return

        item = self.tree.item(selected)
        user_id = item["values"][0]  # ID del usuario

        try:
            from editarp import EditarP
            EditarP(self.master, user_id)  # Abre ventana de edición
            self.destroy()  # Cierra la lista de usuarios
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el formulario de edición:\n{e}")

    # ------------------------------------------------------------
    # ABRIR SOLICITUDES
    # ------------------------------------------------------------
    def ver_solicitudes(self):
        AdminSolicitudes(self)