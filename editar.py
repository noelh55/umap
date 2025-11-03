import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import date
import psycopg2
import shutil
import os

DB_CONFIG = {
    "host": "localhost",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "tu_contraseña"
}

UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

CONTRACT_TYPES = ["Permanente", "Especial", "Jornal"]
ESTADOS = ["Activo", "Inactivo"]


def copy_file_to_uploads(src_path, prefix):
    if not src_path or not os.path.isfile(src_path):
        return None
    filename = os.path.basename(src_path)
    name = f"{prefix}_{date.today().isoformat()}_{filename}"
    dest = os.path.join(UPLOADS_DIR, name)
    shutil.copy2(src_path, dest)
    return dest


class EditEmpleadoForm:
    def __init__(self, master, empleado_id):
        self.master = master
        self.empleado_id = empleado_id
        self.master.title("Editar Empleado")
        self.master.geometry("1000x750")
        self.master.configure(bg="#f4f6f9")

        # ---- Variables ----
        self.identidad = tk.StringVar()
        self.nombre1 = tk.StringVar()
        self.nombre2 = tk.StringVar()
        self.apellido1 = tk.StringVar()
        self.apellido2 = tk.StringVar()
        self.profesion = tk.StringVar()
        self.telefono = tk.StringVar()
        self.direccion = tk.StringVar()
        self.dependencia = tk.StringVar()
        self.cargo = tk.StringVar()
        self.sueldo = tk.StringVar()
        self.anioss = tk.StringVar()
        self.diasg = tk.StringVar()
        self.tipo_contrato = tk.StringVar()
        self.estado_var = tk.StringVar()
        self.cv_src = self.contrato_src = self.solvencia_src = self.id_src = self.foto_src = None

        # ---- Layout ----
        container = ttk.Frame(master, padding=20)
        container.pack(fill="both", expand=True)

        seccion1 = ttk.LabelFrame(container, text="Datos Personales", padding=10)
        seccion1.grid(row=0, column=0, columnspan=3, sticky="ew", pady=10)

        self.add_field(seccion1, "Identidad", self.identidad, 0, 0)
        self.add_field(seccion1, "Primer Nombre", self.nombre1, 0, 1)
        self.add_field(seccion1, "Segundo Nombre", self.nombre2, 0, 2)
        self.add_field(seccion1, "Primer Apellido", self.apellido1, 1, 0)
        self.add_field(seccion1, "Segundo Apellido", self.apellido2, 1, 1)
        self.add_field(seccion1, "Teléfono", self.telefono, 1, 2)
        self.add_field(seccion1, "Profesión", self.profesion, 2, 0)
        self.add_field(seccion1, "Dirección", self.direccion, 2, 1, width=45)

        seccion2 = ttk.LabelFrame(container, text="Información del Contrato", padding=10)
        seccion2.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)

        self.add_field(seccion2, "Dependencia", self.dependencia, 0, 0)
        self.add_field(seccion2, "Cargo", self.cargo, 0, 1)
        ttk.Label(seccion2, text="Tipo de Contrato").grid(row=0, column=2, sticky="w", padx=5, pady=3)
        ttk.Combobox(seccion2, values=CONTRACT_TYPES, textvariable=self.tipo_contrato, state="readonly", width=25).grid(row=1, column=2, padx=5, pady=3)

        ttk.Label(seccion2, text="Estado").grid(row=2, column=2, sticky="w", padx=5, pady=3)
        ttk.Combobox(seccion2, values=ESTADOS, textvariable=self.estado_var, state="readonly", width=25).grid(row=3, column=2, padx=5, pady=3)

        self.add_field(seccion2, "Sueldo (Lps)", self.sueldo, 2, 0)
        self.add_field(seccion2, "Años de Servicio", self.anioss, 2, 1)
        self.add_field(seccion2, "Días a Gozar", self.diasg, 2, 2)

        ttk.Label(seccion2, text="Fecha Inicio").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.fecha_inicio = DateEntry(seccion2, date_pattern="yyyy-mm-dd")
        self.fecha_inicio.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(seccion2, text="Fecha Finalización").grid(row=3, column=1, sticky="e", padx=5, pady=5)
        self.fecha_fin = DateEntry(seccion2, date_pattern="yyyy-mm-dd")
        self.fecha_fin.grid(row=3, column=2, sticky="w", padx=5, pady=5)

        seccion3 = ttk.LabelFrame(container, text="Documentos Adjuntos", padding=10)
        seccion3.grid(row=2, column=0, columnspan=3, sticky="ew", pady=10)

        ttk.Button(seccion3, text="📄 Seleccionar CV", command=self.select_cv).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(seccion3, text="🧾 Contrato", command=self.select_contrato).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(seccion3, text="🪪 Identidad", command=self.select_identidad).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(seccion3, text="📷 Foto", command=self.select_foto).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(seccion3, text="✅ Solvencia", command=self.select_solvencia).grid(row=1, column=1, padx=5, pady=5)

        btns = ttk.Frame(container)
        btns.grid(row=3, column=0, columnspan=3, pady=20)
        ttk.Button(btns, text="💾 Guardar Cambios", command=self.guardar).grid(row=0, column=0, padx=10)
        ttk.Button(btns, text="❌ Cancelar", command=self.master.destroy).grid(row=0, column=1, padx=10)

        self.cargar_datos()

    # ---- Campos ----
    def add_field(self, parent, label, var, row, col, width=25):
        ttk.Label(parent, text=label).grid(row=row*2, column=col, sticky="w", padx=5, pady=2)
        ttk.Entry(parent, textvariable=var, width=width).grid(row=row*2+1, column=col, padx=5, pady=4, sticky="ew")

    # ---- Selección de archivos ----
    def select_cv(self): self.cv_src = filedialog.askopenfilename(title="Seleccionar CV")
    def select_contrato(self): self.contrato_src = filedialog.askopenfilename(title="Seleccionar Contrato")
    def select_solvencia(self): self.solvencia_src = filedialog.askopenfilename(title="Seleccionar Solvencia")
    def select_identidad(self): self.id_src = filedialog.askopenfilename(title="Seleccionar Identidad")
    def select_foto(self): self.foto_src = filedialog.askopenfilename(title="Seleccionar Foto")

    # ---- Cargar datos desde DB ----
    def cargar_datos(self):
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT identidad, nombre1, nombre2, apellido1, apellido2,
                   telefono, profesion, tipo_contrato, direccion, dependencia,
                   cargo, fecha_inicio, fecha_finalizacion, sueldo, anioss, diasg, estado
            FROM empleados WHERE id = %s
        """, (self.empleado_id,))
        emp = cur.fetchone()
        conn.close()
        if emp:
            (identidad, n1, n2, a1, a2, tel, prof, tipo, dir_, dep, cargo,
             fi, ff, sueldo, anioss, diasg, estado) = emp
            self.identidad.set(identidad)
            self.nombre1.set(n1)
            self.nombre2.set(n2)
            self.apellido1.set(a1)
            self.apellido2.set(a2)
            self.telefono.set(tel)
            self.profesion.set(prof)
            self.tipo_contrato.set(tipo)
            self.direccion.set(dir_)
            self.dependencia.set(dep)
            self.cargo.set(cargo)
            self.fecha_inicio.set_date(fi)
            if ff: self.fecha_fin.set_date(ff)
            self.sueldo.set(str(sueldo))
            self.anioss.set(str(anioss))
            self.diasg.set(str(diasg))
            self.estado_var.set(estado)

    # ---- Guardar cambios ----
    def guardar(self):
        fi, ff = self.fecha_inicio.get_date(), self.fecha_fin.get_date()
        cv_path = copy_file_to_uploads(self.cv_src, "CV") if self.cv_src else None
        contrato_path = copy_file_to_uploads(self.contrato_src, "CONTRATO") if self.contrato_src else None
        solvencia_path = copy_file_to_uploads(self.solvencia_src, "SOLVENCIA") if self.solvencia_src else None
        id_path = copy_file_to_uploads(self.id_src, "IDENTIDAD") if self.id_src else None
        foto_path = copy_file_to_uploads(self.foto_src, "FOTO") if self.foto_src else None

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            UPDATE empleados SET
                identidad=%s, nombre1=%s, nombre2=%s, apellido1=%s, apellido2=%s,
                telefono=%s, profesion=%s, tipo_contrato=%s, direccion=%s, dependencia=%s,
                cargo=%s, fecha_inicio=%s, fecha_finalizacion=%s, sueldo=%s,
                estado=%s, cv_path=COALESCE(%s, cv_path),
                contrato_path=COALESCE(%s, contrato_path),
                solvencia_path=COALESCE(%s, solvencia_path),
                id_path=COALESCE(%s, id_path),
                foto_path=COALESCE(%s, foto_path)
            WHERE id=%s
        """, (
            self.identidad.get(), self.nombre1.get(), self.nombre2.get(), self.apellido1.get(), self.apellido2.get(),
            self.telefono.get(), self.profesion.get(), self.tipo_contrato.get(), self.direccion.get(), self.dependencia.get(),
            self.cargo.get(), fi, ff, float(self.sueldo.get() or 0),
            self.estado_var.get(),
            cv_path, contrato_path, solvencia_path, id_path, foto_path,
            self.empleado_id
        ))
        conn.commit()
        conn.close()
        messagebox.showinfo("Éxito", "Empleado actualizado correctamente.")
        self.master.destroy()


# ==== Ejemplo de uso ====
if __name__ == "__main__":
    root = tk.Tk()
    app = EditEmpleadoForm(root, empleado_id=1)  # Cambiar por el ID del empleado a editar
    root.mainloop()