# Peugeot-UWB-Firmware

Signierte Firmware für die **Keyless-Box** (ESP32 + UWB) aus dem Projekt Peugeot Keyless. Die App „Peugeot Keyless“
(ab 1.12.0) holt sich hier die Firmware und spielt sie per Bluetooth in die Box (ab Firmware 1.11.0):
Schlüssel › Firmware › „Nach Update suchen“ › „Jetzt aktualisieren“.

Hier liegt **kein Quelltext und kein Schlüssel**, nur:

| Datei | Inhalt |
|---|---|
| `firmware.json` | welche Version die App anbietet: Kanal `stabil` (im Auto getestet) und `beta` (Vorabversion) |
| `bins/uwbfira-X.Y.Z.bin` | signierte Firmware (ESP32-Abbild + 88 Byte Signatur-Anhang) |
| `schluessel.txt` | die öffentlichen Schlüssel, mit denen die Box Firmware annimmt |
| `pruefen.py` | prüft alle Dateien hier selbst nach (Python 3 + `pip install cryptography`) |

## Warum das sicher ist

- **Nur Tommys Signatur zählt.** Jede Datei ist mit ECDSA P-256 signiert. Der private Schlüssel liegt nur auf Tommys PC
  (mit Passwort), nie auf GitHub, nie in einem Workflow und nie bei einer KI. Signiert wird ausschließlich lokal.
- **Die Box prüft selbst**, bevor sie umschaltet: Keyless-Kennung, ESP32-Abbild, Signatur gegen die eingebauten
  öffentlichen Schlüssel, Sicherheitsstand (kein Zurückspielen alter Firmware mit bekannter Lücke). Danach läuft die neue
  Firmware „auf Probe“ und wird erst bestätigt, wenn UWB läuft und sich das Besitzer-Handy wieder anmeldet – sonst
  springt die Box von selbst auf die alte Firmware zurück.
- **Die App prüft vorher auch:** Pfad nur `bins/*.bin` in diesem Repo, Größe, SHA-256, Version in der Datei, Signatur.
  Sie bietet nur Versionen an, die neuer sind als die im Auto.
- **Nur das Besitzer-Handy** darf ein Update starten, nur bei ausgeschalteter Zündung.
- `firmware.json` selbst ist nicht signiert. Wer dieses Repo verändert, kann deshalb höchstens ein Update verhindern oder
  eine ältere echte Version anbieten (die App nimmt nur neuere). Eigene Firmware auf die Box bringen kann er nicht.

## Öffentliche Schlüssel

| Name | Schlüssel-ID | Zweck |
|---|---|---|
| Haupt | `41f1e8c6af15acbe` | jede Veröffentlichung |
| Not | `1f6440d08e7e77f9` | nur falls der Hauptschlüssel verloren geht (offline verwahrt) |

Die vollständigen Schlüssel stehen in `schluessel.txt`. Schlüssel-ID = die ersten 8 Bytes von SHA-256 des Schlüssels
(65 Bytes `04|X|Y`).

## Signaturformat

`firmware.bin | "KEYLSIG1" | Länge (4, LE) | Sicherheitsstand (4, LE) | Schlüssel-ID (8) | r (32) | s (32)`

Signiert ist SHA-256 über `firmware.bin` und die ersten 24 Bytes des Anhangs. Der ESP32-Bootloader ignoriert den Anhang.

## Selbst nachprüfen

```
pip install cryptography
python pruefen.py
```

prüft für jeden Eintrag in `firmware.json` Größe, SHA-256, Version und Signatur.

## Veröffentlichen (nur Tommy)

Auf Tommys PC im Projekt-Repo, nach dem lokalen Signieren:

```
python tools/fw_veroeffentlichen.py uwbfira-X.Y.Z.bin                  # als beta
python tools/fw_veroeffentlichen.py uwbfira-X.Y.Z.bin --kanal stabil   # nach dem Test im Auto
```

Das Werkzeug prüft die Signatur, trägt die Datei hier ein und pusht.
