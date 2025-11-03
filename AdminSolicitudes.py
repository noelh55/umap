import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from editar_perfil import DB_CONFIG
from datetime import datetime  # <-- agregado para formatear fecha

# ------------------------------------------------------------
# CLASE PRINCIPAL ADMINISTRADOR DE SOLICITUDES
# ------------------------------------------------------------
class AdminSolicitudes(tk.Toplevel):
    def __init__(self, master=None, usuario_actual=None):
        super().__init__(master)
        self.title("Solicitudes de Actualización")
        self.geometry("600x400")
        self.configure(bg="#f7f9fb")
        self.usuario_actual = usuario_actual

        # --- Ventana flotante sobre Main ---
        self.transient(master)
        self.grab_set()
        self.focus_set()

        # --- Centrar la ventana respecto a la principal ---
        self.update_idletasks()
        if master is not None:
            master_x = master.winfo_x()
            master_y = master.winfo_y()
            master_w = master.winfo_width()
            master_h = master.winfo_height()
            w = 600
            h = 400
            x = master_x + (master_w // 2) - (w // 2)
            y = master_y + (master_h // 2) - (h // 2)
        else:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            w = 600
            h = 400
            x = (screen_w // 2) - (w // 2)
            y = (screen_h // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        ttk.Label(self, text="Solicitudes Pendientes", font=("Segoe UI", 14, "bold")).pack(pady=10)

        self.tree = ttk.Treeview(self, columns=("usuario", "estado", "fecha"), show="headings")
        self.tree.heading("usuario", text="Usuario")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("fecha", text="Fecha Solicitud")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Botones ---
        btn_frame = tk.Frame(self, bg="#f7f9fb")
        btn_frame.pack(pady=10)

        # Botones deshabilitados por defecto
        self.btn_aprobar = tk.Button(btn_frame, text="✅ Aprobar", bg="#2ecc71", fg="white",
                                     font=("Segoe UI", 10, "bold"), relief="flat",
                                     command=self.aprobar, state="disabled")
        self.btn_aprobar.pack(side="left", padx=5)

        self.btn_rechazar = tk.Button(btn_frame, text="❌ Rechazar", bg="#e74c3c", fg="white",
                                      font=("Segoe UI", 10, "bold"), relief="flat",
                                      command=self.rechazar, state="disabled")
        self.btn_rechazar.pack(side="left", padx=5)

        tk.Button(btn_frame, text="↩ Cerrar", bg="#3498db", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  command=self.destroy).pack(side="left", padx=5)

        # Evento: cuando selecciona una fila → habilita botones
        self.tree.bind("<<TreeviewSelect>>", self.habilitar_botones)

        self.cargar_solicitudes()

    # ------------------------------------------------------------
    # HABILITAR BOTONES AL SELECCIONAR UNA FILA
    # ------------------------------------------------------------
    def habilitar_botones(self, event=None):
        sel = self.tree.selection()
        if sel:
            self.btn_aprobar.config(state="normal")
            self.btn_rechazar.config(state="normal")

    # ------------------------------------------------------------
    # CARGAR SOLICITUDES
    # ------------------------------------------------------------
    def cargar_solicitudes(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT usuario, estado, fecha_solicitud FROM solicitudes_actualizacion ORDER BY fecha_solicitud DESC")
            for usuario, estado, fecha in cur.fetchall():
                if fecha:
                    fecha_formateada = fecha.strftime("%y/%m/%d - %H:%M")
                else:
                    fecha_formateada = ""
                self.tree.insert("", "end", values=(usuario, estado, fecha_formateada))
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las solicitudes:\n{e}")

    # ------------------------------------------------------------
    # APROBAR / RECHAZAR
    # ------------------------------------------------------------
    def aprobar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una solicitud.")
            return
        item = self.tree.item(sel[0])["values"]
        usuario = item[0]
        fecha_str = item[2]
        self.cambiar_estado(usuario, fecha_str, "aprobada")

    def rechazar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una solicitud.")
            return
        item = self.tree.item(sel[0])["values"]
        usuario = item[0]
        fecha_str = item[2]
        self.cambiar_estado(usuario, fecha_str, "rechazada")

    # ------------------------------------------------------------
    # CAMBIAR ESTADO SOLO DE ESA SOLICITUD (NO TODAS)
    # ------------------------------------------------------------
    def cambiar_estado(self, usuario, fecha_str, nuevo_estado):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # 🔹 Convertir el string de fecha al mismo formato del campo en DB
            fecha_solicitud = None
            if fecha_str:
                try:
                    fecha_solicitud = datetime.strptime(fecha_str, "%y/%m/%d - %H:%M")
                except Exception:
                    fecha_solicitud = None

            # 🔹 Solo actualizar la solicitud seleccionada
            if fecha_solicitud:
                cur.execute("""
                    UPDATE solicitudes_actualizacion 
                    SET estado = %s 
                    WHERE usuario = %s AND fecha_solicitud = %s
                """, (nuevo_estado, usuario, fecha_solicitud))
            else:
                # Fallback si no hay fecha (poco probable)
                cur.execute("""
                    UPDATE solicitudes_actualizacion 
                    SET estado = %s 
                    WHERE usuario = %s 
                    ORDER BY fecha_solicitud DESC LIMIT 1
                """, (nuevo_estado, usuario))

            # 🔹 Si se aprueba → permitir edición del perfil
            if nuevo_estado == "aprobada":
                cur.execute("UPDATE usuarios SET editable = TRUE WHERE usuario = %s", (usuario,))
            else:
                cur.execute("UPDATE usuarios SET editable = FALSE WHERE usuario = %s", (usuario,))

            conn.commit()
            cur.close()
            conn.close()

            # Refrescar lista
            self.cargar_solicitudes()
            messagebox.showinfo("Éxito", f"Solicitud de {usuario} {nuevo_estado}.")
            self.btn_aprobar.config(state="disabled")
            self.btn_rechazar.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el estado:\n{e}")