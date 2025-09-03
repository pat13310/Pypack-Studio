# Ajoute une icône et un style bleu pour le profil actif dans la liste des profils
from PySide6 import QtGui, QtWidgets

def update_profiles_list_widget(lst_widget, profiles, active_profile=None):
    lst_widget.clear()
        # Applique un style hover cohérent avec le thème sombre de l'interface
    lst_widget.setStyleSheet("""
            QListWidget::item {
                background: #252525;
                color: #e0e0e0;
                border-radius: 8px;
                margin: 3px;
                padding: 3px;
                font-size: 14px;
            }
            QListWidget::item:hover {
                background: #e6f3ff;
                color: #2da8ff;
                border-left: 5px solid #5a9bff;
            }
            QListWidget::item:selected {
                background: #2da8ff;
                color: #ffffff;
                border-left: 5px solid #5a9bff;
            }
        """)
    for name in sorted(profiles):
        item = QtWidgets.QListWidgetItem(name)
        # Ajoute une icône devant chaque profil (utilise profile.png si existe)
        icon_path = "res/person.png"
        if QtGui.QIcon(icon_path).isNull():
            icon = lst_widget.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
        else:
            icon = QtGui.QIcon(icon_path)
        item.setIcon(icon)
        # Police plus grande pour tous les profils
        font = QtGui.QFont("Segoe UI")
        font.setPointSize(12)
        # Style bleu et gras pour le profil actif
        if active_profile and name == active_profile:
            item.setForeground(QtGui.QColor("#007acc"))
        item.setFont(font)
        lst_widget.addItem(item)
