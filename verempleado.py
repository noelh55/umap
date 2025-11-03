import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from openpyxl import Workbook
import os
import sys
import subprocess
from datetime import date, timedelta
import psycopg2

# ---- Configuración PostgreSQL ----
DB_CONFIG = {
    "host": "localhost",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

# ---- Colores y estilos ----
BG = "#ecf0f1"
FRAME_BG = "#34495e"
BTN_BG = "#1abc9c"
BTN_HOVER = "#16a085"
TEXT_COLOR = "#2c3e50"
ENTRY_BG = "#ffffff"

class ColaboradorWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Gestión de Colaboradores")
        self.master.geometry("1100x700")
        self.master.configure(bg=BG)
        self.master.state("zoomed")

        # Variables de filtro
        self.estado_var = tk.StringVar(value="Todos")
        self.tipo_contrato_var = tk.StringVar(value="Todos")
        self.id_var = tk.StringVar()
        self.identidad_var = tk.StringVar()
        self.nombre_var = tk.StringVar()
        self.sueldo_var = tk.StringVar()
        self.cargo_var = tk.StringVar()
        self.dependencia_var = tk.StringVar()

        # Frame principal
        main_frame = tk.Frame(self.master, bg=BG, padx=15, pady=15)
        main_frame.pack(fill="both", expand=True)

        # ==== Filtros ==== #
        filtros_frame = tk.LabelFrame(
            main_frame,
            text="Filtros de Búsqueda",
            bg=BG,
            fg=TEXT_COLOR,
            font=("Segoe UI", 12, "bold"),
            padx=25,
            pady=25,
            bd=2,
            relief="groove"
        )
        filtros_frame.pack(fill="x", pady=10)

        # --- Primera fila de filtros ---
        fila1 = tk.Frame(filtros_frame, bg=BG)
        fila1.pack(pady=8)

        tk.Label(fila1, text="Estado:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=8)
        estado_cb = ttk.Combobox(fila1, textvariable=self.estado_var,
                                 values=["Todos", "Activo", "Inactivo"], state="readonly", width=20)
        estado_cb.grid(row=0, column=1, padx=8)
        estado_cb.bind("<<ComboboxSelected>>", lambda e: self.actualizar_tabla())

        tk.Label(fila1, text="Tipo Contrato:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=8)
        tipo_cb = ttk.Combobox(fila1, textvariable=self.tipo_contrato_var,
                               values=["Todos", "Jornal", "Contrato Especial"], state="readonly", width=20)
        tipo_cb.grid(row=0, column=3, padx=8)
        tipo_cb.bind("<<ComboboxSelected>>", lambda e: self.actualizar_tabla())

        tk.Label(fila1, text="Dependencia:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=4, padx=8)
        tk.Entry(fila1, textvariable=self.dependencia_var, bg=ENTRY_BG, width=25, font=("Segoe UI", 10)).grid(row=0, column=5, padx=8)

        tk.Label(fila1, text="Cargo:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=6, padx=8)
        tk.Entry(fila1, textvariable=self.cargo_var, bg=ENTRY_BG, width=25, font=("Segoe UI", 10)).grid(row=0, column=7, padx=8)

        for col in range(8):
            fila1.grid_columnconfigure(col, weight=1)

        # --- Segunda fila ---
        fila2 = tk.Frame(filtros_frame, bg=BG)
        fila2.pack(pady=8)

        tk.Label(fila2, text="ID:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=8)
        tk.Entry(fila2, textvariable=self.id_var, bg=ENTRY_BG, width=20, font=("Segoe UI", 10)).grid(row=0, column=1, padx=8)

        tk.Label(fila2, text="Identidad:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=8)
        tk.Entry(fila2, textvariable=self.identidad_var, bg=ENTRY_BG, width=25, font=("Segoe UI", 10)).grid(row=0, column=3, padx=8)

        tk.Label(fila2, text="Nombre:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=4, padx=8)
        tk.Entry(fila2, textvariable=self.nombre_var, bg=ENTRY_BG, width=30, font=("Segoe UI", 10)).grid(row=0, column=5, padx=8)

        tk.Label(fila2, text="Sueldo:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=6, padx=8)
        tk.Entry(fila2, textvariable=self.sueldo_var, bg=ENTRY_BG, width=20, font=("Segoe UI", 10)).grid(row=0, column=7, padx=8)

        for col in range(8):
            fila2.grid_columnconfigure(col, weight=1)

        # --- Tercera fila (Fechas) ---
        fila3 = tk.Frame(filtros_frame, bg=BG)
        fila3.pack(pady=8)

        tk.Label(fila3, text="Desde:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=8)
        self.anio_inicio = DateEntry(fila3, date_pattern="yyyy-mm-dd", width=18, background="#1abc9c", foreground="white")
        self.anio_inicio.grid(row=0, column=1, padx=8)
        self.anio_inicio.bind("<<DateEntrySelected>>", lambda e: self.actualizar_tabla())

        tk.Label(fila3, text="Hasta:", bg=BG, fg=TEXT_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=8)
        self.anio_fin = DateEntry(fila3, date_pattern="yyyy-mm-dd", width=18, background="#3498db", foreground="white")
        self.anio_fin.grid(row=0, column=3, padx=8)
        self.anio_fin.bind("<<DateEntrySelected>>", lambda e: self.actualizar_tabla())

        for col in range(4):
            fila3.grid_columnconfigure(col, weight=1)

        # ==== Tabla ==== #
        tabla_frame = tk.Frame(main_frame, bg=BG, bd=2, relief="groove", height=350)  # altura reducida
        tabla_frame.pack(fill="x", pady=10)  # fill solo en X para no estirarse verticalmente

        columnas = ("id", "identidad", "nombre", "tipo_contrato", "dependencia", "cargo",
                    "fecha_inicio", "fecha_fin", "sueldo", "estado")
        self.tree = ttk.Treeview(tabla_frame, columns=columnas, show="headings", height=12)  # menos filas visibles

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                        background=FRAME_BG, foreground=TEXT_COLOR)
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=25, background="white", fieldbackground="white")

        for col in columnas:
            self.tree.heading(col, text=col.replace("_", " ").capitalize())
            self.tree.column(col, anchor="center", width=120)

        vsb = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        tabla_frame.columnconfigure(0, weight=1)
        tabla_frame.rowconfigure(0, weight=1)

        # ==== Botones ==== #
        btns_frame = tk.Frame(main_frame, bg=BG)
        btns_frame.pack(pady=20)

        tk.Button(btns_frame, text="📄 Exportar PDF", bg="#e74c3c", fg="white", font=("Segoe UI", 11, "bold"),
                relief="flat", width=18, height=2, command=self.exportar_pdf).grid(row=0, column=0, padx=15)
        tk.Button(btns_frame, text="📊 Exportar Excel", bg="#2ecc71", fg="white", font=("Segoe UI", 11, "bold"),
                relief="flat", width=18, height=2, command=self.exportar_excel).grid(row=0, column=1, padx=15)
        tk.Button(btns_frame, text="🖨️ Imprimir", bg="#3498db", fg="white", font=("Segoe UI", 11, "bold"),
                relief="flat", width=18, height=2, command=self.imprimir_pdf).grid(row=0, column=2, padx=15)
        tk.Button(btns_frame, text="🧹 Limpiar Filtros", bg="#f1c40f", fg="black", font=("Segoe UI", 11, "bold"),
                relief="flat", width=18, height=2, command=self.limpiar).grid(row=0, column=3, padx=15)
        tk.Button(btns_frame, text="↩️ Regresar", bg="#9b59b6", fg="white", font=("Segoe UI", 11, "bold"),
                relief="flat", width=18, height=2, command=self.volver_main).grid(row=0, column=4, padx=15)

        # ---- Actualizar estado automático ----
        self.actualizar_estados_bd()
        self.actualizar_tabla()

    # ---- Conexión y consulta ---- #
    def obtener_empleados(self):
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, identidad, nombre1, nombre2, apellido1, apellido2,
                   tipo_contrato, dependencia, cargo, fecha_inicio, fecha_finalizacion, sueldo, estado
            FROM empleados
        """)
        empleados = cur.fetchall()
        conn.close()
        return empleados

    # ---- Actualizar estados automáticamente según fecha final ---- #
    def actualizar_estados_bd(self):
        hoy = date.today()
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            UPDATE empleados
            SET estado = 'Inactivo'
            WHERE fecha_finalizacion IS NOT NULL AND fecha_finalizacion < %s;
        """, (hoy,))
        cur.execute("""
            UPDATE empleados
            SET estado = 'Activo'
            WHERE fecha_finalizacion IS NULL OR fecha_finalizacion >= %s;
        """, (hoy,))

        conn.commit()
        conn.close()

    # ---- Filtrado actualizado ---- #
    def filtrar_empleados(self, empleados):
        estado_filtro = self.estado_var.get()
        tipo_filtro = self.tipo_contrato_var.get()
        fecha_inicio = self.anio_inicio.get_date()
        fecha_fin = self.anio_fin.get_date()

        id_filtro = self.id_var.get().strip().lower()
        identidad_filtro = self.identidad_var.get().strip().lower()
        nombre_filtro = self.nombre_var.get().strip().lower()
        sueldo_filtro = self.sueldo_var.get().strip().lower()
        cargo_filtro = self.cargo_var.get().strip().lower()
        dep_filtro = self.dependencia_var.get().strip().lower()

        filtrados = []
        for emp in empleados:
            (id_, identidad, n1, n2, a1, a2, tipo, dep, cargo, fi, ff, sueldo, estado) = emp
            fi_date = fi if isinstance(fi, date) else date.fromisoformat(fi)
            ff_date = ff if isinstance(ff, date) else (date.fromisoformat(ff) if ff else None)
            nombre = f"{n1} {n2 or ''} {a1} {a2 or ''}".strip()

            # Filtros
            if estado_filtro != "Todos" and estado != estado_filtro:
                continue
            if tipo_filtro != "Todos" and tipo != tipo_filtro:
                continue
            if id_filtro and id_filtro not in str(id_).lower():
                continue
            if identidad_filtro and identidad_filtro not in str(identidad).lower():
                continue
            if nombre_filtro and nombre_filtro not in nombre.lower():
                continue
            if sueldo_filtro and sueldo_filtro not in str(sueldo).lower():
                continue
            if cargo_filtro and cargo_filtro not in cargo.lower():
                continue
            if dep_filtro and dep_filtro not in dep.lower():
                continue

            # Rango de fechas (solo lunes-viernes)
            fecha_valida = False
            current = fi_date
            while current <= (ff_date or fi_date):
                if fecha_inicio <= current <= fecha_fin and current.weekday() < 5:
                    fecha_valida = True
                    break
                current += timedelta(days=1)
            if not fecha_valida:
                continue

            filtrados.append((id_, identidad, nombre, tipo, dep, cargo, fi, ff or "", sueldo, estado))
        return filtrados

    # ---- Actualizar tabla ---- #
    def actualizar_tabla(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        empleados = self.obtener_empleados()
        filtrados = self.filtrar_empleados(empleados)
        for emp in filtrados:
            self.tree.insert("", "end", values=emp)

    # ---- Limpiar filtros ---- #
    def limpiar(self):
        for var in [self.estado_var, self.tipo_contrato_var, self.id_var, self.identidad_var,
                    self.nombre_var, self.sueldo_var, self.cargo_var, self.dependencia_var]:
            var.set("")
        self.estado_var.set("Todos")
        self.tipo_contrato_var.set("Todos")

        self.anio_inicio.set_date(date.today())
        self.anio_fin.set_date(date.today())

        self.actualizar_tabla()

    # ---- Exportar PDF ---- #
    def exportar_pdf(self):
        data = [self.tree.item(i, "values") for i in self.tree.get_children()]
        if not data:
            messagebox.showwarning("Sin datos", "No hay información para exportar.")
            return

        pdf_path = "reporte_colaboradores.pdf"
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica", 10)
        c.drawString(50, 750, "Reporte de Colaboradores UMAP")
        y = 720
        headers = ["ID", "Identidad", "Nombre", "Contrato", "Dependencia", "Cargo", "Inicio", "Fin", "Sueldo", "Estado"]
        x_positions = [30, 70, 150, 260, 330, 420, 500, 570, 630, 690]

        for i, h in enumerate(headers):
            c.drawString(x_positions[i], y, h)

        y -= 20
        for row in data:
            if y < 50:
                c.showPage()
                y = 750
            for i, val in enumerate(row):
                c.drawString(x_positions[i], y, str(val))
            y -= 18

        c.save()
        messagebox.showinfo("Éxito", f"PDF generado: {pdf_path}")
        self.ultimo_pdf = pdf_path

    # ---- Exportar Excel ---- #
    def exportar_excel(self):
        data = [self.tree.item(i, "values") for i in self.tree.get_children()]
        if not data:
            messagebox.showwarning("Sin datos", "No hay información para exportar.")
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Colaboradores"
        headers = ["ID", "Identidad", "Nombre", "Contrato", "Dependencia", "Cargo", "Inicio", "Fin", "Sueldo", "Estado"]
        ws.append(headers)
        for row in data:
            ws.append(row)

        filename = "reporte_colaboradores.xlsx"
        wb.save(filename)
        messagebox.showinfo("Éxito", f"Excel generado: {filename}")

    # ---- Imprimir PDF ---- #
    def imprimir_pdf(self):
        if not hasattr(self, "ultimo_pdf") or not os.path.exists(self.ultimo_pdf):
            messagebox.showwarning("Atención", "Primero genere el PDF.")
            return
        try:
            os.startfile(self.ultimo_pdf, "print")
        except Exception:
            try:
                subprocess.run(["xdg-open", self.ultimo_pdf])
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el PDF: {e}")

    # ---- Volver a Main ---- #
    def volver_main(self):
        self.master.destroy()
        import Main
        os.execl(sys.executable, sys.executable, "Main.py")

# ==== Ejecutar ventana ==== #
if __name__ == "__main__":
    root = tk.Tk()
    app = ColaboradorWindow(root)

    # ---- Búsqueda en tiempo real ----
    for var in [app.id_var, app.identidad_var, app.nombre_var, app.sueldo_var, app.cargo_var, app.dependencia_var]:
        var.trace_add("write", lambda *args: app.actualizar_tabla())
    
    # Combos también filtran en tiempo real
    app.estado_var.trace_add("write", lambda *args: app.actualizar_tabla())
    app.tipo_contrato_var.trace_add("write", lambda *args: app.actualizar_tabla())

    root.mainloop()