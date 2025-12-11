import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import psycopg2
import psycopg2.extras
from datetime import date, datetime, timedelta

DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import psycopg2, psycopg2.extras
from datetime import date, datetime, timedelta
from editar_perfil import DB_CONFIG

class SolicitudVacaciones(tk.Toplevel):

    def __init__(self, master, user_id):
        super().__init__(master)
        self.master = master
        self.user_id = user_id
        self.usuario_actual = user_id
        self.title("Solicitud de Vacaciones")
        self.geometry("900x650")
        self.resizable(False, False)
        self.configure(bg="#ecf0f1")
        self.transient(master)
        self.grab_set()
        self.focus_set()
        self.lift()

        # ------ Centrar ventana ------
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.winfo_screenheight() // 2) - (650 // 2)
        self.geometry(f"900x650+{x}+{y}")

        # ------ Estilos ------
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#ecf0f1", foreground="#2c3e50", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#2c3e50")
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6, relief="flat")
        style.configure("TEntry", font=("Segoe UI", 10))

        # ------ Frame Principal ------
        self.frame = tk.Frame(self, bg="#ffffff", bd=2, relief="flat")
        self.frame.pack(fill="both", expand=True, padx=16, pady=16)

        ttk.Label(self.frame, text="Solicitud de Vacaciones", style="Header.TLabel").pack(pady=(10, 10))

        # ======================================================
        # ========== PRIMERO: DÍAS DISPONIBLES ARRIBA ==========
        # ======================================================
        self.dias_frame = tk.LabelFrame(self.frame, text="Días", bg="#ffffff")
        self.dias_frame.pack(fill="x", padx=10, pady=6)

        self.dias_a_gozar_var = tk.StringVar(value="0")
        self.dias_solicitados_var = tk.StringVar(value="0")
        self.dias_restantes_var = tk.StringVar(value="0")

        for idx, (label, var, bg) in enumerate([
            ("Días a Gozar", self.dias_a_gozar_var, "#1abc9c"),
            ("Días Solicitados", self.dias_solicitados_var, "#3498db"),
            ("Días Restantes", self.dias_restantes_var, "#e74c3c")
        ]):
            tk.Label(self.dias_frame, text=label + ":", bg=bg, fg="white", width=15).grid(row=0, column=idx * 2, padx=4, pady=6)
            tk.Label(self.dias_frame, textvariable=var, bg=bg, fg="white",
                     width=8, font=("Segoe UI", 16, "bold")).grid(row=0, column=idx * 2 + 1, padx=4, pady=6)

        # ======================================================
        # ============ INFORMACIÓN PERSONAL =====================
        # ======================================================
        self.personal_frame = tk.LabelFrame(self.frame, text="Información Personal", bg="#ffffff")
        self.personal_frame.pack(fill="x", padx=10, pady=6)

        self.fields = {}
        labels = [("Identidad", "identidad"), ("Nombre Completo", "nombre_completo"),
                  ("Cargo", "cargo"), ("Dependencia", "dependencia")]

        for i in range(2):
            tk.Label(self.personal_frame, text=labels[i][0] + ":", bg="#ffffff").grid(row=0, column=i * 2, sticky="w", pady=6, padx=4)
            ent = ttk.Entry(self.personal_frame, state="disabled", width=35)
            ent.grid(row=0, column=i * 2 + 1, sticky="w", padx=4, ipady=5)
            self.fields[labels[i][1]] = ent

        for i in range(2, 4):
            tk.Label(self.personal_frame, text=labels[i][0] + ":", bg="#ffffff").grid(row=1, column=(i - 2) * 2, sticky="w", pady=6, padx=4)
            ent = ttk.Entry(self.personal_frame, state="disabled", width=35)
            ent.grid(row=1, column=(i - 2) * 2 + 1, sticky="w", padx=4, ipady=5)
            self.fields[labels[i][1]] = ent

        # ======================================================
        # ================= FECHAS ==============================
        # ======================================================
        self.fecha_frame = tk.LabelFrame(self.frame, text="Fechas de Vacaciones", bg="#ffffff")
        self.fecha_frame.pack(fill="x", padx=10, pady=6)

        tk.Label(self.fecha_frame, text="Fecha inicio:", bg="#ffffff").grid(row=0, column=0, padx=6, pady=6)
        self.fecha_inicio = DateEntry(self.fecha_frame, width=15)
        self.fecha_inicio.grid(row=0, column=1, padx=6)

        tk.Label(self.fecha_frame, text="Fecha fin:", bg="#ffffff").grid(row=0, column=2, padx=6, pady=6)
        self.fecha_fin = DateEntry(self.fecha_frame, width=15)
        self.fecha_fin.grid(row=0, column=3, padx=6)

        self.fecha_inicio.bind("<<DateEntrySelected>>", lambda e: self.actualizar_dias())
        self.fecha_fin.bind("<<DateEntrySelected>>", lambda e: self.actualizar_dias())

        # ======================================================
        # ================= BITÁCORA ============================
        # ======================================================
        tabla_frame = tk.LabelFrame(self.frame, text="Bitácora de Solicitudes", bg="#ffffff")
        tabla_frame.pack(fill="both", expand=True, padx=10, pady=6)

        self.tree = ttk.Treeview(tabla_frame, columns=("Inicio", "Fin", "Días", "Estado"), show="headings", height=5)
        self.tree.heading("Inicio", text="Inicio")
        self.tree.heading("Fin", text="Fin")
        self.tree.heading("Días", text="Días")
        self.tree.heading("Estado", text="Estado")

        self.tree.column("Inicio", width=100)
        self.tree.column("Fin", width=100)
        self.tree.column("Días", width=50, anchor="center")
        self.tree.column("Estado", width=100, anchor="center")

        vsb = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # ======================================================
        # ================= BOTONES =============================
        # ======================================================
        btn_frame = tk.Frame(self.frame, bg="#ffffff")
        btn_frame.pack(fill="x", pady=10)

        self.btn_solicitar = tk.Button(btn_frame, text="📝 Solicitar", bg="#2ecc71", fg="white", command=self.solicitar)
        self.btn_solicitar.pack(side="left", expand=True, fill="x", padx=6, ipady=6)

        self.btn_limpiar = tk.Button(btn_frame, text="🧹 Limpiar", bg="#f39c12", fg="white", command=self.limpiar)
        self.btn_limpiar.pack(side="left", expand=True, fill="x", padx=6, ipady=6)

        self.btn_cancelar = tk.Button(btn_frame, text="❌ Cancelar", bg="#e74c3c", fg="white", command=self.destroy)
        self.btn_cancelar.pack(side="left", expand=True, fill="x", padx=6, ipady=6)

        # =======================
        # CARGA INICIAL
        # =======================
        self.dias_a_gozar = 0  # evitar crash antes de load_user
        self.load_user()
        self.actualizar_dias()
        self.cargar_bitacora()

    # ======================================================
    # ============ FUNCIONES PRINCIPALES ===================
    # ======================================================
    def calcular_dias_a_gozar(self, fecha_ingreso):
        hoy = date.today()
        anios = hoy.year - fecha_ingreso.year - (
            (hoy.month, hoy.day) < (fecha_ingreso.month, fecha_ingreso.day)
        )

        # Año 0 → NO GOZA
        if anios < 1:
            return 0
        # Año 1 → GOZA 10
        elif anios == 1:
            return 10
        # Año 2 → GOZA 12
        elif anios == 2:
            return 12
        # Año 3 → GOZA 15
        elif anios == 3:
            return 15
        # Año 4 en adelante → 20
        else:
            return 20

    def actualizar_dias(self):
        try:
            inicio = self.fecha_inicio.get_date()
            fin = self.fecha_fin.get_date()

            # No permitir elegir fecha inicio o fin en sábado o domingo
            if inicio.weekday() >= 5 or fin.weekday() >= 5:
                self.dias_solicitados_var.set("0")
                self.dias_restantes_var.set(str(self.dias_a_gozar))
                return

            if fin < inicio:
                self.dias_solicitados_var.set("0")
                self.dias_restantes_var.set(str(self.dias_a_gozar))
                return

            # calcular días hábiles
            delta = fin - inicio
            dias_solicitados = sum(
                1 for i in range(delta.days + 1)
                if (inicio + timedelta(days=i)).weekday() < 5
            )

            # validar límites según antigüedad
            if dias_solicitados > self.dias_a_gozar:
                dias_solicitados = self.dias_a_gozar

            self.dias_solicitados_var.set(str(dias_solicitados))
            self.dias_restantes_var.set(str(self.dias_a_gozar - dias_solicitados))

            self.btn_solicitar.config(
                state="normal" if self.dias_a_gozar > 0 else "disabled"
            )
        except:
            pass

    def load_user(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            if str(self.user_id).isdigit():
                cur.execute("SELECT * FROM colaborador WHERE id=%s", (int(self.user_id),))
            else:
                cur.execute("SELECT * FROM colaborador WHERE usuario=%s", (self.user_id,))
                print("DEBUG: Buscando usuario:", self.user_id)

            row = cur.fetchone()
            conn.close()

            # Convertir correctamente a nombre de usuario (string)
            self.usuario_actual = row.get("usuario")  

            if not row:
                messagebox.showerror("Error", "Usuario no encontrado")
                self.destroy()
                return

            self.colaborador_id = row.get("id")
            self.fecha_ingreso = row.get("fecha_inicio")

            # calcular antigüedad
            self.dias_a_gozar = self.calcular_dias_a_gozar(self.fecha_ingreso)
            self.dias_a_gozar_var.set(str(self.dias_a_gozar))

            # Restar días ya gozados (solo solicitudes aceptadas)
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                SELECT COALESCE(SUM(dias_solicitados), 0)
                FROM vacaciones 
                WHERE usuario=%s AND estado='aceptada'
            """, (self.usuario_actual,))
            ya_gozados = cur.fetchone()[0]
            conn.close()

            self.dias_a_gozar -= ya_gozados

            if self.dias_a_gozar < 0:
                self.dias_a_gozar = 0

            self.dias_restantes_var.set(str(self.dias_a_gozar))

            # llenar campos
            nombre_completo = f"{row.get('nombre1','')} {row.get('nombre2','')} {row.get('apellido1','')} {row.get('apellido2','')}".strip()

            datos = {
                "identidad": row.get("identidad", ""),
                "nombre_completo": nombre_completo,
                "cargo": row.get("cargo", ""),
                "dependencia": row.get("dependencia", "")
            }

            for key, ent in self.fields.items():
                ent.config(state="normal")
                ent.delete(0, tk.END)
                ent.insert(0, datos.get(key, ""))
                ent.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo cargar:\n{e}")

    def solicitar(self):
        try:
            inicio = self.fecha_inicio.get_date()
            fin = self.fecha_fin.get_date()

            # No permitir si tiene solicitud pendiente
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM vacaciones WHERE usuario=%s AND estado='pendiente'", (self.usuario_actual,))
            pendientes = cur.fetchone()[0]
            conn.close()

            if pendientes > 0:
                messagebox.showwarning(
                    "Solicitud pendiente",
                    "Tiene una solicitud pendiente de aprobación. No puede generar otra."
                )
                return

            delta = fin - inicio
            dias_solicitados = sum(
                1 for i in range(delta.days + 1)
                if (inicio + timedelta(days=i)).weekday() < 5
            )

            dias_restantes = self.dias_a_gozar - dias_solicitados
            # Validar si ya no tiene días disponibles
            if self.dias_a_gozar <= 0:
                messagebox.showwarning(
                    "Sin días disponibles",
                    "No tiene días de vacaciones disponibles según su antigüedad."
                )
                return

            if dias_solicitados <= 0:
                messagebox.showwarning("Atención", "Seleccione un rango de fechas válido.")
                return

            if dias_solicitados > self.dias_a_gozar:
                messagebox.showwarning(
                    "Excede Límite",
                    f"Su antigüedad solo permite {self.dias_a_gozar} días."
                )
                return

            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO vacaciones
                    (colaborador_id, identidad, nombre_completo, fecha_inicio, fecha_fin,
                    dias_a_gozar, dias_solicitados, dias_gozados, dias_restantes, estado, usuario)
                VALUES (%s,%s,%s,%s,%s,%s,%s,0,%s,'pendiente', %s)
            """, (
                self.colaborador_id,
                self.fields["identidad"].get(),
                self.fields["nombre_completo"].get(),
                inicio, fin,
                self.dias_a_gozar,
                dias_solicitados,
                dias_restantes,
                self.usuario_actual          # ← SOLO ESTE
            ))

            conn.commit()
            conn.close()

            messagebox.showinfo("Solicitud", "Solicitud enviada correctamente.")

            self.cargar_bitacora()
            self.actualizar_dias()

        except Exception as e:
            messagebox.showerror("Error BD", f"No se puede enviar:\n{e}")

    def cargar_bitacora(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("""
                SELECT fecha_inicio, fecha_fin, dias_solicitados, estado 
                FROM vacaciones 
                WHERE  usuario=%s
            ORDER BY id DESC
         """, (self.usuario_actual,))  # 👈 BIEN

            for row in cur.fetchall():
                iid = self.tree.insert("", "end", values=row)

                estado = row[3]
                if estado == "aceptada":
                    self.tree.item(iid, tags=("aceptada",))
                elif estado == "rechazada":
                    self.tree.item(iid, tags=("rechazada",))
                else:
                    self.tree.item(iid, tags=("pendiente",))

            self.tree.tag_configure("aceptada", background="#d4edda")
            self.tree.tag_configure("rechazada", background="#f8d7da")
            self.tree.tag_configure("pendiente", background="#e2e3e5")

            conn.close()

        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo cargar la bitácora:\n{e}")

    def limpiar(self):
        hoy = date.today()
        self.fecha_inicio.set_date(hoy)
        self.fecha_fin.set_date(hoy)
        self.actualizar_dias()

# ---------------- Ejemplo ----------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    SolicitudVacaciones(root, "fernando")
    root.mainloop()