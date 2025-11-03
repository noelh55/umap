import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psycopg2
import pandas as pd
from tkcalendar import DateEntry
from PIL import Image, ImageTk
import os

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
    def __init__(self, root):
        self.root = root
        self.root.title("Reporte de Colaboradores")
        self.root.state("zoomed")
        self.root.configure(bg="#f4f6f9")

        # ---------------- CARD ----------------
        self.card_canvas = tk.Canvas(root, width=1200, height=700, bg=root["bg"], highlightthickness=0)
        self.card_canvas.place(relx=0.5, rely=0.5, anchor="center")
        self.round_rectangle(10, 10, 1190, 690, radius=25, fill="#ffffff", outline="#ffffff")
        self.card_frame = tk.Frame(self.card_canvas, bg="#ffffff")
        self.card_frame.place(x=0, y=0, width=1200, height=700)

        # ---------------- TÍTULO ----------------
        tk.Label(self.card_frame, text="Reporte de Colaboradores", font=("Segoe UI", 18, "bold"), bg="#ffffff").pack(pady=15)

        # ---------------- FILTROS ----------------
        filtros_frame = tk.Frame(self.card_frame, bg="#ffffff")
        filtros_frame.pack(pady=10, fill="x", padx=20)

        tk.Label(filtros_frame, text="Dependencia:", bg="#ffffff").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Label(filtros_frame, text="Cargo:", bg="#ffffff").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        tk.Label(filtros_frame, text="Tipo Contrato:", bg="#ffffff").grid(row=0, column=4, padx=5, pady=5, sticky="w")

        self.dependencia_var = tk.StringVar(value="Todos")
        self.cargo_var = tk.StringVar(value="Todos")
        self.tipo_var = tk.StringVar(value="Todos")

        self.dependencia_cb = ttk.Combobox(filtros_frame, values=["Todos", "Administración", "Finanzas", "Recursos Humanos", "Sistemas"], textvariable=self.dependencia_var, state="readonly", width=25)
        self.cargo_cb = ttk.Combobox(filtros_frame, values=["Todos", "Gerente", "Analista", "Asistente", "Técnico"], textvariable=self.cargo_var, state="readonly", width=25)
        self.tipo_cb = ttk.Combobox(filtros_frame, values=["Todos", "Permanente", "Especial", "Jornal"], textvariable=self.tipo_var, state="readonly", width=25)

        self.dependencia_cb.grid(row=0, column=1, padx=5, pady=5)
        self.cargo_cb.grid(row=0, column=3, padx=5, pady=5)
        self.tipo_cb.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(filtros_frame, text="Filtrar", command=self.cargar_tabla).grid(row=0, column=6, padx=10, pady=5)
        ttk.Button(filtros_frame, text="Exportar a Excel", command=self.exportar_excel).grid(row=0, column=7, padx=10, pady=5)

        # ---------------- TABLA ----------------
        self.tree_frame = tk.Frame(self.card_frame)
        self.tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columnas = ("ID", "Identidad", "Nombre", "Apellido", "Teléfono", "Profesión", "Tipo Contrato", "Dependencia", "Cargo", "Usuario", "Rol", "Unidad")
        self.tree = ttk.Treeview(self.tree_frame, columns=columnas, show="headings")
        for col in columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Cargar datos iniciales
        self.cargar_tabla()

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
        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            query = "SELECT id, identidad, nombre1, nombre2, apellido1, apellido2, telefono, profesion, tipo_contrato, dependencia, cargo, usuario, rol, unidad FROM empleados WHERE 1=1"

            if self.dependencia_var.get() != "Todos":
                query += f" AND dependencia='{self.dependencia_var.get()}'"
            if self.cargo_var.get() != "Todos":
                query += f" AND cargo='{self.cargo_var.get()}'"
            if self.tipo_var.get() != "Todos":
                query += f" AND tipo_contrato='{self.tipo_var.get()}'"

            cur.execute(query)
            rows = cur.fetchall()
            conn.close()

            for row in rows:
                nombre_completo = f"{row[2]} {row[3]} {row[4]} {row[5]}"
                self.tree.insert("", tk.END, values=(row[0], row[1], nombre_completo, row[4], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13]))

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la tabla:\n{e}")

    # ---------------- EXPORTAR EXCEL ----------------
    def exportar_excel(self):
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
            if not file_path:
                return

            data = []
            for row_id in self.tree.get_children():
                data.append(self.tree.item(row_id)["values"])

            df = pd.DataFrame(data, columns=["ID", "Identidad", "Nombre", "Apellido", "Teléfono", "Profesión", "Tipo Contrato", "Dependencia", "Cargo", "Usuario", "Rol", "Unidad"])
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Éxito", "Reporte exportado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")


# ---------------- RUN ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = ReporteEmpleados(root)
    root.mainloop()