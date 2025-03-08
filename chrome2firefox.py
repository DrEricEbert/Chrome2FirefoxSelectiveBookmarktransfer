import json
import sys
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QLabel,
    QHBoxLayout,
)

# Hilfsfunktion zum Erzeugen eines QTreeWidgetItem mit Checkbox
def create_tree_item(node):
    """
    Erzeugt einen QTreeWidgetItem aus einem node-Dict, das ein Chrome-Lesezeichen
    oder einen Ordner repräsentiert.
    
    Erwartetes Format:
      - Ordner: node["type"] == "folder", hat "name" und "children" (Liste)
      - Lesezeichen: node["type"] == "url", hat "name" und "url"
    """
    item = QTreeWidgetItem()
    item.setText(0, node.get("name", ""))
    item.setData(0, Qt.ItemDataRole.UserRole, node)
    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
    item.setCheckState(0, Qt.CheckState.Unchecked)
    
    if node.get("type") == "folder" and "children" in node:
        for child in node["children"]:
            child_item = create_tree_item(child)
            item.addChild(child_item)
    return item

# Funktion zum parsen der Chrome-Bookmarks JSON-Struktur
def load_chrome_bookmarks(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "roots" not in data:
            raise ValueError("Ungültiges Format - 'roots' nicht gefunden.")
        # Die Einträge unter 'roots' (z. B. bookmark_bar, other, synced)
        roots = data["roots"]
        nodes = []
        for key in roots:
            # Manche Einträge (z. B. "checkout" o.ä.) ignorieren wir
            if key not in ["bookmark_bar", "other", "synced"]:
                continue
            node = roots[key]
            # Manchmal sind leere Ordner enthalten
            if node:
                nodes.append(node)
        return nodes
    except Exception as e:
        QMessageBox.critical(None, "Fehler beim Lesen der Datei", str(e))
        return None

# Rekursive Funktion, um aus den ausgewählten TreeItems eine Datenstruktur zu erzeugen
def process_tree_item(item: QTreeWidgetItem):
    """
    Gibt entweder None zurück, wenn weder das Element noch eines seiner Kind-Elemente ausgewählt wurde,
    oder ein Dict im Format { type: 'folder' or 'url', name: ..., [url: ...], [children: [...]] }
    """
    node = item.data(0, Qt.ItemDataRole.UserRole)
    node_type = node.get("type")
    children = []
    for i in range(item.childCount()):
        child_result = process_tree_item(item.child(i))
        if child_result is not None:
            children.append(child_result)
    # Wenn das Item selbst ausgewählt ist, oder wenn eines der untergeordneten Elemente ausgewählt wurde,
    # nehmen wir das Element in den Export auf.
    if item.checkState(0) == Qt.CheckState.Checked or children:
        if node_type == "folder":
            return {
                "type": "folder",
                "name": node.get("name", ""),
                "children": children
            }
        elif node_type == "url":
            # Bei Lesezeichen: nur exportieren, wenn explizit ausgewählt
            if item.checkState(0) == Qt.CheckState.Checked:
                return {
                    "type": "url",
                    "name": node.get("name", ""),
                    "url": node.get("url", "")
                }
    return None

# Rekursive Funktion, um aus einer Datenstruktur im oben genannten Format HTML (Netscape-Format) zu generieren.
def generate_html(bookmark_structure, indent=1):
    html_lines = []
    spacer = "    " * indent
    if bookmark_structure.get("type") == "folder":
        # Erzeuge einen Ordner
        folder_name = bookmark_structure.get("name", "Unbenannt")
        html_lines.append(f'{spacer}<DT><H3>{folder_name}</H3>')
        html_lines.append(f'{spacer}<DL><p>')
        for child in bookmark_structure.get("children", []):
            html_lines.extend(generate_html(child, indent + 1))
        html_lines.append(f'{spacer}</DL><p>')
    elif bookmark_structure.get("type") == "url":
        title = bookmark_structure.get("name", "")
        url = bookmark_structure.get("url", "")
        # Füge ein Add-Date hinzu (als Integer; hier einfach das aktuelle Datum)
        add_date = int(datetime.now().timestamp())
        html_lines.append(f'{spacer}<DT><A HREF="{url}" ADD_DATE="{add_date}">{title}</A>')
    return html_lines

# Erzeugt den kompletten HTML-Export als String
def export_to_html(structures):
    html = []
    html.append('<!DOCTYPE NETSCAPE-Bookmark-file-1>')
    html.append('<!-- This is an automatically generated file.')
    html.append('     It will be read and overwritten.')
    html.append('     Do Not Edit! -->')
    html.append('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">')
    html.append('<TITLE>Bookmarks</TITLE>')
    html.append('<H1>Bookmarks</H1>')
    html.append('<DL><p>')
    for structure in structures:
        html.extend(generate_html(structure))
    html.append('</DL><p>')
    return "\n".join(html)

# Hauptfenster der Anwendung
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chrome → Firefox Bookmark Exporter")
        self.resize(800, 600)
        
        # Zentrales Widget und Layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Informationen
        self.info_label = QLabel("Lade eine Chrome-Bookmark-Datei (JSON) um fortzufahren")
        layout.addWidget(self.info_label)
        
        # Tree-Widget zur Anzeige der Lesezeichen
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Lesezeichen")
        layout.addWidget(self.tree, stretch=1)
        
        # Buttons: Datei laden und Exportieren
        button_layout = QHBoxLayout()
        self.load_button = QPushButton("Chrome-Bookmarks laden")
        self.load_button.clicked.connect(self.load_bookmarks)
        button_layout.addWidget(self.load_button)
        
        self.export_button = QPushButton("Ausgewählte Bookmarks exportieren")
        self.export_button.clicked.connect(self.export_bookmarks)
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)
        
        layout.addLayout(button_layout)
    
    def load_bookmarks(self):
        options = QFileDialog.Option.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(self, "Chrome-Bookmarks JSON-Datei laden", "",
                                                   "JSON Dateien (*.json);;Alle Dateien (*)", options=options)
        if not file_path:
            return
        
        nodes = load_chrome_bookmarks(file_path)
        if nodes is None:
            return
        
        self.tree.clear()
        # Für jedes Wurzelverzeichnis (z. B. bookmark_bar, other, synced) einen Top-Level-Eintrag hinzufügen.
        for node in nodes:
            item = create_tree_item(node)
            # Optional: Man kann den Top-Level-Ordner immer standardmäßig aktivieren
            item.setCheckState(0, Qt.CheckState.Unchecked)
            self.tree.addTopLevelItem(item)
        self.info_label.setText("Bitte wähle die Bookmarks/Ordner zum Export aus (über die Checkboxen).")
        self.export_button.setEnabled(True)
    
    def export_bookmarks(self):
        # Erzeuge eine Datenstruktur der ausgewählten Einträge
        selected_structures = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            processed = process_tree_item(item)
            if processed is not None:
                selected_structures.append(processed)
        
        if not selected_structures:
            QMessageBox.information(self, "Export", "Es wurden keine Lesezeichen ausgewählt!")
            return
        
        # Generiere HTML
        html_output = export_to_html(selected_structures)
        
        # Speichere die HTML in eine Datei
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportiere Bookmarks nach HTML", "",
                                                   "HTML Dateien (*.html);;Alle Dateien (*)")
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_output)
            QMessageBox.information(self, "Export", f"Export erfolgreich in {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export-Fehler", str(e))

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
