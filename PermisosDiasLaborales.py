import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from tkcalendar import Calendar
import psycopg2
import psycopg2.extras
from datetime import date
import os
import json

# ---------------- CONFIGURACIÓN BASE DE DATOS ----------------
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

# ---------------- VENTANA SOLICITAR AUSENCIA ----------------
class EditarP(tk.Toplevel):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.master = master
        self.user_id = user_id
        self.title("Solicitud de Ausencia")
        self.geometry("1000x750")
        self.resizable(False, False)
        self.configure(bg="#ecf0f1")

        self.transient(master)
        self.grab_set()
        self.focus_set()
        self.lift()

        self.origin = "colaborador"

        # ------ CENTRAR ------
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.winfo_screenheight() // 2) - (750 // 2)
        self.geometry(f"1000x750+{x}+{y}")

        # ------ ESTILOS ------
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#ecf0f1", foreground="#2c3e50", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#2c3e50")
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6, relief="flat")
        style.configure("TEntry", font=("Segoe UI", 10))

        self.cal_inicio = Calendar(self, selectmode="day", date_pattern="yyyy-mm-dd")
        self.cal_inicio.place(x=100, y=150)
        self.cal_fin = Calendar(self, selectmode="day", date_pattern="yyyy-mm-dd")
        self.cal_fin.place(x=350, y=150)

        # ---------- FRAME PRINCIPAL ----------
        self.frame = tk.Frame(self, bg="#ffffff", bd=2, relief="flat")
        self.frame.pack(fill="both", expand=True, padx=16, pady=16)

        header_label = ttk.Label(self.frame, text="Solicitud de Ausencia", style="Header.TLabel")
        header_label.pack(pady=(10, 10))

        # ---------- FRAME GRUPOS ----------
        self.dias_frame = tk.LabelFrame(self.frame, text="Días", bg="#ffffff", font=("Segoe UI",10,"bold"))
        self.dias_frame.pack(fill="x", padx=10, pady=16)  # más alto

        self.personal_frame = tk.LabelFrame(self.frame, text="Información Personal", bg="#ffffff", font=("Segoe UI",10,"bold"))
        self.personal_frame.pack(fill="x", padx=10, pady=6)

        self.fecha_frame = tk.LabelFrame(self.frame, text="Fechas de Ausencia", bg="#ffffff", font=("Segoe UI",10,"bold"))
        self.fecha_frame.pack(fill="x", padx=10, pady=6)

        self.motivo_frame = tk.LabelFrame(self.frame, text="Motivo de Ausencia", bg="#ffffff", font=("Segoe UI",10,"bold"))
        self.motivo_frame.pack(fill="x", padx=10, pady=6)

        self.comprobante_frame = tk.LabelFrame(self.frame, text="Comprobante", bg="#ffffff", font=("Segoe UI",10,"bold"))
        self.comprobante_frame.pack(fill="x", padx=10, pady=6)

        # ---------- CAMPOS ----------
        self.fields = {}
        labels = [("Identidad","identidad"),("Nombre Completo","nombre_completo"),
                  ("Cargo","cargo"),("Dependencia","dependencia")]

        # Diseño 2 columnas por fila
        for i in range(2):
            tk.Label(self.personal_frame, text=labels[i][0]+":", bg="#ffffff", anchor="w").grid(row=0, column=i*2, sticky="w", pady=6, padx=(4,8))
            ent = ttk.Entry(self.personal_frame, state="disabled", width=35)
            ent.grid(row=0, column=i*2+1, sticky="w", padx=(0,6), ipady=5)
            self.fields[labels[i][1]] = ent
        for i in range(2,4):
            tk.Label(self.personal_frame, text=labels[i][0]+":", bg="#ffffff", anchor="w").grid(row=1, column=(i-2)*2, sticky="w", pady=6, padx=(4,8))
            ent = ttk.Entry(self.personal_frame, state="disabled", width=35)
            ent.grid(row=1, column=(i-2)*2+1, sticky="w", padx=(0,6), ipady=5)
            self.fields[labels[i][1]] = ent

        # Fechas en una fila
        tk.Label(self.fecha_frame, text="Fecha de entrega:", bg="#ffffff").grid(row=0, column=0, sticky="w", pady=6, padx=6)
        self.fecha_entrega = DateEntry(self.fecha_frame, width=15, background="darkblue", foreground="white", borderwidth=2)
        self.fecha_entrega.grid(row=0, column=1, sticky="w", padx=6)

        tk.Label(self.fecha_frame, text="Fecha inicio:", bg="#ffffff").grid(row=0, column=2, sticky="w", pady=6, padx=6)
        self.fecha_inicio = DateEntry(self.fecha_frame, width=15, background="darkblue", foreground="white", borderwidth=2)
        self.fecha_inicio.grid(row=0, column=3, sticky="w", padx=6)

        tk.Label(self.fecha_frame, text="Fecha finalización:", bg="#ffffff").grid(row=0, column=4, sticky="w", pady=6, padx=6)
        self.fecha_fin = DateEntry(self.fecha_frame, width=15, background="darkblue", foreground="white", borderwidth=2)
        self.fecha_fin.grid(row=0, column=5, sticky="w", padx=6)

        # ---------- MOTIVO DE AUSENCIA (HORIZONTAL) ----------
        # Tipo de carácter
        tk.Label(self.motivo_frame, text="Tipo de carácter:", bg="#ffffff").grid(row=0, column=0, sticky="w", pady=6)
        self.tipo_cb = ttk.Combobox(self.motivo_frame, values=["Oficial", "Personal", "Negociable"], state="readonly", width=22)
        self.tipo_cb.grid(row=0, column=1, sticky="w", padx=6)
        self.tipo_cb.bind("<<ComboboxSelected>>", self.actualizar_checks)

        # -------- COMBOBOX AL MISMO NIVEL --------
        tk.Label(self.motivo_frame, text="Motivos:", bg="#ffffff").grid(row=1, column=0, sticky="w", pady=5)

        # Oficial
        self.lista_oficial_var = tk.StringVar()
        self.lista_oficial = ttk.Combobox(
            self.motivo_frame,
            textvariable=self.lista_oficial_var,
            values=["Representación / funciones", "Asistencia a cursos", "Otros"],
            state="disabled",
            width=25
        )
        self.lista_oficial.grid(row=1, column=1, sticky="w", padx=4)

        # Personal
        self.lista_personal_var = tk.StringVar()
        self.lista_personal = ttk.Combobox(
            self.motivo_frame,
            textvariable=self.lista_personal_var,
            values=["Visita médica", "Trámites personales", "Otros"],
            state="disabled",
            width=25
        )
        self.lista_personal.grid(row=1, column=2, sticky="w", padx=4)

        # Negociable
        self.lista_negociable_var = tk.StringVar()
        self.lista_negociable = ttk.Combobox(
            self.motivo_frame,
            textvariable=self.lista_negociable_var,
            values=["Salario", "Compensatorio", "Otros"],
            state="disabled",
            width=25
        )
        self.lista_negociable.grid(row=1, column=3, sticky="w", padx=4)

        # ------------ CAMPO OTROS ------------
        tk.Label(self.motivo_frame, text="Detalle (si es Otros):", bg="#ffffff").grid(row=2, column=0, sticky="w", pady=5)
        self.otros_var = tk.StringVar()
        self.otros_entry = ttk.Entry(self.motivo_frame, textvariable=self.otros_var, state="disabled", width=60)
        self.otros_entry.grid(row=2, column=1, columnspan=3, sticky="w", padx=4)

        # ------------ OBSERVACIONES ------------
        tk.Label(self.motivo_frame, text="Observaciones:", bg="#ffffff").grid(row=3, column=0, sticky="nw", pady=5)
        self.obs = tk.Text(self.motivo_frame, width=60, height=6)
        self.obs.grid(row=3, column=1, columnspan=3, sticky="w", padx=4)

        # Binds
        self.lista_oficial.bind("<<ComboboxSelected>>", self.verificar_otros)
        self.lista_personal.bind("<<ComboboxSelected>>", self.verificar_otros)
        self.lista_negociable.bind("<<ComboboxSelected>>", self.verificar_otros)

        self.lista_personal.bind("<<ComboboxSelected>>", self.validar_motivo)

        self.cal_inicio.bind("<<CalendarSelected>>", self.validar_fechas_medicas)
        self.cal_fin.bind("<<CalendarSelected>>", self.validar_fechas_medicas)

        self.fecha_inicio.bind("<<DateEntrySelected>>", self.validar_fechas_medicas)
        self.fecha_fin.bind("<<DateEntrySelected>>", self.validar_fechas_medicas)

        # Días grandes
        self.solicitados_var = tk.StringVar(value="0")
        self.gozados_var = tk.StringVar(value="0")
        self.restantes_var = tk.StringVar(value="0")
        for idx,(label,var,bg) in enumerate([("Días Solicitados",self.solicitados_var,"#1abc9c"),
                                             ("Días Gozados",self.gozados_var,"#3498db"),
                                             ("Días Restantes",self.restantes_var,"#e74c3c")]):
            tk.Label(self.dias_frame, text=label+":", bg=bg, fg="white", width=15).grid(row=0,column=idx*2,padx=4)
            tk.Label(self.dias_frame, textvariable=var, bg=bg, fg="white", width=10, font=("Segoe UI",16,"bold")).grid(row=0,column=idx*2+1,padx=4)

        self.fecha_inicio.bind("<<DateEntrySelected>>", lambda e:self.actualizar_dias())
        self.fecha_fin.bind("<<DateEntrySelected>>", lambda e:self.actualizar_dias())

        # Comprobante
        self.archivo_var = tk.StringVar(value="No adjuntado")
        self.btn_adjuntar = tk.Button(self.comprobante_frame, text="📎 Adjuntar comprobante", bg="#f39c12", fg="white",
                                      font=("Segoe UI",10,"bold"), relief="flat", cursor="hand2", command=self.adjuntar_archivo)
        self.btn_adjuntar.pack(side="left", padx=4, pady=4)
        tk.Label(self.comprobante_frame, textvariable=self.archivo_var, bg="#ffffff").pack(side="left", padx=6)

        # Botones
        self.btn_frame = tk.Frame(self.frame, bg="#ffffff")
        self.btn_frame.pack(fill="x", pady=12, padx=4)
        self.btn_solicitar = tk.Button(self.btn_frame, text="📝 Solicitar", bg="#2ecc71", fg="white", command=self.solicitar)
        self.btn_solicitar.pack(side="left", expand=True, fill="x", padx=6, ipady=6)
        self.btn_editar = tk.Button(self.btn_frame, text="✏️ Editar", bg="#3498db", fg="white", command=self.habilitar_edicion)
        self.btn_editar.pack(side="left", expand=True, fill="x", padx=6, ipady=6)
        self.btn_guardar = tk.Button(self.btn_frame, text="💾 Guardar", bg="#1abc9c", fg="white", command=self.guardar, state="disabled")
        self.btn_guardar.pack(side="left", expand=True, fill="x", padx=6, ipady=6)
        self.btn_limpiar = tk.Button(self.btn_frame, text="🧹 Limpiar", bg="#f39c12", fg="white", command=self.limpiar)
        self.btn_limpiar.pack(side="left", expand=True, fill="x", padx=6, ipady=6)
        self.btn_cancelar = tk.Button(self.btn_frame, text="❌ Cancelar", bg="#e74c3c", fg="white", command=self.destroy)
        self.btn_cancelar.pack(side="left", expand=True, fill="x", padx=6, ipady=6)

        # Cargar usuario
        self.load_user()
        self.actualizar_checks()
        self.actualizar_dias()

    # ---------------- FUNCIONES ----------------
    def actualizar_checks(self, event=None):
        tipo = self.tipo_cb.get()
        # Deshabilitar todas
        self.lista_oficial.config(state="disabled")
        self.lista_personal.config(state="disabled")
        self.lista_negociable.config(state="disabled")
        self.lista_oficial_var.set("")
        self.lista_personal_var.set("")
        self.lista_negociable_var.set("")
        self.otros_var.set("")
        self.otros_entry.config(state="disabled")

        if tipo=="Oficial":
            self.lista_oficial.config(state="readonly")
        elif tipo=="Personal":
            self.lista_personal.config(state="readonly")
        elif tipo=="Negociable":
            self.lista_negociable.config(state="readonly")

    def check_otros(self, event=None):
        tipo = self.tipo_cb.get()
        selected = ""
        if tipo=="Oficial":
            selected = self.lista_oficial_var.get()
        elif tipo=="Personal":
            selected = self.lista_personal_var.get()
        elif tipo=="Negociable":
            selected = self.lista_negociable_var.get()

        if selected=="Otros":
            self.otros_entry.config(state="normal")
        else:
            self.otros_entry.config(state="disabled")
            self.otros_var.set("")

        # Validación rápida de días para visita médica
        if tipo=="Personal" and selected=="Visita médica":
            dias_max = 3
            fecha_inicio = self.fecha_inicio.get_date()
            fecha_fin = self.fecha_fin.get_date()
            if (fecha_fin - fecha_inicio).days + 1 > dias_max:
                messagebox.showinfo("Aviso", f"La ausencia por visita médica es de máximo {dias_max} días.")
                self.fecha_fin.set_date(fecha_inicio + timedelta(days=dias_max-1))
        
        self.lista_oficial.bind("<<ComboboxSelected>>", self.check_otros)
        self.lista_personal.bind("<<ComboboxSelected>>", self.check_otros)
        self.lista_negociable.bind("<<ComboboxSelected>>", self.check_otros)

    def verificar_otros(self, event=None):
        seleccion = [
            self.lista_oficial_var.get(),
            self.lista_personal_var.get(),
            self.lista_negociable_var.get()
        ]

        if "Otros" in seleccion:
            self.otros_entry.config(state="normal")
        else:
            self.otros_entry.delete(0, tk.END)
            self.otros_entry.config(state="disabled")

    def actualizar_dias(self):
        try:
            inicio = self.fecha_inicio.get_date()
            fin = self.fecha_fin.get_date()
            hoy = date.today()
            solicitados = (fin - inicio).days + 1
            gozados = (hoy - inicio).days + 1 if hoy >= inicio else 0
            restantes = solicitados - gozados
            if restantes < 0: restantes=0
            self.solicitados_var.set(str(solicitados))
            self.gozados_var.set(str(gozados))
            self.restantes_var.set(str(restantes))
        except:
            pass

    def adjuntar_archivo(self):
        archivo = filedialog.askopenfilename()
        if archivo:
            self.archivo_var.set(os.path.basename(archivo))
            self.btn_adjuntar.config(bg="#27ae60")
    
    def validar_motivo(self, event=None):
        motivo = self.lista_personal_var.get()

        if motivo == "Visita médica":
            self.mostrar_toast("Para una solicitud médica, el máximo permitido es 3 días.")
    
    def validar_fechas_medicas(self, event=None):
        motivo = self.lista_personal_var.get()

        # Solo validar para VISITA MÉDICA
        if motivo != "Visita médica":
            return

        try:
            fecha_inicio = self.fecha_inicio.get_date()
            fecha_fin = self.fecha_fin.get_date()
        except:
            return

        dias = (fecha_fin - fecha_inicio).days + 1

        if dias > 3:
            self.mostrar_toast("La ausencia por visita médica no puede superar los 3 días.")

            # Corregir FECHA FIN automáticamente
            nueva_fin = fecha_inicio + timedelta(days=2)
            self.fecha_fin.set_date(nueva_fin)

        if dias > 3:
            self.mostrar_toast("La ausencia por visita médica no puede superar los 3 días.")
            nueva_fin = fecha_inicio + timedelta(days=2)
            self.fecha_fin_var.set(nueva_fin.strftime("%Y-%m-%d"))

    def mostrar_toast(self, mensaje):
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.geometry("+{}+{}".format(self.winfo_rootx()+200, self.winfo_rooty()+100))
        tk.Label(toast, text=mensaje, bg="#333", fg="white", padx=10, pady=5).pack()
        toast.after(2500, toast.destroy)

    def habilitar_edicion(self):
        for ent in self.fields.values():
            ent.config(state="normal")
        self.btn_guardar.config(state="normal")

    def limpiar(self):
        for ent in self.fields.values():
            if ent.cget("state")=="normal":
                ent.delete(0, tk.END)
        if self.obs.cget("state")=="normal":
            self.obs.delete("1.0","end")
        self.tipo_cb.set("")
        self.otros_var.set("")
        self.archivo_var.set("No adjuntado")
        self.btn_adjuntar.config(bg="#f39c12")
        self.actualizar_dias()

    def guardar(self):
        messagebox.showinfo("Guardar","Cambios guardados correctamente.")
        self.btn_guardar.config(state="disabled")

    def solicitar(self):
        # Validación de campos obligatorios
        if not self.fields["identidad"].get().strip() or not self.fields["nombre_completo"].get().strip():
            messagebox.showwarning("Campos incompletos", "Debe llenar la identidad y el nombre completo.")
            return

        if not self.tipo_cb.get():
            messagebox.showwarning("Campos incompletos", "Debe seleccionar un tipo de carácter.")
            return

        if not self.fecha_entrega.get() or not self.fecha_inicio.get() or not self.fecha_fin.get():
            messagebox.showwarning("Campos incompletos", "Debe seleccionar todas las fechas.")
            return

        tipo = self.tipo_cb.get()
        if tipo in self.check_vars:
            checks_seleccionados = [v.get() for v in self.check_vars[tipo]]
            if tipo != "Negociable" and sum(checks_seleccionados) == 0:
                messagebox.showwarning("Campos incompletos", "Debe seleccionar al menos un motivo.")
                return
            if self.check_vars[tipo][-1].get() == 1 and not self.otros_var.get().strip():
                messagebox.showwarning("Campos incompletos", "Debe indicar el detalle en 'Otros'.")
                return

    # Si pasa todas las validaciones, continúa con el envío
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            row_identidad = self.fields["identidad"].get()
            row_nombre_completo = self.fields["nombre_completo"].get()
            tipo = self.tipo_cb.get()
            otros = self.otros_var.get()
            observ = self.obs.get("1.0","end").strip()
            archivo = self.archivo_var.get()
            fecha_entrega = self.fecha_entrega.get_date()
            fecha_inicio = self.fecha_inicio.get_date()
            fecha_fin = self.fecha_fin.get_date()
            dias = (fecha_fin-fecha_inicio).days+1
            checks_list = []
            if tipo=="Oficial" and self.lista_oficial_var.get():
                checks_list.append(self.lista_oficial_var.get())
            elif tipo=="Personal" and self.lista_personal_var.get():
                checks_list.append(self.lista_personal_var.get())
            elif tipo=="Negociable" and self.lista_negociable_var.get():
                checks_list.append(self.lista_negociable_var.get())

            # Validar que al menos un check esté seleccionado (excepto Negociable si quieres)
            if tipo != "Negociable" and not checks_list:
               messagebox.showwarning("Campos incompletos", "Debe seleccionar al menos un motivo.")
               return

            checks_str = json.dumps(checks_list)  # Convierte a JSON válido para PostgreSQL

            cur.execute("""
                INSERT INTO permisos_dias_laborales
                (colaborador_id, identidad, nombre_completo, tipo_permiso, fecha_entrega, fecha_inicio, fecha_fin,
                dias_solicitados, caracter, motivo_detalle, checks, observaciones, constancia_path, estado, creado_por, creado_en,
                dias_restantes_total, dias_restantes_actual)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pendiente',%s,NOW(),%s,%s)
            """, (
                self.colaborador_id, row_identidad, row_nombre_completo, tipo, fecha_entrega, fecha_inicio, fecha_fin,
                dias, tipo, otros, checks_str, observ, archivo, self.user_id, dias, dias
            ))
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo("Solicitud","Solicitud enviada correctamente al administrador.")
        except Exception as e:
            messagebox.showerror("Error BD",f"No se puede enviar:\n{e}")

    # ---------------- CARGAR DESDE BD ----------------
    def load_user(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            if str(self.user_id).isdigit():
                cur.execute("SELECT * FROM colaborador WHERE id=%s",(int(self.user_id),))
            else:
                cur.execute("SELECT * FROM colaborador WHERE usuario=%s",(self.user_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()

            self.colaborador_id = row.get("id")

            if not row:
                messagebox.showerror("Error","Usuario no encontrado")
                self.destroy()
                return
            nombre_completo = f"{row.get('nombre1','')} {row.get('nombre2','')} {row.get('apellido1','')} {row.get('apellido2','')}".strip()
            valores = {
                "identidad": row.get("identidad",""),
                "nombre_completo": nombre_completo,
                "cargo": row.get("cargo",""),
                "dependencia": row.get("dependencia","")
            }
            for key, ent in self.fields.items():
                ent.config(state="normal")
                ent.delete(0, tk.END)
                ent.insert(0, valores.get(key,""))
                ent.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Error BD",f"No se pudo cargar:\n{e}")

# ---------------- EJEMPLO DE PRUEBA ----------------
if __name__=="__main__":
    root = tk.Tk()
    root.withdraw()
    EditarP(root,"noel")
    root.mainloop()