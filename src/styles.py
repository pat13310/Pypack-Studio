"""
Fichier contenant les styles personnalisés pour l'application PyPack Studio.
"""

CUSTOM_STYLE = """
/* Dégradé gris sombre pour la fenêtre principale */
 QMainWindow {
     background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                 stop: 0 #2e2e2e, stop: 1 #1a1a1a);
     color: #ffffff;
 }

 /* Style des boutons */
 QPushButton {
     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #5a5a5a, stop: 1 #3c3c3c);
     border: 1px solid #4a4a4a;
     border-radius: 6px;
     padding: 6px 12px;
     color: #ffffff;
     font-weight: bold;
 }

 QPushButton:hover {
     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #6a6a6a, stop: 1 #4c4c4c);
    border: 1px solid #5a9bff;
 }

 QPushButton:pressed {
     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #3c3c3c, stop: 1 #5a5a5a);
     border: 1px solid #2a2a2a;
 }

 QPushButton:disabled {
     background-color: #3a3a3a;
     color: #6a6a6a;
     border: 1px solid #2a2a2a;
 }

 /* Style pour les boutons plus petits comme ceux de PathPicker */
 QToolButton {
     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #5a5a5a, stop: 1 #3c3c3c);
     border: 1px solid #4a4a4a;
     border-radius: 4px;
     padding: 2px 4px;
     color: #ffffff;
     font-weight: bold;
 }

 QToolButton:hover {
     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #6a6a6a, stop: 1 #4c4c4c);
     border: 1px solid #5a9bff;
     
 }

 QToolButton:pressed {
     background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #3c3c3c, stop: 1 #5a5a5a);
     border: 1px solid #2a2a2a;
 }

 /* Style pour les champs de saisie */
 QLineEdit, QPlainTextEdit, QComboBox {
     background-color: #2d2d2d;
     border: 1px solid #4a4a4a;
     border-radius: 4px;
     padding: 4px;
     color: #ffffff;
     selection-background-color: #5a5a5a;
 }

 QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
     border: 1px solid #5a9bff ;
 }

 /* Style pour les labels */
 QLabel {
     color: #e0e0e0;
     padding-top:6px;
 }

 /* Style pour les listes et tableaux */
 QListWidget, QTableWidget {
     background-color: #252525;
     alternate-background-color: #2a2a2a;
     border: 1px solid #4a4a4a;
     border-radius: 4px;
     color: #ffffff;
     gridline-color: #4a4a4a;
 }

 QListWidget::item:selected, QTableWidget::item:selected {
     background-color: #5a5a5a;
 }

 /* Style pour la barre de navigation */
 QListWidget#nav {
     background-color: #252525;
     border: none;
     border-radius: 8px;
     font-size:14px;
 }

 QListWidget#nav::item {
     padding: 15px 10px;
     color: #f0f0f0;
     background-color: #2a2a2a;
     border-radius: 8px;
     margin: 3px ;
     border: 1px solid #3a3a3a;
     font-size:14px;
 }

 QListWidget#nav::item:hover {
     background-color: #353535;
     border: 1px solid #454545;
 }

 QListWidget#nav::item:selected {
     background-color: #353535;
     color: #ffffff;
     border-left: 5px solid #5a9bff;
     font-weight: bold;
 }

 /* Style pour les en-têtes de tableau */
 QHeaderView::section {
     background-color: #3a3a3a;
     color: #ffffff;
     padding: 4px;
     border: 1px solid #4a4a4a;
 }

 /* Style pour les cases à cocher */
 QCheckBox {
     color: #e0e0e0;
 }

 QCheckBox::indicator {
     width: 16px;
     height: 16px;
 }

 QCheckBox::indicator:unchecked {
     border: 1px solid #4a4a4a;
     background-color: #2d2d2d;
 }

 QCheckBox::indicator:checked {
     border: 1px solid #4a4a4a;
     background-color: #5a9bff;
 }

 QCheckBox::indicator:unchecked:hover {
     border: 1px solid #5a9bff;
 }

 QCheckBox::indicator:checked:hover {
     border: 1px solid #5a9bff;
 }

 /* Style pour la barre de progression */
 QProgressBar {
     border: 1px solid #4a4a4a;
     border-radius: 4px;
     text-align: center;
     background-color: #2d2d2d;
 }

 QProgressBar::chunk {
     background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                       stop: 0 #5a9bff, stop: 0.5 #007acc, stop: 1 #003d7a);
     border-radius: 3px;
 }

"""