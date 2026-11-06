# PS5-WebKit: dokumentierter Quellcodevergleich

Dieses Projekt erstellt einen **statischen Versionsvergleich** von zwei Quellcode-Paketen. Es enthält **keinen Jailbreak, keinen Exploit und keine PS5-Payload**. Es führt nichts auf der Konsole aus.

## Welches Material wird verglichen?

Sony listet auf der [offiziellen PS5-WebKit-Seite](https://www.playstation.com/en-us/oss/ps5/webkit/) Quellcode für die Gruppen **12.00–14.00** und **14.00–**. Die scheinbar überlappenden Bezeichnungen stammen von Sony; daraus allein lässt sich nicht ableiten, welcher Einzel-Build exakt auf PS5-Firmware 14.22 läuft.

- Altes Paket: `WebKit-1200.zip` (Gruppe 12.00–14.00)
- Neueres Paket: `WebKit_1400.zip` (Gruppe 14.00–)

**Wichtig:** Das Ergebnis ist nur ein Vergleich *veröffentlichter Quellcodepakete*. Ein geänderter Dateiname ist keine Sicherheitslücke, und ein möglicherweise veralteter Codeabschnitt ist kein Beweis für einen Exploit auf 14.22.

## Am Handy mit GitHub Actions

1. Erstelle ein **neues** GitHub-Repository, z. B. `ps5-webkit-forschung` (getrennt von deiner PS5-Browser-Testseite).
2. Entpacke die ZIP-Datei auf deinem Handy und lade **den Inhalt des Projektordners** hoch, einschließlich `.github/workflows/compare.yml`. Die Ordnerstruktur muss im Stamm des Repositories liegen.
3. Öffne **Actions → PS5 WebKit Quellcodevergleich → Run workflow**.
4. Wähle `demo` für einen kleinen Funktionstest oder `official` für Sonys Quellcodepakete. Mit `official` lädt GitHub Actions die großen Archive direkt von Sonys öffentlich verlinkter Website herunter. Die Downloads können scheitern, wenn Sony die Links ändert oder die Archive nicht erreichbar sind.
5. Nach Abschluss: **Actions → Lauf → Artifacts → webkit-vergleich-...**. Lade das ZIP mit `bericht.md` und `details.json` herunter. Die Dateien werden beim Vergleich unter `reports/` erstellt.

Der Demo-Modus vergleicht **ausschließlich erfundene Testdateien**, keine Sony-Dateien. In den Ergebnissen wird dieser Modus deutlich markiert. Nur der `official`-Modus verwendet die echten öffentlich angebotenen Archive.

## Was genau prüft das Skript?

- Gemeinsame, neue, entfernte und inhaltlich veränderte Dateipfade.
- Für ZIP-Pakete: Größe und CRC32 als **schnelle Vorprüfung** (keine kryptografische Echtheitsprüfung).
- Für einige kleinere veränderte Textdateien: kurze Ausschnitte des Unified-Diffs.
- Ausgabe eines lesbaren Berichts und maschinenlesbarer JSON-Daten.

Keine automatische Identifizierung von Schwachstellen. Eine Sicherheitsbewertung erfordert unabhängige Codeprüfung und reproduzierbare Forschung.

## Grenzen

- Große Archive benötigen Speicherplatz und Rechenzeit; GitHub hat Laufzeit-/Speicherlimits.
- ZIP-Inhalte werden **nicht** ausgepackt. Das Skript liest sie als Archivdaten.
- Unterschiede im Archivaufbau können viele umbenannte Pfade erzeugen. Hierzu enthält der Bericht Hinweise.
- Weil Sonys Quellcode Open-Source-Lizenzen unterliegt, liegt der **fremde Quellcode nicht** diesem Repository bei; er wird nur für den Vergleich geladen.
- Kein Downgrade, keine Firmware-Änderung, keine PSN-Anmeldedaten oder Konsolenbefehle nötig.

## Quellennachweis

- Sony: https://www.playstation.com/en-us/oss/ps5/webkit/
- Verwendete Sony-Downloadadressen werden in `.github/workflows/compare.yml` festgehalten.

Stand der Dokumentation: 2026-11-06.
