import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import psycopg2
import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# ---------------- CONFIGURACIÓN BD ----------------
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

# ---------------- VENTANA DE REPORTE ----------------
class ReporteEmpleados:
    def __init__(self, master):
        # ---------------- VENTANA FLOTAENTE ----------------
        self.root = tk.Toplevel(master)
        self.root.title("Reporte Tipo Contrato")
        self.root.configure(bg="#f4f6f9")
        self.root.resizable(False, False)
        self.root.transient(master)
        self.root.grab_set()

        # Centrar ventana
        ancho, alto = 1200, 700
        x = (self.root.winfo_screenwidth() - ancho)//2
        y = (self.root.winfo_screenheight() - alto)//2
        self.root.geometry(f"{ancho}x{alto}+{x}+{y}")

        self.grafico_visible = False
        self.tabla_datos_previos = []

        # ---------------- CARD ----------------
        self.card_canvas = tk.Canvas(self.root, width=1200, height=700, bg=self.root["bg"], highlightthickness=0)
        self.card_canvas.place(relx=0.5, rely=0.5, anchor="center")
        self.round_rectangle(10, 10, 1190, 690, radius=25, fill="#ffffff", outline="#ffffff")
        self.card_frame = tk.Frame(self.card_canvas, bg="#ffffff")
        self.card_frame.place(x=0, y=0, width=1200, height=700)

        # ---------------- TÍTULO ----------------
        tk.Label(self.card_frame, text="Reporte por Tipo de Contrato",
                 font=("Segoe UI", 18, "bold"), bg="#ffffff").pack(pady=15)

        # ---------------- FILTROS ----------------
        filtros_frame = tk.Frame(self.card_frame, bg="#ffffff")
        filtros_frame.pack(pady=10, fill="x", padx=20)

        tk.Label(filtros_frame, text="Tipo Contrato:", bg="#ffffff").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.tipo_var = tk.StringVar(value="Todos")
        self.tipo_cb = ttk.Combobox(filtros_frame, textvariable=self.tipo_var,
                                    state="readonly", width=25)
        self.tipo_cb.grid(row=0, column=1, padx=5, pady=5)
        self.tipo_cb.bind("<<ComboboxSelected>>", lambda e: self.cargar_tabla())

        ttk.Button(filtros_frame, text="Limpiar Filtro", command=self.limpiar_filtro).grid(row=0, column=2, padx=10)
        ttk.Button(filtros_frame, text="Generar PDF", command=self.generar_pdf).grid(row=0, column=3, padx=10)
        ttk.Button(filtros_frame, text="Generar Excel", command=self.exportar_excel).grid(row=0, column=4, padx=10)
        self.boton_grafico = ttk.Button(filtros_frame, text="Ver Gráfico", command=self.toggle_grafico)
        self.boton_grafico.grid(row=0, column=5, padx=10)
        #ttk.Button(filtros_frame, text="Regresar", command=self.regresar).grid(row=0, column=7, padx=10)
        ttk.Button(filtros_frame, text="Cerrar", command=self.cerrar_ventana).grid(row=0, column=6, padx=10)

        self.cargar_comboboxes()

        # ---------------- ÁREA TABLA / GRÁFICO ----------------
        self.contenedor = tk.Frame(self.card_frame, bg="#ffffff")
        self.contenedor.pack(fill="both", expand=True, padx=20, pady=10)

        self.crear_tabla()
        self.cargar_tabla()
        self.tipo_cb.bind("<<ComboboxSelected>>", lambda e: self.actualizar_vista())

    # ---------------- CREAR TABLA ----------------
    def crear_tabla(self):
        if hasattr(self, "tree_frame"):
            self.tree_frame.destroy()

        self.tree_frame = tk.Frame(self.contenedor, bg="#ffffff")
        self.tree_frame.pack(fill="both", expand=True)

        columnas = ("#", "ID", "Identidad", "Nombre", "Apellido", "Teléfono",
                    "Profesión", "Tipo Contrato", "Dependencia", "Cargo",
                    "Usuario", "Rol", "Unidad")

        self.tree = ttk.Treeview(self.tree_frame, columns=columnas, show="headings", selectmode="browse", height=20)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#4a7abc", foreground="white")
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=25, background="#f9f9f9")

        for col in columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.column("#", width=50)

        self.tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        if not hasattr(self, "contador_label"):
            self.contador_label = tk.Label(self.card_frame, text="", bg="#ffffff", font=("Segoe UI", 12, "bold"))
            self.contador_label.pack(pady=5)

    # ---------------- LIMPIAR FILTRO ----------------
    def limpiar_filtro(self):
        self.tipo_var.set("Todos")
        self.cargar_tabla()

    def actualizar_vista(self):
        """Actualiza la tabla o el gráfico según lo que se esté mostrando."""
        if self.grafico_visible:
            self.mostrar_grafico()  # vuelve a dibujar el gráfico con el nuevo filtro
        else:
            self.cargar_tabla()  # recarga la tabla con el nuevo filtro

    # ---------------- CAMBIAR A GRÁFICO O TABLA ----------------
    def toggle_grafico(self):
        if self.grafico_visible:
            # Volver a tabla
            self.canvas_graph.get_tk_widget().destroy()
            self.crear_tabla()
            for row in self.tabla_datos_previos:
                self.tree.insert("", tk.END, values=row)
            self.contador_label.config(text=f"Total de registros: {len(self.tabla_datos_previos)}")
            self.boton_grafico.config(text="Ver Gráfico")
            self.grafico_visible = False
        else:
            # Mostrar gráfico
            for w in self.contenedor.winfo_children():
                w.destroy()
            self.mostrar_grafico()
            self.boton_grafico.config(text="Volver a Tabla")
            self.grafico_visible = True

    # ---------------- MOSTRAR GRÁFICO DONUT ----------------
    def mostrar_grafico(self):
        # Primero, limpiar contenedor
        for w in self.contenedor.winfo_children():
            w.destroy()

        data = self.obtener_datos_grafico()
        if not data:
            self.mostrar_toast("No hay datos para el filtro seleccionado")
            return

        labels = list(data.keys())
        values = list(data.values())

        fig, ax = plt.subplots(figsize=(7, 7))
        wedges, _ = ax.pie(values, wedgeprops=dict(width=0.45), startangle=90)
        ax.set_title("Distribución por Tipo de Contrato")
        ax.legend(wedges, labels, title="Tipos", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

        circle = plt.Circle((0, 0), 0.30, color='white')
        fig.gca().add_artist(circle)

        if hasattr(self, "canvas_graph"):
            self.canvas_graph.get_tk_widget().destroy()

        self.canvas_graph = FigureCanvasTkAgg(fig, master=self.contenedor)
        self.canvas_graph.draw()
        self.canvas_graph.get_tk_widget().pack(fill="both", expand=True)
        self.grafico_visible = True

    # ---------------- DATOS PARA GRÁFICO ----------------
    def obtener_datos_grafico(self):
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        if self.tipo_var.get() == "Todos":
            cur.execute("SELECT tipo_contrato, COUNT(*) FROM colaborador GROUP BY tipo_contrato")
        else:
            cur.execute("SELECT tipo_contrato, COUNT(*) FROM colaborador WHERE tipo_contrato=%s GROUP BY tipo_contrato",
                        (self.tipo_var.get(),))

        data = {row[0]: row[1] for row in cur.fetchall()}
        conn.close()
        return data

    # ---------------- CARGAR COMBOBOX ----------------
    def cargar_comboboxes(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT nombre FROM contratos ORDER BY nombre")
            contratos = [row[0] for row in cur.fetchall()]
            self.tipo_cb['values'] = ["Todos"] + contratos
            conn.close()
        except Exception as e:
            self.mostrar_toast(f"Error al cargar tipos: {e}")

    # ---------------- RECTÁNGULO REDONDEADO ----------------
    def round_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [x1+radius, y1,
                  x2-radius, y1,
                  x2, y1,
                  x2, y1+radius,
                  x2, y2-radius,
                  x2, y2,
                  x2-radius, y2,
                  x1+radius, y2,
                  x1, y2,
                  x1, y2-radius,
                  x1, y1+radius,
                  x1, y1]
        return self.card_canvas.create_polygon(points, smooth=True, **kwargs)

    # ---------------- CARGAR TABLA ----------------
    def cargar_tabla(self):
        self.tipo_cb.bind("<<ComboboxSelected>>", lambda e: self.actualizar_vista())
        if self.grafico_visible:
            return

        # Limpiar tabla
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            query = """SELECT id, identidad, nombre1, nombre2, apellido1, apellido2, telefono, profesion,
                              tipo_contrato, dependencia, cargo, usuario, rol, unidad 
                       FROM colaborador WHERE 1=1"""
            if self.tipo_var.get() != "Todos":
                query += " AND tipo_contrato=%s"
                cur.execute(query, (self.tipo_var.get(),))
            else:
                cur.execute(query)
            rows = cur.fetchall()
            conn.close()

            self.tabla_datos_previos = []
            for idx, row in enumerate(rows, start=1):
                nombre_completo = f"{row[2]} {row[3]} {row[4]} {row[5]}"
                values = (idx, row[0], row[1], nombre_completo, row[4],
                          row[6], row[7], row[8], row[9], row[10],
                          row[11], row[12], row[13])
                self.tree.insert("", tk.END, values=values)
                self.tabla_datos_previos.append(values)

            self.contador_label.config(text=f"Total de registros: {len(self.tabla_datos_previos)}")

        except Exception as e:
            self.mostrar_toast(f"Error al cargar tabla: {e}")

    def regresar(self):
        self.root.destroy()
        from contrato import VentanaContrato
        VentanaContrato(self.root.master)

    # ---------------- EXPORTAR EXCEL ----------------
    def exportar_excel(self):
        try:
            file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
            if not file:
                return
            df = pd.DataFrame(self.tabla_datos_previos, columns=["#","ID","Identidad","Nombre","Apellido","Teléfono",
                    "Profesión","Tipo Contrato","Dependencia","Cargo","Usuario","Rol","Unidad"])
            df.to_excel(file, index=False)
            self.mostrar_toast("Excel generado correctamente.")
        except Exception as e:
            self.mostrar_toast(f"No se pudo exportar: {e}")

    # ---------------- GENERAR PDF ----------------
    def generar_pdf(self):
        try:
            file = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
            if not file:
                return
            c = canvas.Canvas(file, pagesize=landscape(A4))
            width, height = landscape(A4)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(30, height - 40, "Reporte por Tipo de Contrato")
            columnas = ["#","ID","Identidad","Nombre","Apellido","Teléfono",
                        "Profesión","Tipo Contrato","Dependencia","Cargo",
                        "Usuario","Rol","Unidad"]
            col_width = (width - 60) / len(columnas)
            y = height - 80
            c.setFillColorRGB(0.29, 0.47, 0.73)  # Azul
            c.rect(30, y - 15, width - 60, 20, stroke=1, fill=1)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 8)
            for i, col in enumerate(columnas):
                c.drawString(35 + i * col_width, y, col)
            y -= 25
            total = 0
            for row in self.tabla_datos_previos:
                total += 1
                c.setFillColorRGB(0.93, 0.93, 0.93) if total % 2 == 0 else c.setFillColorRGB(1, 1, 1)
                c.rect(30, y - 15, width - 60, 20, stroke=0, fill=1)
                c.setFillColorRGB(0, 0, 0)
                c.setFont("Helvetica", 7)
                for i, val in enumerate(row):
                    c.drawString(35 + i * col_width, y, str(val))
                y -= 20
                if y < 40:
                    c.showPage()
                    y = height - 40
            c.setFont("Helvetica-Bold", 10)
            c.drawString(30, y - 20, f"Total de registros: {total}")
            c.save()
            self.mostrar_toast("PDF generado correctamente.")
        except Exception as e:
            self.mostrar_toast(f"No se pudo generar el PDF: {e}")

    # ---------------- TOAST ----------------
    def mostrar_toast(self, mensaje, duracion=2000):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.configure(bg="#333333")
        toast.attributes("-topmost", True)
        toast.attributes("-alpha", 0.0)
        self.root.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() - 300
        y = self.root.winfo_y() + 20
        toast.geometry(f"250x50+{x}+{y}")
        lbl = tk.Label(toast, text=mensaje, bg="#333333", fg="white", font=("Segoe UI", 10, "bold"))
        lbl.pack(expand=True, fill="both")

        def fade_in(alpha=0.0):
            alpha += 0.05
            if alpha >= 1.0:
                toast.after(duracion, fade_out)
                return
            toast.attributes("-alpha", alpha)
            toast.after(30, lambda: fade_in(alpha))

        def fade_out(alpha=1.0):
            alpha -= 0.05
            if alpha <= 0.0:
                toast.destroy()
                return
            toast.attributes("-alpha", alpha)
            toast.after(30, lambda: fade_out(alpha))

        fade_in()

    # ---------------- CERRAR VENTANA ----------------
    def cerrar_ventana(self):
        self.root.destroy()