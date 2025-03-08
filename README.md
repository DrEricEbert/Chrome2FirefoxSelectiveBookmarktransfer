# PyQT Gui to transfers Chrome Bookmarks selective to Firefox

Python‑Script, das:
Eine PyQt6‑Oberfläche bereitstellt, mit der du eine Chrome‑Bookmarks‑Datei (im JSON‑Format) laden kannst.
Die Lesezeichen inklusive Ordnerstruktur in einem Tree-Widget anzeigt, wobei jeder Eintrag (Ordner oder einzelnes Lesezeichen) über ein Kontrollkästchen verfügt.
Die ausgewählten Einträge (mit deren Ordnerstruktur) in das Netscape‑Bookmark‑HTML‑Format (welches Firefox importieren kann) exportiert.

### Hinweise
- Der Pfad zu den Chrome‑Bookmarks liegt typischerweise etwa bei
  - Windows:
        ```C:\Users\<Benutzer>\AppData\Local\Google\Chrome\User Data\Default\Bookmarks```
  - Linux:
        ```~/.config/google-chrome/Default/Bookmarks```
    
- Das Script geht davon aus, dass die Chrome‑Bookmarks im JSON‑Format vorliegen (also nicht aus einem bereits exportierten HTML‑File).
- Dieses Beispiel exportiert nur die Einträge, die entweder direkt ausgewählt sind oder in denen (bei Ordnern) mindestens ein untergeordneter Eintrag ausgewählt wurde.
      
### Erklärung

- Laden der Chrome‑Bookmarks:
    Über den Button „Chrome-Bookmarks laden“ wird mit einem Dateidialog eine JSON‑Datei ausgewählt. Die Funktion load_chrome_bookmarks() liest diese ein und filtert die interessanten Ordner (wie „bookmark_bar“, „other“, „synced“) aus.

- Darstellung in einem Tree-Widget:
    Mit der Funktion create_tree_item() wird rekursiv ein QTreeWidgetItem erstellt, das jeweils ein Lesezeichen oder einen Ordner repräsentiert. Jeder Eintrag verfügt über ein Kontrollkästchen, sodass du gezielt auswählen kannst, was exportiert werden soll.

- Auswahl und Export:
    Beim Klick auf „Ausgewählte Bookmarks exportieren“ wird rekursiv die ausgewählte Struktur (über process_tree_item()) eingelesen. Anschließend wird mit export_to_html() ein HTML‑String im Netscape‑Format generiert. Über einen Dateidialog kannst du dann eine Zieldatei    wählen, in die die HTML‑Datei gespeichert wird. Diese Datei kann später in Firefox importiert werden.
