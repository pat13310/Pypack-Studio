"""
Application MyApp1
"""

import sys
from PySide6 import QtCore, QtGui, QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyApp1")
        self.resize(800, 600)
        
        # Widget central
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Label de bienvenue
        label = QtWidgets.QLabel("Bienvenue dans MyApp1!")
        label.setAlignment(QtCore.Qt.AlignCenter)
        font = label.font()
        font.setPointSize(18)
        label.setFont(font)
        layout.addWidget(label)
        
        # Bouton de test
        button = QtWidgets.QPushButton("Cliquez-moi")
        button.clicked.connect(self.on_button_clicked)
        layout.addWidget(button)
        
        # Zone de texte
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setPlaceholderText("Entrez votre texte ici...")
        layout.addWidget(self.text_edit)
    
    def on_button_clicked(self):
        self.text_edit.append("Bonjour, monde!")


def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Style
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
