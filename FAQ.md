# Frequently Asked Questions (FAQ)


## Instellingen en API-tokens (opslaglocatie)

GenreSplitter slaat **jouw instellingen en API-tokens lokaal per gebruiker** op in:

- Windows: `%APPDATA%\GenreSplitter\settings.json`

In de projectmap meegeleverd `settings.json` / `genresplitter_settings.example.json` zijn **voorbeelden** en bevatten in deze clean release **geen tokens**.

This FAQ applies to the **Beta** phase of GenreSplitter.

---

## Troubleshooting

### App does not start
**Possible causes**
- Missing dependencies
- PyQt6 not installed
- Wrong Python environment

**What to do**
1. Activate your virtual environment
2. Run `pip install -r requirements.txt`
3. Verify with `python -c "import PyQt6"`

---

### Splashscreen appears but app closes
**Possible causes**
- Broken configuration file
- Incompatible version upgrade

**What to do**
- Delete `%APPDATA%\GenreSplitter\genresplitter_settings.json`
- Restart GenreSplitter

---

### No files are moved
**Possible causes**
- Dry-run is enabled
- No valid genre detected

**What to do**
- Disable Dry-run
- Check status window for skipped files

---

### Permission errors
**Possible causes**
- Target folder is protected

**What to do**
- Use a user-writable folder (Documents/Music)

---

### Log file not created
**Possible causes**
- Logging disabled
- No actions executed

**What to do**
- Enable logging in Settings
- Perform a sort action
## AcoustID / fpcalc not detected

If you installed `fpcalc.exe` but GenreSplitter cannot find it:

1) Verify in PowerShell:
```powershell
Get-Command fpcalc
fpcalc -version
```
2) If it is not found, add the folder containing `fpcalc.exe` to your PATH and restart PowerShell.
3) Alternatively, set an explicit override for GenreSplitter:
```powershell
$env:GENRESPLITTER_FPCALC = "C:\path\to\fpcalc.exe"
python main.py
```


### iTunes maakt een kopie van tracks na het sorteren

Als iTunes/Apple Music is ingesteld op **“Copy files to iTunes Media folder when adding to library”** en/of **“Keep iTunes Media folder organized”**, dan kan iTunes een track **opnieuw kopiëren** of verplaatsen zodra een bestand buiten iTunes om wordt verplaatst. Dit kan lijken alsof er een extra kopie in een (genre)map wordt gemaakt.

Oplossing:
- Zet in iTunes **Copy files to iTunes Media folder…** uit als je wilt dat iTunes verwijst naar het bestand op zijn nieuwe locatie.
- Of sorteer naar een map **buiten** de iTunes Media folder en voeg die map toe aan iTunes met kopiëren uitgeschakeld.
- GenreSplitter verplaatst bestanden (geen kopie); dubbele bestanden worden vrijwel altijd door iTunes-instellingen veroorzaakt.

## AcoustID en MusicBrainz fallback

Wanneer AcoustID geen genre oplevert, mag GenreSplitter tijdelijk MusicBrainz raadplegen als fallback. Dit zet de MusicBrainz-instelling in de UI niet permanent aan; het is uitsluitend voor die specifieke lookup.

