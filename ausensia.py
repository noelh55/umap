import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
import sqlite3
from datetime import datetime, timedelta

DB_NAME = "ausencias.db"

class MisAusencias(tk.Tk):
    def __init__(self, master=None, usuario_actual=None):
        super().__init__(master)
        self.usuario_actual = usuario_actual
        self.title("Mis ausencias")
        self.state("zoomed")
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.crear_tabla()

        # ---------- ENCABEZADO ----------
        encabezado_frame = tk.Frame(self)
        encabezado_frame.pack(fill="x", padx=20, pady=10)

        lbl_titulo = tk.Label(encabezado_frame, text="Mis ausencias", font=("Segoe UI", 20, "bold"))
        lbl_titulo.pack(side="left")

        btn_frame = tk.Frame(encabezado_frame)
        btn_frame.pack(side="right")

        self.btn_calendario = tk.Button(btn_frame, text="📅 Calendario", command=self.mostrar_calendario,
                                       bg="#6C63FF", fg="white", relief="flat", padx=14, pady=6)
        self.btn_calendario.pack(side="left", padx=5)

        self.btn_listado = tk.Button(btn_frame, text="📋 Listado", command=self.mostrar_listado,
                                     bg="#E0E0E0", relief="flat", padx=14, pady=6)
        self.btn_listado.pack(side="left", padx=5)

        # ---------- RESUMEN DE DÍAS ----------
        resumen_frame = tk.Frame(self)
        resumen_frame.pack(fill="x", padx=20, pady=10)

        self.lbl_vac_dispo = tk.Label(resumen_frame, text="9 / 22 disponibles", font=("Segoe UI", 10), bg="#F8F9FA")
        self.lbl_vac_solic = tk.Label(resumen_frame, text="13 solicitados", font=("Segoe UI", 10), bg="#F8F9FA")
        self.lbl_vac_validadas = tk.Label(resumen_frame, text="2 validadas", font=("Segoe UI", 10), bg="#F8F9FA")

        for i, (titulo, label) in enumerate([("Disponibles", self.lbl_vac_dispo),
                                             ("Solicitados", self.lbl_vac_solic),
                                             ("Validadas", self.lbl_vac_validadas)]):
            frame = tk.Frame(resumen_frame, bg="#F8F9FA", bd=0, relief="ridge", padx=10, pady=10)
            frame.grid(row=0, column=i, padx=10)
            tk.Label(frame, text=titulo, bg="#F8F9FA").grid(row=0, column=0)
            label.grid(row=1, column=0)

        # ---------- FORMULARIO DE REGISTRO ----------
        form_frame = tk.Frame(self)
        form_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(form_frame, text="Tipo:").pack(side="left", padx=5)
        self.cmb_tipo = ttk.Combobox(form_frame, values=["Vacaciones", "Otros"], state="readonly")
        self.cmb_tipo.current(0)
        self.cmb_tipo.pack(side="left", padx=5)

        tk.Label(form_frame, text="Inicio:").pack(side="left", padx=5)
        self.date_edit = Calendar(form_frame, selectmode='day', date_pattern='yyyy-mm-dd')
        self.date_edit.pack(side="left", padx=5)

        tk.Label(form_frame, text="Días:").pack(side="left", padx=5)
        self.spin_dias = tk.Spinbox(form_frame, from_=1, to=30, width=5)
        self.spin_dias.pack(side="left", padx=5)

        self.btn_registrar = tk.Button(form_frame, text="➕ Registrar ausencia", command=self.registrar_ausencia,
                                       bg="#6C63FF", fg="white", relief="flat", padx=10, pady=6)
        self.btn_registrar.pack(side="left", padx=10)

        self.btn_regresar = tk.Button(form_frame, text="↩ Regresar", command=self.regresar,
                                       bg="#6C63FF", fg="white", relief="flat", padx=10, pady=6)
        self.btn_regresar.pack(side="left", padx=10)

        # ---------- STACKED VIEW (Calendario / Listado) ----------
        self.stack_frame = tk.Frame(self)
        self.stack_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Calendario
        self.calendario_frame = tk.Frame(self.stack_frame)
        self.calendario_frame.pack(fill="both", expand=True)
        self.calendario = Calendar(self.calendario_frame, selectmode='day', date_pattern='yyyy-mm-dd')
        self.calendario.pack(fill="both", expand=True)
        self.calendario.bind("<<CalendarSelected>>", lambda e: self.mostrar_detalle_dia())

        # Listado
        self.listado_frame = tk.Frame(self.stack_frame)
        self.tabla = ttk.Treeview(self.listado_frame, columns=("ID", "Tipo", "Inicio", "Días"), show="headings")
        for col in ["ID", "Tipo", "Inicio", "Días"]:
            self.tabla.heading(col, text=col)
        self.tabla.column("ID", width=0, stretch=False)
        self.tabla.pack(fill="both", expand=True)

        self.btn_eliminar = tk.Button(self.listado_frame, text="🗑️ Eliminar selección", command=self.eliminar_ausencia,
                                      bg="#DC3545", fg="white", relief="flat", padx=10, pady=6)
        self.btn_eliminar.pack(pady=10)

        # Mostrar calendario por defecto
        self.mostrar_calendario()

        self.colorear_calendario()
        self.actualizar_tabla()

    # ---------------- FUNCIONES -----------------
    def crear_tabla(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ausencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT,
                fecha_inicio TEXT,
                dias INTEGER
            )
        """)
        self.conn.commit()

    def registrar_ausencia(self):
        tipo = self.cmb_tipo.get()
        fecha = self.date_edit.get_date()
        dias = int(self.spin_dias.get())

        self.cursor.execute("INSERT INTO ausencias (tipo, fecha_inicio, dias) VALUES (?, ?, ?)",
                            (tipo, fecha, dias))
        self.conn.commit()
        messagebox.showinfo("Éxito", "Ausencia registrada correctamente.")
        self.colorear_calendario()
        self.actualizar_tabla()

    def regresar(self):
        self.destroy()
        from Main import PantallaPrincipal
        # master es la raíz existente
        app = PantallaPrincipal(master=self.master, usuario_actual=self.usuario_actual)

    def colorear_calendario(self):
        self.calendario.calevent_remove('all')
        self.cursor.execute("SELECT tipo, fecha_inicio, dias FROM ausencias")
        for tipo, fecha_inicio, dias in self.cursor.fetchall():
            start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            for i in range(dias):
                fecha = start_date + timedelta(days=i)
                color = "#6C63FF" if tipo == "Vacaciones" else "#FFB84D"
                self.calendario.calevent_create(fecha, tipo, tags=tipo)
                self.calendario.tag_config(tipo, background=color, foreground="white" if tipo=="Vacaciones" else "black")

    def mostrar_detalle_dia(self):
        fecha = self.calendario.get_date()
        self.cursor.execute("SELECT tipo, dias FROM ausencias WHERE fecha_inicio=?", (fecha,))
        registros = self.cursor.fetchall()
        if registros:
            detalles = "\n".join([f"- {tipo} ({dias} días)" for tipo, dias in registros])
            messagebox.showinfo("Detalle de ausencias", f"Ausencias desde {fecha}:\n{detalles}")
        else:
            messagebox.showinfo("Detalle de ausencias", f"No hay ausencias registradas en {fecha}.")

    def actualizar_tabla(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        self.cursor.execute("SELECT * FROM ausencias ORDER BY fecha_inicio DESC")
        for registro in self.cursor.fetchall():
            self.tabla.insert("", "end", values=registro)

    def eliminar_ausencia(self):
        selected = self.tabla.selection()
        if not selected:
            messagebox.showwarning("Atención", "Selecciona una fila para eliminar.")
            return
        id_ausencia = self.tabla.item(selected[0])['values'][0]
        self.cursor.execute("DELETE FROM ausencias WHERE id=?", (id_ausencia,))
        self.conn.commit()
        messagebox.showinfo("Eliminado", "Ausencia eliminada correctamente.")
        self.actualizar_tabla()
        self.colorear_calendario()

    def mostrar_calendario(self):
        self.listado_frame.pack_forget()
        self.calendario_frame.pack(fill="both", expand=True)
        self.btn_calendario.config(bg="#6C63FF", fg="white")
        self.btn_listado.config(bg="#E0E0E0", fg="black")

    def mostrar_listado(self):
        self.calendario_frame.pack_forget()
        self.listado_frame.pack(fill="both", expand=True)
        self.btn_listado.config(bg="#6C63FF", fg="white")
        self.btn_calendario.config(bg="#E0E0E0", fg="black")


if __name__ == "__main__":
    # Para prueba directa, se puede usar un usuario ficticio
    usuario_prueba = {"nombre": "Delmer", "rol": "Administrador", "foto_path": None}
    app = MisAusencias(usuario_prueba)
    app.mainloop()