# GenreSplitter – Volledige Gebruikershandleiding
**Versie:** 2.9.2 (Final)  
**Doelgroep:** Eindgebruikers (beginner tot gevorderd)  
**Platform:** Windows  

---

## Inhoudsopgave

1. Wat is GenreSplitter  
2. Voorbereiding en installatie  
3. Eerste keer opstarten  
4. Overzicht van het hoofdscherm  
5. Bronmap instellen (Source)  
6. Doelmap instellen (Target)  
7. Instellingen – Algemeen  
8. Instellingen – Metadata en iTunes  
9. Instellingen – Overschrijfbeleid (Confidence)  
10. Instellingen – Cover-only modus  
11. Instellingen – Rapportage  
12. Starten van een sorteerrun  
13. Wat gebeurt er tijdens het sorteren  
14. Stoppen van een run  
15. Wat gebeurt er bij fouten  
16. Controle van het resultaat  
17. Veelvoorkomende scenario’s  
18. Aanbevolen instellingen (praktijkvoorbeelden)  
19. Prestatie- en stabiliteitstips  
20. Beperkingen en aandachtspunten  
21. Veelgestelde vragen  

---

## 1. Wat is GenreSplitter

GenreSplitter is een desktopprogramma dat audiobestanden:

- analyseert,
- voorziet van correcte metadata (zoals genre en albumcover),
- en **verplaatst naar mappen op basis van genre**.

Het programma is ontworpen voor:
- grote muziekcollecties,
- minimale handmatige correctie,
- maximale betrouwbaarheid.

Belangrijk uitgangspunt:
> **Eén audiobestand wordt altijd maar één keer verplaatst en nooit gekopieerd.**

---

## 2. Voorbereiding en installatie

### 2.1 Vereisten
- Windows 10 of hoger
- Python 3.9 t/m 3.13 geïnstalleerd
- Internetverbinding (voor metadata via iTunes)

