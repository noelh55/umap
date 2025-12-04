import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psycopg2
from editar_perfil import DB_CONFIG
from datetime import datetime
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import csv
from datetime import datetime

class AdminUsuarios(tk.Toplevel):
    def __init__(self, master=None, usuario_actual=None):
        super().__init__(master)
        self.title("Administración de Usuarios y Solicitudes")
        self.geometry("900x650")
        self.configure(bg="#f7f9fb")
        self.usuario_actual = usuario_actual

        self.transient(master)
        self.grab_set()
        self.focus_set()
        self.lift()

        # Centrar ventana
        self.update_idletasks()
        if master:
            master_x = master.winfo_x()
            master_y = master.winfo_y()
            master_w = master.winfo_width()
            master_h = master.winfo_height()
            w, h = 900, 650
            x = master_x + (master_w // 2) - (w // 2)
            y = master_y + (master_h // 2) - (h // 2)
        else:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            w, h = 900, 650
            x = (screen_w // 2) - (w // 2)
            y = (screen_h // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Tabs
        self.tab_usuarios = ttk.Frame(self.notebook)
        self.tab_solicitudes = ttk.Frame(self.notebook)
        self.tab_historial = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_usuarios, text="Usuarios")
        self.notebook.add(self.tab_solicitudes, text="Solicitudes")
        self.notebook.add(self.tab_historial, text="Historial")

        self.init_tab_usuarios()
        self.init_tab_solicitudes()
        self.init_tab_historial()

    # -------------------- TAB USUARIOS --------------------
    def init_tab_usuarios(self):
        ttk.Label(self.tab_usuarios, text="Colaboradores Registrados", font=("Segoe UI", 14, "bold")).pack(pady=5)

        # === TABLA PRINCIPAL: TODOS LOS USUARIOS ===
        self.tree_usuarios = ttk.Treeview(
            self.tab_usuarios,
            columns=("id","usuario","nombre1","rol","dependencia"),
            show="headings",
            height=4
        )
        for col, width in zip(("id","usuario","nombre1","rol","dependencia"), (50,150,200,120,150)):
            self.tree_usuarios.heading(col, text=col.capitalize())
            self.tree_usuarios.column(col, width=width, anchor="center")
        self.tree_usuarios.pack(fill="x", padx=10, pady=5)

        # Eventos igual que antes
        self.tree_usuarios.bind("<<TreeviewSelect>>", self.on_tree_select_usuario)
        self.tree_usuarios.bind("<Double-1>", lambda e: self.abrir_editar_usuario())

        # === TABLA DE USUARIOS ACTIVOS ===
        tk.Label(
            self.tab_usuarios,
            text="Usuarios Activos",
            font=("Segoe UI", 12, "bold"),
            fg="#27ae60",
            bg="#f7f9fb"
        ).pack(pady=(10,0))

        self.tree_activos = ttk.Treeview(
            self.tab_usuarios,
            columns=("usuario","nombre1","rol","dependencia"),
            show="headings",
            height=4
        )
        for col, width in zip(("usuario","nombre1","rol","dependencia"), (150,200,120,150)):
            self.tree_activos.heading(col, text=col.capitalize())
            self.tree_activos.column(col, width=width, anchor="center")
        self.tree_activos.pack(fill="x", padx=10, pady=5)

        # === TABLA DE USUARIOS INACTIVOS ===
        tk.Label(
            self.tab_usuarios,
            text="Usuarios Inactivos",
            font=("Segoe UI", 12, "bold"),
            fg="#c0392b",
            bg="#f7f9fb"
        ).pack(pady=(10,0))

        self.tree_inactivos = ttk.Treeview(
            self.tab_usuarios,
            columns=("usuario","nombre1","rol","dependencia"),
            show="headings",
            height=4
        )
        for col, width in zip(("usuario","nombre1","rol","dependencia"), (150,200,120,150)):
            self.tree_inactivos.heading(col, text=col.capitalize())
            self.tree_inactivos.column(col, width=width, anchor="center")
        self.tree_inactivos.pack(fill="x", padx=10, pady=5)

        # === BOTONES ===
        btn_frame = tk.Frame(self.tab_usuarios, bg="#f7f9fb")
        btn_frame.pack(pady=10)

        self.btn_editar = tk.Button(
            btn_frame, text="✏️ Editar",
            bg="#1abc9c", fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat", width=12,
            state="disabled",
            activebackground="#16a085",
            activeforeground="white",
            command=self.abrir_editar_usuario
        )
        self.btn_editar.pack(side="left", padx=10)

        self.btn_eliminar = tk.Button(
            btn_frame, text="🗑 Eliminar",
            bg="#e67e22", fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat", width=12,
            command=self.eliminar_usuario
        )
        self.btn_eliminar.pack(side="left", padx=10)

        tk.Button(
            btn_frame, text="📄 Generar PDF",
            bg="#2c3e50", fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat", width=14,
            command=self.generar_pdf_usuarios
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame, text="↩ Cerrar",
            bg="#e74c3c", fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat", width=12,
            activebackground="#c0392b",
            activeforeground="white",
            command=self.destroy
        ).pack(side="left", padx=10)

        # Cargar datos
        self.cargar_usuarios()
        self.cargar_activos_inactivos()

    def cargar_activos_inactivos(self):
        for row in self.tree_activos.get_children():
            self.tree_activos.delete(row)
        for row in self.tree_inactivos.get_children():
            self.tree_inactivos.delete(row)

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            cur.execute("SELECT usuario, nombre1, rol, dependencia FROM colaborador WHERE estado = 'Activo'")
            for usuario, nombre, rol, dependencia in cur.fetchall():
                self.tree_activos.insert("", "end", values=(usuario, nombre, rol, dependencia))

            cur.execute("SELECT usuario, nombre1, rol, dependencia FROM colaborador WHERE estado = 'Inactivo'")
            for usuario, nombre, rol, dependencia in cur.fetchall():
                self.tree_inactivos.insert("", "end", values=(usuario, nombre, rol, dependencia))

            cur.close()
            conn.close()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar activos/inactivos:\n{e}")

    def cargar_usuarios(self):
        for row in self.tree_usuarios.get_children():
            self.tree_usuarios.delete(row)

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            cur.execute("SELECT id, usuario, nombre1, rol, dependencia FROM colaborador ORDER BY id")
            for usuario_id, usuario, nombre, rol, dependencia in cur.fetchall():
               self.tree_usuarios.insert("", "end", values=(usuario_id, usuario, nombre, rol, dependencia))

            cur.close()
            conn.close()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los usuarios:\n{e}")

    def on_tree_select_usuario(self, event):
        sel = self.tree_usuarios.selection()
        self.btn_editar.config(state="normal" if sel else "disabled")

    def abrir_editar_usuario(self):
        selected = self.tree_usuarios.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un usuario.")
            return

        item = self.tree_usuarios.item(selected)
        user_id = item["values"][0]

        try:
            from editarp import EditarP
            EditarP(self.master, user_id)
        except Exception as e:
           messagebox.showerror("Error", f"No se pudo abrir el formulario de edición:\n{e}")

    def eliminar_usuario(self):
        selected = self.tree_usuarios.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un usuario.")
            return

        item = self.tree_usuarios.item(selected)
        user_id = item["values"][0]

        if not messagebox.askyesno("Confirmar", "¿Desea marcar este usuario como INACTIVO?"):
            return

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("UPDATE usuarios SET estado = 'Inactivo' WHERE id=%s", (user_id,))
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Listo", "Usuario marcado como INACTIVO.")

            self.cargar_usuarios()
            self.cargar_activos_inactivos()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cambiar estado:\n{e}")

    def generar_pdf_usuarios(self):
        try:
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet

            doc = SimpleDocTemplate("usuarios_registro.pdf", pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()

            title = Paragraph("Listado de Usuarios", styles["Title"])
            elements.append(title)

            data = [["Usuario", "Nombre", "Rol", "Unidad", "Estado"]]

            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT usuario, nombre1, rol, dependencia, estado FROM colaborador ORDER BY nombre")
            rows = cur.fetchall()
            cur.close()
            conn.close()

            for row in rows:
                data.append(row)

            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.gray),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
            ]))

            elements.append(table)
            doc.build(elements)

            messagebox.showinfo("PDF Generado", "El archivo usuarios_registro.pdf se creó correctamente.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}")

    # -------------------- TAB SOLICITUDES --------------------
    def init_tab_solicitudes(self):
        ttk.Label(self.tab_solicitudes, text="Solicitudes de Actualización", font=("Segoe UI", 14, "bold")).pack(pady=5)

        # Tabla solicitudes recientes
        ttk.Label(self.tab_solicitudes, text="Recientes", font=("Segoe UI", 12, "bold")).pack(pady=2)
        self.tree_recientes = ttk.Treeview(self.tab_solicitudes, columns=("usuario","estado","fecha"), show="headings", height=5)
        for col, width in zip(("usuario","estado","fecha"), (250,120,180)):
            self.tree_recientes.heading(col, text=col.capitalize())
            self.tree_recientes.column(col, width=width, anchor="center")
        self.tree_recientes.pack(fill="x", padx=10)
        self.tree_recientes.bind("<<TreeviewSelect>>", self.on_tree_select_solicitud)

        # Tabla todas las solicitudes
        ttk.Label(self.tab_solicitudes, text="Todas", font=("Segoe UI", 12, "bold")).pack(pady=2)
        self.tree_solicitudes = ttk.Treeview(self.tab_solicitudes, columns=("usuario","estado","fecha"), show="headings", height=8)
        for col, width in zip(("usuario","estado","fecha"), (250,120,180)):
            self.tree_solicitudes.heading(col, text=col.capitalize())
            self.tree_solicitudes.column(col, width=width, anchor="center")
        self.tree_solicitudes.pack(fill="x", padx=10)
        self.tree_solicitudes.bind("<<TreeviewSelect>>", self.on_tree_select_solicitud)

        # Tabla eliminadas recientemente
        ttk.Label(self.tab_solicitudes, text="Eliminadas", 
                  font=("Segoe UI", 12, "bold")).pack(pady=2)

        self.tree_eliminadas = ttk.Treeview(
            self.tab_solicitudes,
            columns=("usuario",),
            show="headings",
            height=3
        ) 
        self.tree_eliminadas.heading("usuario", text="Usuario")
        self.tree_eliminadas.column("usuario", width=200, anchor="center")

        self.tree_eliminadas.pack(fill="x", padx=10, pady=(0,10))

        # Botones
        btn_frame = tk.Frame(self.tab_solicitudes, bg="#f7f9fb")
        btn_frame.pack(pady=5)
        self.btn_aceptar = tk.Button(btn_frame, text="✅ Aceptar", bg="#a3e4d7", fg="black", font=("Segoe UI", 11, "bold"),
                                     width=12, relief="flat", command=lambda: self.cambiar_estado_solicitud("aprobada"), state="disabled")
        self.btn_aceptar.pack(side="left", padx=5)
        self.btn_rechazar = tk.Button(btn_frame, text="❌ Rechazar", bg="#f1948a", fg="black", font=("Segoe UI", 11, "bold"),
                                      width=12, relief="flat", command=lambda: self.cambiar_estado_solicitud("rechazada"), state="disabled")
        self.btn_rechazar.pack(side="left", padx=5)
        self.btn_eliminar = tk.Button(btn_frame, text="🗑 Eliminar", bg="#d5dbdb", fg="black", font=("Segoe UI", 11, "bold"),
                                      width=12, relief="flat", command=self.eliminar_solicitud_actual, state="disabled")
        self.btn_eliminar.pack(side="left", padx=5)
        tk.Button(btn_frame, text="↩ Cerrar", bg="#e74c3c", fg="white", font=("Segoe UI", 11, "bold"),
                  width=12, relief="flat", command=self.destroy).pack(side="left", padx=5)

        self.cargar_solicitudes()

    def cargar_solicitudes(self):
        # Limpiar tablas
        for tree in [self.tree_recientes, self.tree_solicitudes]:
            for row in tree.get_children():
                tree.delete(row)

        self.selected_solicitud = None
        self.btn_aceptar.config(state="disabled")
        self.btn_rechazar.config(state="disabled")
        self.btn_eliminar.config(state="disabled")

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Traer todas las solicitudes
            cur.execute("""
                SELECT usuario, estado, fecha_solicitud
                FROM solicitudes_actualizacion
                ORDER BY fecha_solicitud DESC
            """)
            datos = cur.fetchall()

            # Recientes solo pendientes
            pendientes = [d for d in datos if d[1].lower() == "pendiente"]
            for usuario, estado, fecha in pendientes:
                fecha_str = fecha.strftime("%y/%m/%d - %H:%M") if fecha else ""
                row_id = self.tree_recientes.insert("", "end", values=(usuario, estado, fecha_str))
                self.color_fila(self.tree_recientes, row_id, estado)

            # Todas las solicitudes
            for usuario, estado, fecha in datos:
                fecha_str = fecha.strftime("%y/%m/%d - %H:%M") if fecha else ""
                row_id = self.tree_solicitudes.insert("", "end", values=(usuario, estado, fecha_str))
                self.color_fila(self.tree_solicitudes, row_id, estado)

            cur.close()
            conn.close()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las solicitudes:\n{e}")

    def color_fila(self, tree, row_id, estado):
        estado = estado.lower()
        if estado == "aprobada":
            color = "#a3e4d7"  # verde claro
        elif estado == "rechazada":
            color = "#f1948a"  # rojo claro
        else:  # pendiente
            color = "#d5dbdb"  # gris
        tree.tag_configure(estado, background=color)
        tree.item(row_id, tags=(estado,))

    def eliminar_solicitud_actual(self):
        if not self.selected_solicitud:
            return
        
        usuario, estado, fecha_str = self.selected_solicitud["values"]

        if not messagebox.askyesno("Confirmar", "¿Desea eliminar esta solicitud?"):
            return

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            fecha_solicitud = datetime.strptime(fecha_str, "%y/%m/%d - %H:%M")

            # ---- BORRAR DE BD ----
            cur.execute("""
                DELETE FROM solicitudes_actualizacion 
                WHERE usuario=%s AND fecha_solicitud=%s
            """, (usuario, fecha_solicitud))

            conn.commit()
            cur.close()
            conn.close()

            # ---- AGREGAR A TABLA DE ELIMINADAS ----
            self.tree_eliminadas.insert("", "end", values=(usuario,))

            # ---- REFRESCAR OTRAS TABLAS ----
            self.cargar_solicitudes()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar solicitud:\n{e}")

    def on_tree_select_solicitud(self, event):
        widget = event.widget
        sel = widget.selection()

        if not sel:
            self.btn_aceptar.config(state="disabled")
            self.btn_rechazar.config(state="disabled")
            self.btn_eliminar.config(state="disabled")
            self.selected_solicitud = None
            return

        self.selected_solicitud = widget.item(sel[0])

        estado = self.selected_solicitud["values"][1].lower()

        # Solo habilitar aceptar/rechazar si está pendiente
        if estado == "pendiente":
            self.btn_aceptar.config(state="normal")
            self.btn_rechazar.config(state="normal")
        else:
            self.btn_aceptar.config(state="disabled")
            self.btn_rechazar.config(state="disabled")

        # Eliminar siempre habilitado
        self.btn_eliminar.config(state="normal")

    def cambiar_estado_solicitud(self, nuevo_estado):
        if not self.selected_solicitud:
            return

        usuario, estado_actual, fecha_str = self.selected_solicitud["values"]
        fecha_solicitud = datetime.strptime(fecha_str, "%y/%m/%d - %H:%M")

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Actualizar el estado en la BD y la fecha de aceptación
            cur.execute("""
                UPDATE solicitudes_actualizacion
                SET estado=%s, fecha_aceptacion=NOW()
                WHERE usuario=%s AND fecha_solicitud=%s
            """, (nuevo_estado, usuario, fecha_solicitud))

            conn.commit()
            cur.close()
            conn.close()

            # Refrescar tablas para reflejar cambios inmediatamente
            self.cargar_solicitudes()

            # Deshabilitar botones hasta que se seleccione otra fila
            self.btn_aceptar.config(state="disabled")
            self.btn_rechazar.config(state="disabled")
            self.btn_eliminar.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cambiar estado:\n{e}")

    def eliminar_solicitud_actual(self):
        if not self.selected_solicitud:
            return
        usuario, estado, fecha_str = self.selected_solicitud["values"]
        if not messagebox.askyesno("Confirmar", "¿Desea eliminar esta solicitud?"):
            return
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            fecha_solicitud = datetime.strptime(fecha_str, "%y/%m/%d - %H:%M")
            cur.execute("DELETE FROM solicitudes_actualizacion WHERE usuario=%s AND fecha_solicitud=%s",
                        (usuario, fecha_solicitud))
            conn.commit()
            cur.close()
            conn.close()
            self.cargar_solicitudes()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar solicitud:\n{e}")

    # -------------------- TAB HISTORIAL --------------------
    def init_tab_historial(self):
        ttk.Label(self.tab_historial, text="Historial de Solicitudes", font=("Segoe UI", 14, "bold")).pack(pady=5)

        hist_frame = tk.Frame(self.tab_historial)
        hist_frame.pack(fill="x", padx=5, pady=2)

        # Tablas lado a lado
        left_frame = tk.Frame(hist_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)
        right_frame = tk.Frame(hist_frame)
        right_frame.pack(side="left", fill="both", expand=True, padx=5)

        # Aprobadas
        lbl_aprobadas = tk.Label(left_frame, text="Aprobadas", font=("Segoe UI", 12, "bold"), fg="#2ecc71")
        lbl_aprobadas.pack()
        self.tree_aprobadas = ttk.Treeview(left_frame, columns=("usuario","fecha"), show="headings", height=6)
        for col, width in zip(("usuario","fecha"), (150,100)):
            self.tree_aprobadas.heading(col, text=col.capitalize())
            self.tree_aprobadas.column(col, width=width, anchor="center")
        self.tree_aprobadas.pack(fill="x", pady=2)

        # Rechazadas
        lbl_rechazadas = tk.Label(right_frame, text="Rechazadas", font=("Segoe UI", 12, "bold"), fg="#e74c3c")
        lbl_rechazadas.pack()
        self.tree_rechazadas = ttk.Treeview(right_frame, columns=("usuario","fecha"), show="headings", height=6)
        for col, width in zip(("usuario","fecha"), (150,100)):
            self.tree_rechazadas.heading(col, text=col.capitalize())
            self.tree_rechazadas.column(col, width=width, anchor="center")
        self.tree_rechazadas.pack(fill="x", pady=2)

        # Gráfico debajo
        self.fig_hist, self.ax_hist = plt.subplots(figsize=(7,2))
        self.canvas_hist = FigureCanvasTkAgg(self.fig_hist, master=self.tab_historial)
        self.canvas_hist.get_tk_widget().pack(fill="x", padx=10, pady=5)

        # Botones
        btn_frame = tk.Frame(self.tab_historial, bg="#f7f9fb")
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="↩ Cerrar", bg="#e74c3c", fg="white", font=("Segoe UI", 11, "bold"),
                  width=12, relief="flat", command=self.destroy).pack(side="left", padx=5)
        tk.Button(btn_frame, text="💾 Descargar Excel", bg="#3498db", fg="white", font=("Segoe UI", 11, "bold"),
                  width=15, relief="flat", command=self.descargar_historial_excel).pack(side="left", padx=5)

        self.cargar_historial()

    def cargar_historial(self):
        for tree in [self.tree_aprobadas, self.tree_rechazadas]:
            for row in tree.get_children():
                tree.delete(row)
        self.hist_usuarios, self.hist_estados, self.hist_fechas = [], [], []
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT usuario, estado, fecha_solicitud FROM solicitudes_actualizacion ORDER BY fecha_solicitud DESC")
            for usuario, estado, fecha in cur.fetchall():
                fecha_str = fecha.strftime("%y/%m/%d - %H:%M") if fecha else ""
                if estado=="aprobada":
                    self.tree_aprobadas.insert("", "end", values=(usuario, fecha_str))
                elif estado=="rechazada":
                    self.tree_rechazadas.insert("", "end", values=(usuario, fecha_str))
                self.hist_usuarios.append(usuario)
                self.hist_estados.append(estado)
                self.hist_fechas.append(fecha_str)
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar historial:\n{e}")
        self.actualizar_grafico_historial()

    def actualizar_grafico_historial(self):
        self.ax_hist.clear()
        aprobadas = self.hist_estados.count("aprobada")
        rechazadas = self.hist_estados.count("rechazada")
        self.ax_hist.bar(["Aprobadas","Rechazadas"], [aprobadas,rechazadas], color=["#2ecc71","#e74c3c"])
        self.ax_hist.set_ylabel("Cantidad")
        self.ax_hist.set_title("Historial de Solicitudes")
        self.canvas_hist.draw()

    def descargar_historial_excel(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files","*.csv")])
        if not filepath:
            return
        try:
            with open(filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Usuario","Estado","Fecha"])
                for usuario, estado, fecha in zip(self.hist_usuarios, self.hist_estados, self.hist_fechas):
                    writer.writerow([usuario, estado, fecha])
            messagebox.showinfo("Descarga exitosa", f"Historial guardado en {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el historial:\n{e}")