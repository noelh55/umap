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

        # Treeview
        cols = ("id","identidad","nombre_completo","tipo_permiso","fecha_inicio","fecha_fin","dias_solicitados","estado")
        self.tree = ttk.Treeview(self.left, columns=cols, show="headings", height=20)
        for c in cols:
            self.tree.heading(c, text=c.replace("_"," ").title())
            self.tree.column(c, width=120, anchor="center")
        self.tree.pack(fill="x", expand=False, padx=6, pady=6)
        self.tree.configure(height=10)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.btn_pdf = tk.Button(self.left, text="Generar PDF", state="disabled", command=self.export_selected_pdf)
        self.btn_pdf.pack(pady=(4,6))

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

        # Buttons accept/reject
        btns = tk.Frame(self.left, bg=COLOR_BG)
        btns.pack(fill="x", pady=(4,8))
        self.btn_aceptar = tk.Button(btns, text="✅ Aceptar", bg="#27ae60", fg="white", command=self.aceptar_solicitud, state="disabled")
        self.btn_aceptar.pack(side="left", padx=6)
        self.btn_rechazar = tk.Button(btns, text="❌ Rechazar", bg="#e74c3c", fg="white", command=self.rechazar_solicitud, state="disabled")
        self.btn_rechazar.pack(side="left", padx=6)

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

        # leyenda
        lg = tk.Frame(self.right, bg=COLOR_BG)
        lg.pack(fill="x", padx=6, pady=(6,12))
        tk.Label(lg, text="Vacaciones", bg=COLOR_BG).grid(row=0,column=0,sticky="w")
        tk.Label(lg, bg=COLOR_VAC_YELLOW, width=3).grid(row=0,column=1,padx=6)
        tk.Label(lg, text="Ausencias", bg=COLOR_BG).grid(row=1,column=0,sticky="w")
        tk.Label(lg, bg=COLOR_AUS_BLUE, width=3).grid(row=1,column=1,padx=6)

    # ---------------- FUNCIONES BD Y TREE ----------------
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
        self.load_vacaciones()
        self.total_lbl = tk.Label(self.left, bg=COLOR_BG, font=("Segoe UI",10))
        self.total_lbl.pack(anchor="w")
        self.total_lbl.config(text=f"Total ausencias: {len(rows)}")

        self.btn_pdf.config(state="disabled")
    
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

        self.total_v_lbl = tk.Label(self.left, bg=COLOR_BG, font=("Segoe UI",10))
        self.total_v_lbl.pack(anchor="w")
        self.total_v_lbl.config(text=f"Total vacaciones: {len(rows)}")

        conn.close()

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
        self._cargar_detalle(values[0])

        self.btn_pdf.config(state="normal")

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
        self._cargar_detalle(self.tree_v.item(iid)["values"][0])

    def _cargar_detalle(self, solicitud_id):
        conn = connect()
        if not conn:
            return
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(f"SELECT * FROM {TABLA_PERMISOS} WHERE id = %s", (solicitud_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener detalle:\n{e}")
            conn.close()
            return

        self.detalle_text.delete("1.0","end")
        if not row:
            return
        txt = (
            f"ID: {row['id']}\nIdentidad: {row['identidad']}\nNombre: {row['nombre_completo']}\n"
            f"Tipo: {row['tipo_permiso']}\nFecha entrega: {row['fecha_entrega']}\nInicio: {row['fecha_inicio']}\nFin: {row['fecha_fin']}\n"
            f"Días solicitados: {row['dias_solicitados']}\nCaracter: {row['caracter']}\nObservaciones:\n{row['observaciones'] or ''}\n"
            f"Estado: {row['estado']}\nConstancia: {row['constancia_path'] or '(no)'}"
        )
        self.detalle_text.insert("1.0", txt)

        self._limpiar_eventos_calendar()
        if row["estado"] == "aprobada":
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

    # ---------------- EXPORT ----------------
    def export_selected_pdf(self):
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
            cur.execute(f"SELECT * FROM {TABLA_PERMISOS} WHERE id=%s", (solicitud_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener solicitud:\n{e}")
            conn.close()
            return

        filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
        if not filename:
            return

        try:
            c = canvas.Canvas(filename, pagesize=A4)
            width, height = A4

            # Logos (puedes ajustar rutas)
            logo_path1 = "municipio.png"  # reemplazar con ruta logo municipio
            logo_path2 = "honduras.png"   # reemplazar con ruta logo Honduras
            if os.path.exists(logo_path1):
                c.drawImage(logo_path1, 30, height-110, width=80, height=80, preserveAspectRatio=True)
            if os.path.exists(logo_path2):
                c.drawImage(logo_path2, width-110, height-110, width=80, height=80, preserveAspectRatio=True)

            # Títulos y subtítulos
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(width/2, height-50, "MUNICIPALIDAD DE LA ESPERANZA")
            c.setFont("Helvetica", 11)
            c.drawCentredString(width/2, height-70, "PERMISO EN DÍAS LABORALES")

            # Cajas y campos según imagen
            y = height-130
            line_height = 18
            c.setFont("Helvetica", 10)
            campos = [
                ("Nombre y Apellido", row["nombre_completo"]),
                ("Número de Identidad", row["identidad"]),
                ("Cargo Desempeñado", row.get("cargo", "")),
                ("Dependencia", row.get("dependencia", "")),
                ("Día de inicio", str(row.get("fecha_inicio",""))),
                ("Día de finalización", str(row.get("fecha_fin",""))),
                ("Caracter oficial/personal", row.get("caracter","")),
                ("Observaciones", row.get("observaciones","")),
            ]
            for label, valor in campos:
                c.drawString(50, y, f"{label}: {valor}")
                y -= line_height

            # Firmas (solo cuadros)
            y -= 30
            c.drawString(60, y, "Firma Empleado: _____________________")
            c.drawString(250, y, "Firma Jefe Inmediato: _____________________")
            y -= 25
            c.drawString(60, y, "Firma Coordinador UMAP: _____________________")
            c.drawString(250, y, "Firma Alcalde Municipal: _____________________")

            c.save()
            messagebox.showinfo("PDF", f"PDF guardado en: {filename}")
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