### 2.2 Installatie
1. Pak het ZIP-bestand uit (bijv. `GenreSplitter-2.9.2.zip`)
2. Open de map
3. Installeer afhankelijkheden:
   ```powershell
   pip install -r requirements.txt
Start de app:

powershell
Code kopiëren
python main.py
3. Eerste keer opstarten
Bij het starten zie je:

een kort splash screen

daarna het hoofdvenster

Er worden nog geen bestanden aangepast totdat je expliciet op Start klikt.

4. Overzicht van het hoofdscherm
Het hoofdscherm bestaat uit:

Bronmap (Source)

Doelmap (Target)

Instellingen (meerdere tabs)

Actieknoppen (Start / Stop)

Status- en voortgangsweergave

5. Bronmap instellen (Source)
Wat is de bronmap?
De map waarin je ongeordende muziekbestanden staan.

Zo stel je deze in:
Klik op Bladeren… bij “Bronmap”

Kies de map met je muziek

Bevestig

Gedrag:
Alle ondersteunde audiobestanden worden meegenomen

Submappen worden automatisch doorzocht

Niet-ondersteunde bestanden worden genegeerd

6. Doelmap instellen (Target)
Wat is de doelmap?
De map waarin GenreSplitter nieuwe genre-mappen aanmaakt.

Voorbeeld:

Code kopiëren
Music_Sorted/
├── Rock/
├── Jazz/
├── Electronic/
Belangrijk:
Bestanden worden verplaatst, niet gekopieerd

Er ontstaan geen duplicaten

7. Instellingen – Algemeen
7.1 Metadata bijwerken
Bepaalt hoe bestaande metadata wordt aangepast.

Opties:

Altijd overschrijven

Overschrijven alleen bij hoge matchscore

Alleen cover bijwerken

Aanbevolen voor de meeste gebruikers:
✔ Overschrijven alleen bij hoge matchscore

8. Instellingen – Metadata en iTunes
8.1 iTunes metadata gebruiken
Wanneer ingeschakeld:

GenreSplitter haalt metadata op via iTunes

Dit omvat genre, album, cover en releasedatum

8.2 Single-winner principe
Als iTunes meerdere resultaten teruggeeft:

slechts één beste match wordt gekozen

voorkomt dat één nummer in meerdere genres belandt

9. Instellingen – Overschrijfbeleid (Confidence)
Wat is confidence?
Een score (0–100) die aangeeft hoe goed:

artiest

titel
overeenkomen met de metadata-bron.

Confidence-drempel
Alleen als de score boven deze waarde ligt, wordt bestaande metadata overschreven

Lagere scores vullen alleen lege velden

Standaardwaarde: 85

10. Instellingen – Cover-only modus
Wanneer ingeschakeld:

Alleen albumcover wordt bijgewerkt

Titel, artiest, album en genre blijven ongewijzigd

Handig wanneer:

je metadata al klopt

maar covers ontbreken of inconsistent zijn

11. Instellingen – Rapportage
Na elke run kan GenreSplitter:

een overzicht maken van verwerkte bestanden

fouten en overgeslagen bestanden bijhouden

Rapporten helpen bij controle, maar zijn niet verplicht.

12. Starten van een sorteerrun
Controleer bron- en doelmap

Controleer instellingen

Klik op Start

Vanaf dit moment:

worden bestanden één voor één verwerkt

blijft de interface bruikbaar

13. Wat gebeurt er tijdens het sorteren
Voor elk bestand:

Bestand wordt geanalyseerd

Bestaande metadata wordt gelezen

iTunes metadata wordt opgehaald (indien actief)

Confidence-score wordt berekend

Metadata wordt aangepast volgens beleid

Genre wordt bepaald

Bestand wordt verplaatst naar juiste map

14. Stoppen van een run
Klik op Stop om:

de huidige run netjes af te breken

geen half-verplaatste bestanden achter te laten

15. Wat gebeurt er bij fouten
Als één bestand niet verwerkt kan worden:

het bestand wordt overgeslagen

de run gaat verder

de applicatie blijft stabiel

Veelvoorkomende oorzaken:

bestand in gebruik

te lange bestandsnaam

geen schrijfrechten

16. Controle van het resultaat
Na afloop:

controleer de doelmap

controleer een paar bestanden in een tag-editor (optioneel)

GenreSplitter past metadata conservatief aan.

17. Veelvoorkomende scenario’s
“Mijn bestanden staan al in submappen”
Dat is geen probleem; GenreSplitter kijkt alleen naar de bestanden zelf.

“Ik wil niets overschrijven”
Gebruik:

confidence-modus met hoge drempel

of cover-only modus

18. Aanbevolen instellingen (praktijkvoorbeelden)
Grote collectie (veilig)
Confidence: 90

Metadata: confidence-modus

Cover-only: uit

Alleen covers repareren
Cover-only: aan

iTunes: aan

19. Prestatie- en stabiliteitstips
Gebruik SSD/NVMe

Sluit muziekspelers

Schakel antivirus-exclusies in

Werk in batches bij zeer grote libraries

20. Beperkingen
Geen undo-functie

Geen live preview

Geen automatische metadata-cache

Deze keuzes zijn bewust gemaakt voor betrouwbaarheid.

21. Samenvatting
GenreSplitter is ontworpen om:

grote muziekcollecties veilig te ordenen

metadata gecontroleerd te verbeteren

zonder duplicaten of crashes

Bij correct gebruik is het een betrouwbaar eindproduct.

## v2.10.8 – UI & Documentation Update
**Release date:** 27-December-2025

### UI
- Dropdowns now show a clear ▼ arrow indicator
- Visible border when expanded
- Improved contrast, focus and hover states

### Genre system
- Vastly reduced incorrect `Other` assignments
- Added and normalized top-level genres (Dance, Indie, Trance, House, EDM, etc.)
- iTunes fallback when primary APIs return unmapped genres

### Stability
- `hang.log` disabled
- Subprocess API resolver stabilized
- Improved Unicode handling
