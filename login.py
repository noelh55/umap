import sys
import os
import psycopg2
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPixmap, QPalette, QBrush, QPainter, QPainterPath
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QCheckBox, QMainWindow, QFrame, QGraphicsDropShadowEffect
)
import tkinter as tk
from Main import PantallaPrincipal  # Importa tu ventana principal

# ---------------- CONFIGURACIÓN BASE DE DATOS ----------------
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "database_umap",
    "user": "postgres",
    "password": "umap"
}

REMEMBER_FILE = "remember_user.txt"


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Municipal - Login")

        # Pantalla completa sin bordes
        self.showFullScreen()
        self.setWindowFlag(Qt.FramelessWindowHint)

        # Fondo
        fondo = QPixmap("fondo.jpg")
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(fondo.scaled(
            self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)))
        self.setPalette(palette)

        # ---------------- Contenedor central ----------------
        container = QWidget()
        self.setCentralWidget(container)

        self.form_frame = QFrame()
        self.form_frame.setFixedSize(430, 470)
        self.form_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(50, 50, 50, 130);
                border-radius: 22px;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                background-color: rgba(255, 255, 255, 0);
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 210);
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                color: #000000;
            }
            QPushButton {
                background-color: rgba(51, 102, 153, 160);
                color: white;
                border-radius: 20px;
                font-weight: bold;
                font-size: 14px;
                height: 48px;
                width: 160px;
            }
            QPushButton:hover {
                background-color: rgba(77, 136, 204, 200);
            }
            QCheckBox {
                color: white;
                font-size: 13px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 0)
        self.form_frame.setGraphicsEffect(shadow)

        # ----------- Título -----------
        title = QLabel("Sistema Municipal")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Century Gothic", 22, QFont.Bold))
        title.setStyleSheet("color: white;")

        # ----------- Imagen circular del usuario -----------
        self.user_image = QLabel()
        self.user_image.setFixedSize(80, 80)
        self.user_image.setAlignment(Qt.AlignCenter)
        self.user_image.setStyleSheet("border-radius: 40px; background-color: rgba(255,255,255,45);")

        # ----------- Campos de texto -----------
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Ingrese usuario")
        self.user_input.textChanged.connect(self.reconocer_usuario)  # <<< Detecta al escribir

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Ingrese contraseña")
        self.pass_input.setEchoMode(QLineEdit.Password)

        # ----------- Recordarme -----------
        self.remember_check = QCheckBox("Recordarme")

        # Cargar usuario guardado
        if os.path.exists(REMEMBER_FILE):
            try:
                with open(REMEMBER_FILE, "r") as f:
                    data = f.read().split("|")
                    if len(data) == 2:
                        remembered_user, remembered_pass = data
                        self.user_input.setPlaceholderText(remembered_user)
                        self.pass_input.setPlaceholderText("••••••••")
                        self.load_user_photo(remembered_user)
            except:
                pass

        # ----------- Mensaje de error -----------
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("color: red; font-size: 12px;")

        # ----------- Botón Login -----------
        self.login_btn = QPushButton("Iniciar Sesión")
        self.login_btn.clicked.connect(self.iniciar_sesion)

        # ----------- Salir -----------
        self.exit_label = QLabel("<a href='#' style='color:white;text-decoration:none;'>Salir</a>")
        self.exit_label.setAlignment(Qt.AlignCenter)
        self.exit_label.linkActivated.connect(self.close)

        # ----------- Layout interno -----------
        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addSpacing(15)
        layout.addWidget(self.user_image, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.user_input)
        layout.addSpacing(12)
        layout.addWidget(self.pass_input)
        layout.addSpacing(15)
        layout.addWidget(self.remember_check)
        layout.addSpacing(5)
        layout.addWidget(self.error_label)
        layout.addSpacing(10)
        layout.addWidget(self.login_btn, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.exit_label)
        layout.setContentsMargins(40, 25, 40, 25)
        layout.setAlignment(Qt.AlignCenter)
        self.form_frame.setLayout(layout)

        # ----------- Layout principal -----------
        main_layout = QVBoxLayout(container)
        main_layout.addStretch()
        main_layout.addWidget(self.form_frame, alignment=Qt.AlignCenter)
        main_layout.addStretch()

    # ---------------------------------------------------------------------
    # Cargar imagen circular del usuario
    def load_user_photo(self, username):
        foto_path = os.path.join("fotos", f"{username}.jpg")
        if os.path.exists(foto_path):
            pixmap = QPixmap(foto_path).scaled(80, 80, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            mask = QPixmap(80, 80)
            mask.fill(Qt.transparent)
            painter = QPainter(mask)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, 80, 80)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            self.user_image.setPixmap(mask)
        else:
            self.user_image.setPixmap(QPixmap())

    # ---------------------------------------------------------------------
    # Detectar cuando se escribe usuario y cargar su foto
    def reconocer_usuario(self):
        usuario = self.user_input.text().strip()
        if usuario:
            self.load_user_photo(usuario)
        else:
            self.user_image.setPixmap(QPixmap())

    # ---------------------------------------------------------------------
    # Redibujar fondo al cambiar tamaño
    def resizeEvent(self, event):
        fondo = QPixmap("fondo.jpg")
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(fondo.scaled(
            self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)))
        self.setPalette(palette)

    # ---------------------------------------------------------------------
    # Lógica de inicio de sesión
    def iniciar_sesion(self):
        usuario = self.user_input.text().strip()
        contrasena = self.pass_input.text().strip()
        self.error_label.setText("")

        if not usuario or not contrasena:
            self.mostrar_error_temporal("Debe ingresar usuario y contraseña.")
            return
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("SELECT nombre, rol FROM usuarios WHERE usuario=%s AND contrasena=%s",
                    (usuario, contrasena))
            resultado = cur.fetchone()
            conn.close()
            
            if resultado:
                # Guardar usuario recordado
                if self.remember_check.isChecked():
                    with open(REMEMBER_FILE, "w") as f:
                        f.write(f"{usuario}|{contrasena}")
                else:
                    if os.path.exists(REMEMBER_FILE):
                        os.remove(REMEMBER_FILE)

                self.load_user_photo(usuario)

                # SOLUCIÓN: Primero crear y mostrar la nueva ventana, luego cerrar login
                QTimer.singleShot(100, self.abrir_ventana_principal)
            else:
                self.mostrar_error_temporal("Usuario o contraseña incorrectos.")
        except Exception as e:
            print(f"Error: {e}")  # Para debugging
            self.mostrar_error_temporal("Error al conectar con la base de datos.")

    # ---------------------------------------------------------------------
    # Nuevo método para abrir la ventana principal
    def abrir_ventana_principal(self):
        usuario = self.user_input.text().strip()
    
        # Cerrar primero la ventana de login
        self.close()
    
        # Ahora abrir la ventana principal
        try:
            # OPCIÓN 1: Si usas PyQt5 para la ventana principal
            from Main import PantallaPrincipal  # Asegúrate que este import sea correcto
            # Cerrar ventana de login
            self.close()

            # Crear ventana Tkinter principal
            import tkinter as tk
            root_principal = tk.Tk()
            app = PantallaPrincipal(root_principal, usuario_actual=usuario)
            root_principal.mainloop()
            
        except ImportError as e:
            print(f"Error importando: {e}")
            # OPCIÓN 2: Si necesitas usar tkinter (no recomendado)
            import tkinter as tk
            from Main import PantallaPrincipal
        
            root_principal = tk.Tk()
            app = PantallaPrincipal(root_principal, usuario_actual=usuario)
            root_principal.mainloop()

    # ---------------------------------------------------------------------
    # Mostrar mensaje de error temporal
    def mostrar_error_temporal(self, mensaje):
        self.error_label.setText(mensaje)
        QTimer.singleShot(8000, lambda: self.error_label.setText(""))


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())