import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import Calendar
from datetime import date, datetime, timedelta
import psycopg2
import psycopg2.extras
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import cm

# ---------------- CONFIGURACIÓN BASE DE DATOS ----------------
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

# Colores
COLOR_BG = "#ecf0f1"
COLOR_PENDING = "#d5dbdb"
COLOR_APPROVED = "#a3e4d7"
COLOR_REJECTED = "#f1948a"
COLOR_VAC_YELLOW = "#fff7c2"
COLOR_AUS_BLUE = "#d9eefc"

TABLA_PERMISOS = "permisos_dias_laborales"

def connect():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        messagebox.showerror("Error BD", f"No se pudo conectar a la BD:\n{e}")
        return None

# ---------------- VENTANA FLOTA SOLICITUDES ----------------
class SolicitudesFlotante(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Solicitudes")
        self.geometry("1100x700")
        self.configure(bg=COLOR_BG)

        # Botón cerrar
        tk.Button(self, text="Cerrar", command=self.destroy, bg="#e74c3c", fg="white").pack(anchor="ne", padx=8, pady=4)

        self._build_ui()
        self.load_solicitudes()

    def _build_ui(self):
        cont = tk.Frame(self, bg=COLOR_BG)
        cont.pack(fill="both", expand=True, padx=12, pady=8)

        # Left: Treeview + controles
        self.left = tk.Frame(cont, bg=COLOR_BG)
        self.left.pack(side="left", fill="both", expand=True)

        # Controls arriba
        ctrl = tk.Frame(self.left, bg=COLOR_BG)
        ctrl.pack(fill="x")
        tk.Label(ctrl, text="Buscar:", bg=COLOR_BG).pack(side="left", padx=(4,6))
        self.search_var = tk.StringVar()
        tk.Entry(ctrl, textvariable=self.search_var).pack(side="left", padx=6)
        self.search_var.trace("w", lambda *args: self.load_solicitudes())
        tk.Button(ctrl, text="🔄 Refrescar", command=self.load_solicitudes).pack(side="left", padx=6)
        tk.Button(ctrl, text="📄 Exportar PDF", command=self.export_selected_pdf).pack(side="left", padx=6)
        tk.Button(ctrl, text="📊 Exportar Excel", command=self.export_all_excel).pack(side="left", padx=6)
        tk.Button(ctrl, text="➕ Nuevo Caracter", command=self.abrir_form_caracter).pack(side="left", padx=6)
        tk.Button(ctrl, text="➕ Nuevo Motivo", command=self.abrir_form_motivo).pack(side="left", padx=6)

        # Treeview
        # Tabla de ausencias
        cols = ("id","identidad","nombre_completo","tipo_permiso","fecha_inicio","fecha_fin","dias_solicitados","estado")
        self.tree = ttk.Treeview(self.left, columns=cols, show="headings", height=20)
        for c in cols:
            self.tree.heading(c, text=c.replace("_"," ").title())
            self.tree.column(c, width=120, anchor="center")
        self.tree.pack(fill="x", expand=False, padx=6, pady=6)
        self.tree.configure(height=10)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Buttons accept/reject
        btns = tk.Frame(self.left, bg=COLOR_BG)
        btns.pack(fill="x", pady=(4,8))
        self.btn_aceptar = tk.Button(btns, text="✅ Aceptar", bg="#27ae60", fg="white", command=self.aceptar_solicitud, state="disabled")
        self.btn_aceptar.pack(side="left", padx=6)
        self.btn_rechazar = tk.Button(btns, text="❌ Rechazar", bg="#e74c3c", fg="white", command=self.rechazar_solicitud, state="disabled")
        self.btn_rechazar.pack(side="left", padx=6)

        # Controls arriba - Vacaciones
        ctrl_vac = tk.Frame(self.left, bg=COLOR_BG)
        ctrl_vac.pack(fill="x", pady=(8,4))

        tk.Label(ctrl_vac, text="Buscar vacaciones:", bg=COLOR_BG).pack(side="left", padx=(4,6))
        self.search_vac_var = tk.StringVar()
        tk.Entry(ctrl_vac, textvariable=self.search_vac_var).pack(side="left", padx=6)
        self.search_vac_var.trace("w", lambda *args: self.load_vacaciones_filtradas())

        tk.Button(ctrl_vac, text="🔄 Refrescar", command=self.load_vacaciones).pack(side="left", padx=6)
        tk.Button(ctrl_vac, text="📄 Exportar PDF", command=lambda: self.export_selected_pdf_vac()).pack(side="left", padx=6)

        # --- Tabla de vacaciones ---
        cols_v = ("id","identidad","nombre_completo","fecha_inicio","fecha_fin","dias","estado")
        self.tree_v = ttk.Treeview(self.left, columns=cols_v, show="headings", height=10)
        for c in cols_v:
            self.tree_v.heading(c, text=c.replace("_"," ").title())
            self.tree_v.column(c, width=120, anchor="center")
        self.tree_v.pack(fill="x", expand=False, padx=6, pady=(0,6))
        self.tree_v.bind("<<TreeviewSelect>>", self.on_select_v)

        btns_v = tk.Frame(self.left, bg=COLOR_BG)
        btns_v.pack(fill="x", pady=(2,8))
        self.btn_aceptar_v = tk.Button(btns_v, text="✅ Aceptar Vacación", bg="#27ae60", fg="white", command=self.aceptar_vacacion, state="disabled")
        self.btn_aceptar_v.pack(side="left", padx=6)
        self.btn_rechazar_v = tk.Button(btns_v, text="❌ Rechazar Vacación", bg="#e74c3c", fg="white", command=self.rechazar_vacacion, state="disabled")
        self.btn_rechazar_v.pack(side="left", padx=6)

        self.tree_v.tag_configure("pend", background="#EEEEEE")
        self.tree_v.tag_configure("ok", background="#A8F5A2")
        self.tree_v.tag_configure("bad", background="#F8B3B3")

        # Right: detalle + calendario
        self.right = tk.Frame(cont, bg=COLOR_BG, width=380)
        self.right.pack(side="left", fill="y", padx=(6,0))

        tk.Label(self.right, text="Detalle solicitud", font=("Segoe UI", 12, "bold"), bg=COLOR_BG).pack(anchor="w", padx=6, pady=(4,4))
        self.detalle_text = tk.Text(self.right, height=10, width=40, state="disabled")
        self.detalle_text.pack(padx=6, pady=4)

        tk.Label(self.right, text="Calendario (días aprobados se marcarán aquí)", bg=COLOR_BG).pack(anchor="w", padx=6, pady=(8,4))
        self.calendar = Calendar(self.right, selectmode="none",
                         year=date.today().year,
                         month=date.today().month,
                         day=1,
                         font="Arial 12",
                         selectforeground="black",
                         selectbackground="#CCE7FF",
                         cursor="hand2")
        self.calendar.pack(padx=6, pady=4)

        self.calendar.bind("<<CalendarSelected>>", self._mostrar_info_dia)

        # leyenda
        lg = tk.Frame(self.right, bg=COLOR_BG)
        lg.pack(fill="x", padx=6, pady=(6,12))

        # --- Vacaciones ---
        tk.Label(lg, bg=COLOR_VAC_YELLOW, width=3).grid(row=0, column=0, padx=(0,6))
        self.lg_vac_lbl = tk.Label(lg, text="Vacaciones: 0", bg=COLOR_BG)
        self.lg_vac_lbl.grid(row=0, column=1, sticky="w")

        # --- Ausencias ---
        tk.Label(lg, bg=COLOR_AUS_BLUE, width=3).grid(row=1, column=0, padx=(0,6))
        self.lg_aus_lbl = tk.Label(lg, text="Ausencias: 0", bg=COLOR_BG)
        self.lg_aus_lbl.grid(row=1, column=1, sticky="w")

    # ---------------- FUNCIONES BD Y TREE ----------------
    # Dentro de tu ventana flotante actual
    def abrir_form_caracter(self):
        from caracter import VentanaCaracter
        # Crear la nueva ventana
        nueva_ventana = VentanaCaracter(self.master)  # pasamos la raíz principal
        nueva_ventana.focus_set()
        nueva_ventana.grab_set()
        # Cerrar la ventana actual donde está el botón
        self.destroy()

    def abrir_form_motivo(self):
        from motivo import VentanaMotivo
        nueva_ventana = VentanaMotivo(self.master)
        nueva_ventana.focus_set()
        nueva_ventana.grab_set()
        self.destroy()

    def _mostrar_info_dia(self, event):
        """Muestra en detalle_text la información de los días seleccionados."""
        sel_date = self.calendar.selection_get()
        if not sel_date:
            return
        conn = connect()
        if not conn:
            return
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            # Buscar permisos y vacaciones que incluyen esa fecha
            cur.execute(f"SELECT * FROM {TABLA_PERMISOS} WHERE estado='aprobada' AND fecha_inicio<=%s AND fecha_fin>=%s", (sel_date, sel_date))
            permisos = cur.fetchall()
            cur.execute("SELECT * FROM vacaciones WHERE estado='aprobada' AND fecha_inicio<=%s AND fecha_fin>=%s", (sel_date, sel_date))
            vacaciones = cur.fetchall()
            cur.close()
            conn.close()
            # Construir texto
            texto = f"Día: {sel_date}\n\n"
            for row in permisos:
                texto += f"Permiso: {row['nombre_completo']} ({row['tipo_permiso']})\n"
            for row in vacaciones:
                texto += f"Vacación: {row['nombre_completo']}\n"
            self.detalle_text.config(state="normal")
            self.detalle_text.delete("1.0", "end")
            self.detalle_text.insert("1.0", texto)
            self.detalle_text.config(state="disabled")
        except Exception:
            pass

    def load_solicitudes(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        conn = connect()
        if not conn:
            return
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            filtro = self.search_var.get()
            Query = f"""
            SELECT id, identidad, nombre_completo, tipo_permiso,
            fecha_inicio, fecha_fin, dias_solicitados, estado
            FROM {TABLA_PERMISOS}
            WHERE 
                CAST(id AS TEXT) ILIKE %s OR
                identidad ILIKE %s OR
                nombre_completo ILIKE %s OR
                tipo_permiso ILIKE %s
            ORDER BY creado_en DESC
            """
            like = f"%{filtro}%"
            cur.execute(Query, (like, like, like, like))
            rows = cur.fetchall()
            self.lg_aus_lbl.config(text=f"Ausencias: {len(rows)}")
            for row in rows:
                vals = (row["id"], row["identidad"], row["nombre_completo"], row["tipo_permiso"],
                        row["fecha_inicio"].strftime("%Y-%m-%d") if row["fecha_inicio"] else "",
                        row["fecha_fin"].strftime("%Y-%m-%d") if row["fecha_fin"] else "",
                        row["dias_solicitados"], row["estado"])
                iid = self.tree.insert("", "end", values=vals)
                # aplicar color por estado
                if row["estado"] == "pendiente":
                    self.tree.item(iid, tags=("pendiente",))
                elif row["estado"] == "aprobada":
                    self.tree.item(iid, tags=("aprobada",))
                elif row["estado"] == "rechazada":
                    self.tree.item(iid, tags=("rechazada",))
            self.tree.tag_configure("pendiente", background=COLOR_PENDING)
            self.tree.tag_configure("aprobada", background=COLOR_APPROVED)
            self.tree.tag_configure("rechazada", background=COLOR_REJECTED)
            cur.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar solicitudes:\n{e}")
        finally:
            conn.close()
            
        self.btn_aceptar.config(state="disabled")
        self.btn_rechazar.config(state="disabled")
        self.detalle_text.delete("1.0","end")
        self._limpiar_eventos_calendar()
        self._marcar_dias_aprobados()
        self.load_vacaciones()
    
    def load_vacaciones(self):
        for r in self.tree_v.get_children():
            self.tree_v.delete(r)

        conn = connect()
        if not conn:
            return

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM vacaciones ORDER BY creado_en DESC")
        rows = cur.fetchall()

        for row in rows:
            iid = self.tree_v.insert("", "end", values=(
                row["id"], row["identidad"], row["nombre_completo"],
                row["fecha_inicio"], row["fecha_fin"], row["dias_solicitados"],
                row["estado"]
            ))
            if row["estado"] == "pendiente":
                self.tree_v.item(iid, tags=("pend",))
            elif row["estado"] == "aprobada":
                self.tree_v.item(iid, tags=("ok",))
            else:
                self.tree_v.item(iid, tags=("bad",))

        self._marcar_dias_aprobados()

        conn.close()

    def load_vacaciones_filtradas(self):
        """Carga la tabla de vacaciones filtrando por nombre o identidad."""
        filtro = self.search_vac_var.get().strip().lower()

        conn = connect()
        if not conn:
            return

        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Consulta base
            query = "SELECT * FROM vacaciones ORDER BY creado_en DESC"
            cur.execute(query)
            rows = cur.fetchall()
            self.lg_vac_lbl.config(text=f"Vacaciones: {len(rows)}")
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar vacaciones:\n{e}")
            conn.close()
            return

        # Limpiar tabla
        for item in self.tree_vac.get_children():
            self.tree_vac.delete(item)

        # Insertar con filtro
        for row in rows:
            nombre = str(row["nombre_completo"]).lower()
            identidad = str(row["identidad"]).lower()

            if filtro in nombre or filtro in identidad:
                self.tree_vac.insert(
                    "",
                    "end",
                    values=(
                        row["id"],
                        row["identidad"],
                        row["nombre_completo"],
                        row["fecha_inicio"],
                        row["fecha_fin"],
                        row["dias_solicitados"],
                        row["estado"]
                   )
                )

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            self.btn_aceptar.config(state="disabled")
            self.btn_rechazar.config(state="disabled")
            return
        iid = sel[0]
        values = self.tree.item(iid)["values"]
        estado = values[7]
        if estado == "pendiente":
            self.btn_aceptar.config(state="normal")
            self.btn_rechazar.config(state="normal")
        else:
            self.btn_aceptar.config(state="disabled")
            self.btn_rechazar.config(state="disabled")
        self._cargar_detalle(values[0], tipo="permiso")

    def on_select_v(self, event):
        sel = self.tree_v.selection()
        if not sel:
            self.btn_aceptar_v.config(state="disabled")
            self.btn_rechazar_v.config(state="disabled")
            return
        iid = sel[0]
        estado = self.tree_v.item(iid)["values"][6]
        if estado == "pendiente":
            self.btn_aceptar_v.config(state="normal")
            self.btn_rechazar_v.config(state="normal")
        else:
            self.btn_aceptar_v.config(state="disabled")
            self.btn_rechazar_v.config(state="disabled")
        self._cargar_detalle(self.tree_v.item(iid)["values"][0], tipo="vacacion")

    def _cargar_detalle(self, solicitud_id, tipo="permiso"):
        conn = connect()
        if not conn:
            return
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            if tipo == "permiso":
                cur.execute(f"SELECT * FROM {TABLA_PERMISOS} WHERE id = %s", (solicitud_id,))
            elif tipo == "vacacion":
                cur.execute(f"SELECT * FROM vacaciones WHERE id = %s", (solicitud_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener detalle:\n{e}")
            conn.close()
            return

        # Habilitar Text para insertar contenido
        self.detalle_text.config(state="normal")
        self.detalle_text.delete("1.0", "end")

        if not row:
            self.detalle_text.config(state="disabled")
            return

        if tipo == "permiso":
            txt = (
                f"ID: {row['id']}\nIdentidad: {row['identidad']}\nNombre: {row['nombre_completo']}\n"
                f"Tipo: {row['tipo_permiso']}\nFecha entrega: {row['fecha_entrega']}\nInicio: {row['fecha_inicio']}\nFin: {row['fecha_fin']}\n"
                f"Días solicitados: {row['dias_solicitados']}\nCaracter: {row['caracter']}\nObservaciones:\n{row['observaciones'] or ''}\n"
                f"Estado: {row['estado']}\nConstancia: {row['constancia_path'] or '(no)'}"
            )
        elif tipo == "vacacion":
            txt = (
                f"ID: {row['id']}\nIdentidad: {row['identidad']}\nNombre: {row['nombre_completo']}\n"
                f"Inicio: {row['fecha_inicio']}\nFin: {row['fecha_fin']}\nDías solicitados: {row['dias_solicitados']}\n"
                f"Estado: {row['estado']}"
            )

        self.detalle_text.insert("1.0", txt)
        self.detalle_text.config(state="disabled")  # Volver a solo lectura

        # Lógica del calendario
        self._limpiar_eventos_calendar()
        if tipo == "permiso" and row["estado"] == "aprobada":
            inicio = row["fecha_inicio"]
            fin = row["fecha_fin"]
            if isinstance(inicio, datetime):
                inicio = inicio.date()
            if isinstance(fin, datetime):
                fin = fin.date()
            if inicio and fin:
                d = inicio
                while d <= fin:
                    tag = "vac" if row["tipo_permiso"]=="vacacion" else "aus"
                    self.calendar.calevent_create(d, f"{row['nombre_completo']}", tag)
                    d += timedelta(days=1)
                try:
                    self.calendar.tag_config("vac", background=COLOR_VAC_YELLOW)
                    self.calendar.tag_config("aus", background=COLOR_AUS_BLUE)
                except Exception:
                    pass

    def _limpiar_eventos_calendar(self):
        try:
            for ev in list(self.calendar.get_calevents()):
                self.calendar.calevent_remove(ev)
        except Exception:
            pass

    # ---------------- BOTONES ACEPTAR/RECHAZAR ----------------
    def aceptar_solicitud(self):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        solicitud_id = self.tree.item(iid)["values"][0]
        if not messagebox.askyesno("Confirmar", "¿Aceptar esta solicitud?"):
            return
        conn = connect()
        if not conn:
            return
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(f"SELECT * FROM {TABLA_PERMISOS} WHERE id = %s", (solicitud_id,))
            row = cur.fetchone()
            if not row:
                messagebox.showerror("Error", "Solicitud no encontrada.")
                cur.close()
                conn.close()
                return
            cur.execute(f"UPDATE {TABLA_PERMISOS} SET estado=%s, notificado_admin=%s WHERE id=%s",
                        ("aprobada", True, solicitud_id))
            if row["tipo_permiso"]=="vacacion" and row.get("dias_restantes_actual") is not None:
                nueva = max(0, row["dias_restantes_actual"]-row["dias_solicitados"])
                cur.execute(f"UPDATE {TABLA_PERMISOS} SET dias_restantes_actual=%s WHERE id=%s", (nueva, solicitud_id))
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo("Listo", "Solicitud aprobada.")
            self.load_solicitudes()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo aprobar solicitud:\n{e}")
            conn.close()

    def rechazar_solicitud(self):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        solicitud_id = self.tree.item(iid)["values"][0]
        if not messagebox.askyesno("Confirmar", "¿Desea rechazar esta solicitud?"):
            return
        conn = connect()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(f"UPDATE {TABLA_PERMISOS} SET estado=%s, notificado_admin=%s WHERE id=%s", ("rechazada", True, solicitud_id))
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo("Listo", "Solicitud rechazada.")
            self.load_solicitudes()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo rechazar:\n{e}")
            conn.close()

    def aceptar_vacacion(self):
        sel = self.tree_v.selection()
        if not sel:
            return
        iid = sel[0]
        vac_id = self.tree_v.item(iid)["values"][0]
        if not messagebox.askyesno("Confirmar", "¿Aceptar esta vacación?"):
            return
        conn = connect()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("UPDATE vacaciones SET estado=%s WHERE id=%s", ("aprobada", vac_id))
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo("Listo", "Vacación aprobada.")
            self.load_vacaciones()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo aprobar:\n{e}")
            conn.close()

    def rechazar_vacacion(self):
        sel = self.tree_v.selection()
        if not sel:
            return
        iid = sel[0]
        vac_id = self.tree_v.item(iid)["values"][0]
        if not messagebox.askyesno("Confirmar", "¿Desea rechazar esta vacación?"):
            return
        conn = connect()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("UPDATE vacaciones SET estado=%s WHERE id=%s", ("rechazada", vac_id))
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo("Listo", "Vacación rechazada.")
            self.load_vacaciones()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo rechazar:\n{e}")
            conn.close()

    def _marcar_dias_aprobados(self):
        """Marca automáticamente en el calendario los días de todas las solicitudes aprobadas."""
        conn = connect()
        if not conn:
            return
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            # Permisos aprobados
            cur.execute(f"SELECT * FROM {TABLA_PERMISOS} WHERE estado='aprobada'")
            permisos = cur.fetchall()
            # Vacaciones aprobadas
            cur.execute("SELECT * FROM vacaciones WHERE estado='aprobada'")
            vacaciones = cur.fetchall()
            cur.close()
            conn.close()

            self._limpiar_eventos_calendar()
            for row in permisos + vacaciones:
                inicio = row["fecha_inicio"]
                fin = row["fecha_fin"]
                nombre = row["nombre_completo"]
                tipo = row.get("tipo_permiso", "vacacion")
                if isinstance(inicio, datetime):
                    inicio = inicio.date()
                if isinstance(fin, datetime):
                    fin = fin.date()
                if inicio and fin:
                    d = inicio
                    while d <= fin:
                        tag = "vac" if tipo=="vacacion" else "aus"
                        self.calendar.calevent_create(d, f"{nombre}", tag)
                        d += timedelta(days=1)
            # Colores
            self.calendar.tag_config("vac", background=COLOR_VAC_YELLOW)
            self.calendar.tag_config("aus", background=COLOR_AUS_BLUE)
        except Exception:
            pass

    # ---------------- EXPORT ----------------
    def export_selected_pdf(self):
        import os
        import webbrowser
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        import psycopg2.extras
        from tkinter import filedialog, messagebox

        def toast(root, mensaje, bg="#28a745", fg="white", duration=3000):
            """
            Toast flotante con animación y fade-out.
            bg = color de fondo
            fg = color del texto
            duration = tiempo antes de desaparecer
            """
            import tkinter as tk

            toast = tk.Toplevel(root)
            toast.overrideredirect(True)
            toast.attributes("-topmost", True)

            # Posición esquina superior derecha
            x = root.winfo_x() + root.winfo_width() - 260
            y = root.winfo_y() + 20
            toast.geometry(f"250x40+{x}+{y}")

            frame = tk.Frame(toast, bg=bg)
            frame.pack(fill="both", expand=True)

            label = tk.Label(frame, text=mensaje, bg=bg, fg=fg, font=("Arial", 10))
            label.pack(expand=True)

            # Animación fade-out
            def fade():
                alpha = toast.attributes("-alpha")
                if alpha > 0:
                    alpha -= 0.05
                    toast.attributes("-alpha", alpha)
                    toast.after(50, fade)
                else:
                    toast.destroy()

            toast.attributes("-alpha", 0.0)

            # Fade-in
            def fade_in():
                alpha = toast.attributes("-alpha")
                if alpha < 1:
                    alpha += 0.1
                    toast.attributes("-alpha", alpha)
                    toast.after(30, fade_in)
                else:
                    # Cuando llega a 1, esperar duration y luego fade-out
                    toast.after(duration, fade)

            fade_in()

        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una solicitud para exportar.")
            return

        iid = sel[0]
        solicitud_id = self.tree.item(iid)["values"][0]

        conn = connect()
        if not conn:
            return

        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            # Traer toda la fila del permiso (aquí están nombre_completo, identidad, fechas, checks, constancia_path, etc.)
            cur.execute("SELECT * FROM permisos_dias_laborales WHERE id=%s", (solicitud_id,))
            permiso = cur.fetchone()
            if not permiso:
                cur.close()
                conn.close()
                messagebox.showerror("Error", "No se encontró la solicitud seleccionada.")
                return

            # Solo traer cargo y dependencia desde colaborador usando colaborador_id
            colaborador_id = permiso["colaborador_id"]
            cur.execute("SELECT cargo, dependencia FROM colaborador WHERE id=%s", (colaborador_id,))
            col = cur.fetchone() or {"cargo": "", "dependencia": ""}

            cur.close()
            conn.close()

        except Exception as e:
            try:
                conn.close()
            except:
                pass
            messagebox.showerror("Error", f"No se pudo obtener datos:\n{e}")
            return

        # Pedir nombre de archivo
        file = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            filetypes=[("PDF files", "*.pdf")])
        if not file:
            return

        try:
            c = canvas.Canvas(file, pagesize=landscape(A4))
            width, height = landscape(A4)

            # --- LOGOS Y ENCABEZADO (NO SE CAMBIA NADA) ---
            if os.path.exists("escudo.png"):
                c.drawImage("escudo.png", 30, height - 95, width=70, height=70, preserveAspectRatio=True, mask='auto')
            if os.path.exists("peh.png"):
                c.drawImage("peh.png", width - 200, height - 95, width=70, height=70, preserveAspectRatio=True, mask='auto')
            if os.path.exists("muni.jpg"):
                c.drawImage("muni.jpg", width - 110, height - 95, width=70, height=70, preserveAspectRatio=True, mask='auto')

            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width/2, height - 30, "MUNICIPALIDAD DE LA ESPERANZA")

            c.setFont("Helvetica", 11)
            c.drawCentredString(width/2, height - 50, "LA ESPERANZA, INTIBUCÁ, HONDURAS C.A.")
            c.drawCentredString(width/2, height - 70, "Tel: 2783-1818, 2783-1296, Fax: 2783-2124")
            c.drawCentredString(width/2, height - 90, "E-mail: munilaeza@yahoo.es   rrhh.municipalidadlaeza@gmail.com")

            # ===================================================================
            # =======================  TABLA PRINCIPAL  =========================
            # ===================================================================

            y = height - 150
            left = 20
            right = width - 20
            colw = (right - left) / 4

            # Helpers
            def titulo(x1, y1, x2, texto, fontsize=10):
                c.setFillColorRGB(0.55, 0.75, 1)
                c.rect(x1, y1, x2 - x1, 22, fill=1, stroke=1)
                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", fontsize)
                c.drawCentredString((x1+x2)/2, y1+6, texto)
                c.setFillColor(colors.black)

            def celda(x1, y1, x2, texto, fontsize=9):
                c.setFillColor(colors.white)
                c.rect(x1, y1, x2 - x1, 22, fill=1, stroke=1)
                c.setFont("Helvetica", fontsize)
                if texto:
                    c.drawString(x1+4, y1+7, str(texto))

            # --------------------------------------------------------------
            # FILA 1 → TÍTULO PRINCIPAL
            # --------------------------------------------------------------
            titulo(left, y, left + colw*3, "PERMISOS EN DÍAS LABORALES")
            titulo(left + colw*3, y, right, "FECHA DE ENTREGA")
            y -= 22

            # FILA 2 (valores)
            celda(left, y, left + colw*3, "")
            celda(left + colw*3, y, right, permiso.get("fecha_entrega"))
            y -= 32

            # --------------------------------------------------------------
            # FILA 3 → IDENTIDAD / NOMBRE / CARGO / DEPENDENCIA
            # -------------------------------------------------------------- 
            titulo(left, y, left + colw, "NUMERO DE IDENTIDAD")
            titulo(left + colw, y, left + colw*2, "NOMBRE COMPLETO")
            titulo(left + colw*2, y, left + colw*3, "CARGO DESEMPEÑADO")
            titulo(left + colw*3, y, right, "DEPENDENCIA")
            y -= 22

            # FILA 4 (valores)
            celda(left, y, left + colw, permiso.get("identidad"))
            celda(left + colw, y, left + colw*2, permiso.get("nombre_completo"))
            celda(left + colw*2, y, left + colw*3, col.get("cargo"))
            celda(left + colw*3, y, right, col.get("dependencia"))
            y -= 32

            # --------------------------------------------------------------
            # FILA 5 → DIA INICIO / DIA FINALIZACION
            # --------------------------------------------------------------
            titulo(left, y, left + colw*2, "DIA DE INICIO")
            titulo(left + colw*2, y, right, "DIA DE FINALIZACIÓN") 
            y -= 22

            # FILA 6 (valores)
            celda(left, y, left + colw*2, permiso.get("fecha_inicio"))
            celda(left + colw*2, y, right, permiso.get("fecha_fin"))
            y -= 32

            # --------------------------------------------------------------
            # FILA 7 → TÍTULO CARÁCTER Y MOTIVO
            # --------------------------------------------------------------
            titulo(left, y, right, "CARÁCTER Y MOTIVO")
            y -= 22

            # FILA 8
            texto_caracter = f"El permiso es de carácter: {permiso.get('caracter','')}"
            celda(left, y, right, texto_caracter)
            y -= 22

            # FILA 9
            texto_motivo = f"Por el motivo siguiente: {permiso.get('checks','')}"
            celda(left, y, right, texto_motivo)
            y -= 32

            # --------------------------------------------------------------
            # FOTO OPCIONAL
            # --------------------------------------------------------------
            if col.get("foto_path") and os.path.exists(col.get("foto_path")):
                try:
                    c.drawImage(col.get("foto_path"), right-120, y-140, width=110, height=130)
                except:
                    pass

            # --------------------------------------------------------------
            # FILA 10 OBSERVACIONES
            # --------------------------------------------------------------
            titulo(left, y, right, "OBSERVACIONES")
            y -= 22

            # Cuadro de constancia
            constancia = permiso.get("constancia_path") or ""
            c.setFont("Helvetica", 9)
            c.drawString(left+4, y+8, f"Constancia adjuntada: {constancia if constancia else 'No adjunta'}")

            # Cuadro grande de observaciones
            c.rect(left, y-100, right-left, 100, stroke=1, fill=0)

            obs = permiso.get("observaciones","")
            c.drawString(left+6, y-20, obs[:170])
            if len(obs) > 170: c.drawString(left+6, y-35, obs[170:340])
            if len(obs) > 340: c.drawString(left+6, y-50, obs[340:510])

            y -= 140

            # --------------------------------------------------------------
            # FILA 11 → FIRMAS
            # --------------------------------------------------------------
            firmas = ["Firma Alcalde Municipal", "Firma Coordinador UMAP", "Firma Jefe Inmediato", "Firma Empleado"]
            fw = (right-left)/4
            for i,f in enumerate(firmas):
                x1 = left + fw*i
                c.rect(x1, y, fw-6, 60, stroke=1, fill=0)
                c.setFont("Helvetica", 9)
                c.drawCentredString(x1 + (fw-6)/2, y+25, f)

            # Guardar
            c.save()
            os.startfile(file)
            toast(self.root, "PDF generado correctamente", bg="#28a745")

            # abrir el PDF automáticamente
            import os
            os.startfile(file)   # en Windows funciona perfecto

        except Exception as e:
            toast(self.root, "Error al generar el PDF", bg="#dc3545")

    def export_selected_pdf_vac(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una solicitud de vacaciones.")
            return
    
        solicitud_id = self.tree.item(sel[0])["values"][0]

        conn = connect()
        if not conn:
            return
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT * FROM vacaciones WHERE id=%s", (solicitud_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener la solicitud:\n{e}")
            conn.close()
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            title="Guardar Solicitud de Vacaciones"
        )
        if not filename:
            return

        try:
            c = canvas.Canvas(filename, pagesize=landscape(A4))
            width, height = landscape(A4)

            # ---------------- ENCABEZADO ----------------
            c.setFillColorRGB(0.20, 0.45, 0.75)  # Azul encabezado
            c.rect(0, height - 60, width, 60, fill=True, stroke=False)

            c.setFont("Helvetica-Bold", 20)
            c.setFillColor(colors.white)
            c.drawCentredString(width / 2, height - 40, "SOLICITUD DE VACACIONES")

            # ---------------- INFORMACIÓN EN TABLA ----------------
            data = [
                ["Campo", "Información"],
                ["Nombre Completo", row["nombre_completo"]],
                ["Identidad", row["identidad"]],
                ["Cargo", row.get("cargo", "")],
                ["Dependencia", row.get("dependencia", "")],
                ["Fecha de Inicio", str(row["fecha_inicio"])],
                ["Fecha de Finalización", str(row["fecha_fin"])],
                ["Días Solicitados", str(row["dias_solicitados"])],
                ["Estado", row["estado"]],
                ["Observaciones", row["observaciones"] or ""],
            ]

            table = Table(data, colWidths=[7*cm, 20*cm])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("ALIGN", (0,0), (-1,-1), "LEFT"),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE", (0,0), (-1,0), 14),
                ("BOTTOMPADDING", (0,0), (-1,0), 10),
            
                ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),
                ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
                ("FONTSIZE", (0,1), (-1,-1), 12),
                ("ROWHEIGHT", (0,1), (-1,-1), 20),
                ("GRID", (0,0), (-1,-1), 0.5, colors.gray),
            ]))

            table.wrapOn(c, width, height)
            table.drawOn(c, 40, height - 380)

            # ---------------- FIRMAS ----------------
            c.setFont("Helvetica", 12)
            y = 140
            c.drawString(60, y, "Firma del Empleado: ________________________________")
            c.drawString(400, y, "Firma del Jefe Inmediato: ________________________________")

            y -= 40
            c.drawString(60, y, "Firma RRHH: _______________________________________")
            c.drawString(400, y, "Firma Alcalde Municipal: ________________________________")

            c.save()
            messagebox.showinfo("PDF", f"PDF generado correctamente:\n{filename}")

        except Exception as e:
            messagebox.showerror("Error PDF", f"No se pudo generar PDF:\n{e}")

    def export_all_excel(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")])
        if not filename:
            return
        conn = connect()
        if not conn:
            return
        try:
            df = pd.read_sql_query(f"SELECT * FROM {TABLA_PERMISOS} ORDER BY creado_en DESC", conn)
            df.to_excel(filename, index=False)
            conn.close()
            messagebox.showinfo("Excel", f"Exportado a {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar Excel:\n{e}")
            conn.close()

# ---------------- RUN ----------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # esconder ventana principal
    win = SolicitudesFlotante()
    win.mainloop()