# 🚀 YT AZS — Versiunea 12.1

[![Release](https://img.shields.io/badge/release-v12.1-blue.svg)](https://github.com)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-brightgreen.svg)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Open%20Source-orange.svg)](https://github.com)

**YT AZS V12.1** este o aplicație modernă, completă și multi-platformă (**Windows** și **Linux**) dedicată descărcării de conținut video și audio la calitate maximă (de la 360p până la 4K/8K și MP3 320 kbps, FLAC, M4A), cu previzualizare în timp real și motoare multiple de extracție (**Multi-Source Download Engines**).

---

## 🌟 Noutăți în Versiunea 12.1

- **Optimizare completă a meniurilor**: Corectarea selecției din listele derulante (surse de descărcare, formate video/audio, selecție cookies browser) pentru un răspuns instantaneu și fără lag.
- **Sistem de derulare ultra-fluid (Mouse Scroll)**: Mecanism rescris de derulare cu detecție geometrică directă a cursorului, garantând derulare lină pe orice sistem Windows sau distribuție Linux.
- **Actualizare identitate și copyright**: Informații de proiect actualizate oficial sub egida **Biserica Adventistă Gherla**.
- **Stabilitate sporită a descărcărilor**: Mecanisme perfecționate de fallback automat pe motoare alternative (YT-DLP, NewPipe, 9xBuddy, Cobalt Tools) în cazul restricțiilor de rețea sau boți.

---

## 🔄 Motoare de Descărcare Suportate

1. **Auto (Fallback inteligent)**: Selectează automat cel mai potrivit motor și comută la următorul dacă apar erori sau limitări de stream.
2. **YT-DLP (Standard / Calitate Maximă)**: Motorul de bază de mare viteză cu suport complet pentru toate rezoluțiile și codecurile moderne.
3. **YT-DL (Classic / youtube-dl)**: Mod compatibil legacy cu fallback multi-client (`web`, `mweb`, `android`).
4. **NewPipe Extractor (Android InnerTube)**: Emulează profilul mobil NewPipe / Android client, ocolind blocajele automate.
5. **9xBuddy (Universal Extractor)**: Suport extins pentru multiple platforme media internaționale.
6. **Cobalt Tools (API & Direct Stream)**: Interogare instanțe Cobalt API cu descărcare directă a fluxului media pe calculator.

---

## 🌐 Mod Web Browser (Zero-Dependency)

Dacă doriți să folosiți aplicația pe un server fără interfață grafică sau preferați să descărcați direct din browser (Chrome, Firefox, Edge, Safari):
- **Linux**: `./run_web.sh` sau `python3 YT-AZS.py --web`
- **Windows**: `run_web.bat` sau `python YT-AZS.py --web`
- Accesați interfața la adresa locală `http://localhost:5000` (cu suport pentru teme Navy/Light și monitorizare în timp real).

---

## 📂 Structura Proiectului

```
YT-AZS/
├── YT-AZS.py                 # Aplicația principală Desktop GUI (CustomTkinter)
├── download_engines.py       # Modulul motoarelor multiple (YT-DLP, NewPipe, Cobalt etc.)
├── web_server.py             # Serverul pentru Modul Web Browser
├── requirements.txt          # Dependențele Python standard
├── build_linux.sh            # Script compilare executabil binar Linux
├── build_ytazs.bat           # Script Windows Builder (PyInstaller + Inno Setup)
├── setup_ytazs.iss           # Configurația Inno Setup pentru installer Windows
├── run_linux.sh              # Script lansator pentru Linux
├── run_web.sh                # Lansator rapid mod Web pe Linux
├── run_web.bat               # Lansator rapid mod Web pe Windows
├── logo_white_PNG.png        # Siglă temă dark
├── logo_black_PNG.png        # Siglă temă light
├── YT-AZS.ico                # Iconița oficială a aplicației
├── .gitignore                # Fișiere excluse din controlul versiunilor
├── .github/workflows/        # Automatizare build & release în cloud (GitHub Actions)
└── README.md                 # Documentația oficială a aplicației
```

---

## 🛠️ Instrucțiuni de Instalare și Rulare

### 🐧 Pe Linux:
1. Instalați pachetele de bază:
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
3. Pentru a genera executabilul binar autonom:
   ```bash
   chmod +x build_linux.sh
   ./build_linux.sh
   ```

---

### 🪟 Pe Windows:
1. Rulare din codul sursă:
   ```cmd
   pip install -r requirements.txt
   python YT-AZS.py
   ```
2. Pentru a genera pachetul de instalare `.exe`:
   - Rulați `build_ytazs.bat`
   - Deschideți `setup_ytazs.iss` în **Inno Setup** și apăsați `Compile` (Ctrl+F9).
   - Installer-ul final va fi generat în: `installer\YT-AZS-Setup-V12.1.exe`.

---

## 📄 Credite & Drepturi de Autor

- **Dezvoltat pentru**: Biserica Adventistă Gherla
- **Versiune**: 12.1 (Septembrie 2026)
- **Copyright**: © Biserica Adventistă Gherla
- **Licență**: Open-source pentru comunitate
