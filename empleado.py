# --- Integración del botón en tu App existente ---
import subprocess
import sys
import tkinter as tk
from tkinter import ttk

class App:
    def __init__(self, root, usuario_actual):
        self.root = root
        root.title("UMAP - Menú Principal")
        root.geometry("1000x700")
        root.configure(bg="#f4f6f9")
        self.usuario_actual = usuario_actual

        # Botón Ver Empleado
        ver_btn = tk.Button(root, text="Ver Empleado", font=("Segoe UI", 14, "bold"),
                            bg="#004080", fg="white", width=20, height=2,
                            command=self.abrir_ver_empleado)
        ver_btn.pack(pady=50)

    def abrir_ver_empleado(self):
        """
        Ejecuta verempleado.py como un nuevo proceso.
        """
        try:
            # Asegúrate de que verempleado.py esté en el mismo directorio o ajusta la ruta
            subprocess.Popen([sys.executable, "verempleado.py"])
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"No se pudo abrir la ventana de empleados:\n{e}")


# --- MAIN ---
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root, usuario_actual="admin")
    root.mainloop()