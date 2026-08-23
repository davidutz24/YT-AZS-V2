# 🚀 YT AZS — Versiunea 12.0 (Update Major)

[![Release](https://img.shields.io/badge/release-v12.0-blue.svg)](https://github.com)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-brightgreen.svg)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Open%20Source-orange.svg)](https://github.com)

**YT AZS V12.0** este o aplicație modernă, completă și multi-platformă (**Windows** și **Linux**) pentru descărcarea videoclipurilor și pieselor audio la calitate maximă (până la 4K/8K și MP3 320 kbps), cu previzualizare în timp real și motoare multiple de extracție (**Multi-Source Engines**).

---

## 🌟 Noutăți Majore în Versiunea 12.0

### 1. 🔄 Multi-Source Download Engines (Motoare Multiple de Descărcare)
Aplicația include un selector dedicat de motoare organizate în ordinea optimă de viteză și stabilitate:
1. **Auto (Fallback inteligent pe toate sursele)**: Selectează automat cel mai optim motor și, dacă întâmpină restricții sau blocaje, comută instant la următorul până când descărcarea reușește.
2. **YT-DLP (Standard / Calitate Maximă)**: Motorul principal de mare viteză cu suport complet pentru toate formatele și codecurile.
3. **YT-DL (Classic / youtube-dl)**: Modul clasic cu opțiuni de compatibilitate legacy și fallback multi-client (`web`, `mweb`, `android`).
4. **NewPipe Extractor (Android InnerTube)**: Emulează profilul NewPipe / Android client, ocolind blocajele de boți și restricțiile de conținut web.
5. **9xBuddy (Universal Extractor)**: Extractor universal optimizat pentru mii de platforme media din întreaga lume.
6. **Cobalt Tools (API & Direct Stream)**: Interoghează instanțe Cobalt API (cu rotație automată din `cobalt.directory`), preia fluxul media și îl descarcă chunk-by-chunk direct pe PC cu bară de progres în timp real.

---

### 2. 🐧 Suport Nativ Complet pentru Linux & Windows
- **Linux**:
  - Script de pornire rapidă: `./run_linux.sh`
  - Script de construire executabil Linux: `./build_linux.sh` (creează binar independent în `dist/YT-AZS/YT-AZS` și fișier de lansare `yt-azs.desktop`)
  - Notificări desktop native prin `notify-send` și deschiderea folderului cu managerul nativ de fișiere (`xdg-open`).
- **Windows**:
  - Script de build complet: `build_ytazs.bat` (PyInstaller + generator script Inno Setup).
  - Installer modern: `installer/YT-AZS-Setup-V12.0.exe` cu scurtături Desktop și Start Menu.
  - Notificări native Windows Toast Balloon.

---

### 3. 🌐 Mod Web Browser (Zero-Dependency Web Mode)
Dacă doriți să rulați aplicația pe un server fără interfață grafică sau preferați să descărcați din browser-ul web preferat (Chrome, Firefox, Edge, Safari) pe calculator sau chiar de pe telefon/tabletă în rețeaua locală:
- Porniți pe Linux: `./run_web.sh` sau `python3 YT-AZS.py --web`
- Porniți pe Windows: `run_web.bat` sau `python YT-AZS.py --web`
- Serverul web pornește la `http://localhost:5000` cu o interfață modernă, reactivă, cu suport pentru temele Navy/Light și actualizări în timp real ale progresului prin JSON REST API.

---

### 4. 🎨 Design Modern & Funcționalități Avansate
- **Teme vizuale**: Temă întunecată **Navy** (implicită) și temă luminoasă **Light**.
- **Scroll Ultra-Fluid**: Motor de scroll rescris complet, perfect compatibil cu mouse-ul pe orice sistem de operare.
- **Previzualizare Video**: Copertă (thumbnail), titlu, autor și durată afișate instantaneu.
- **Auto Clipboard**: Preluare automată și inteligentă a link-urilor copiate în clipboard.
- **Limitator de viteză**: Rată de descărcare configurabilă (ex: `2M`, `500K` sau nelimitat).

---

## 📂 Structura Proiectului

```
YT-AZS/
├── YT-AZS.py                 # Aplicația principală Desktop GUI (CustomTkinter)
├── download_engines.py       # Modulul motoarelor multiple (YT-DLP, NewPipe, Cobalt, etc.)
├── web_server.py             # Serverul pentru Modul Web Browser
├── requirements.txt          # Dependențele Python standard
├── build_linux.sh            # Script Linux Builder pentru generare executabil
├── build_ytazs.bat           # Script Windows Builder (PyInstaller + Inno Setup)
├── setup_ytazs.iss           # Configurația Inno Setup pentru installer Windows
├── run_linux.sh              # Script lansator pentru Linux
├── run_web.sh                # Lansator rapid mod Web pe Linux
├── run_web.bat               # Lansator rapid mod Web pe Windows
├── logo_white_PNG.png        # Logo temă dark
├── logo_black_PNG.png        # Logo temă light
├── YT-AZS.ico                # Iconița aplicației
├── .gitignore                # Fișiere ignorate la commit
├── .github/workflows/        # Automatizare build & release pe GitHub Actions
└── README.md                 # Documentația completă
```

---

## 🛠️ Instrucțiuni de Rulare și Instalare

### 🐧 Pe Linux:
1. Instalați dependențele de sistem:
   ```bash
   sudo dnf install python3 python3-tkinter ffmpeg   # Fedora / RHEL
   # sau:
   sudo apt install python3 python3-tk ffmpeg        # Ubuntu / Debian
   ```
2. Rulați aplicația:
   ```bash
   chmod +x run_linux.sh
   ./run_linux.sh
   ```
3. Sau construiți executabilul de sine stătător:
   ```bash
   chmod +x build_linux.sh
   ./build_linux.sh
   ```

---

### 🪟 Pe Windows:
1. Rulați direct cu Python:
   ```cmd
   pip install -r requirements.txt
   python YT-AZS.py
   ```
2. Pentru a genera executabilul `.exe` și Installer-ul:
   - Rulați `build_ytazs.bat`
   - Deschideți `setup_ytazs.iss` în **Inno Setup** și apăsați `Compile` (Ctrl+F9).
   - Installer-ul va fi generat în `installer\YT-AZS-Setup-V12.0.exe`.

---

## 📄 Credite & Drepturi de Autor
- **Autor**: David Marica - AZS Gherla
- **Versiune**: 12.0 (August 2026)
- **Copyright**: © 2026 David Marica - AZS Gherla
