#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YT-AZS V12.0 - Built-in Web Browser Server Mode
Zero-dependency HTTP server providing full web-based video downloader UI.
"""

import os
import sys
import json
import time
import threading
import subprocess
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from download_engines import ENGINE_LIST, get_engine_by_name

# Import format lists from YT-AZS or define them
VIDEO_FORMATS = [
    "Video - MP4  ProPresenter/Compatibil (H.264+AAC)",
    "Video - MP4  (1080p H.264+AAC)",
    "Video - MP4  (720p  H.264+AAC)",
    "Video - MP4  (480p  H.264+AAC)",
    "Video - MP4  (360p  H.264+AAC)",
    "Video - MP4  (Maxim 4K/8K - toate codecurile)",
    "Video - MKV  (Calitate Maxima)",
    "Video - WEBM (VP9/Opus)",
]
AUDIO_FORMATS = [
    "Audio - MP3  (320 kbps)",
    "Audio - M4A  (AAC)",
    "Audio - FLAC (Lossless)",
    "Audio - OPUS (Opus)",
    "Audio - OGG  (Vorbis)",
    "Audio - WAV  (Necomprimat)",
]
FORMAT_OPTIONS = VIDEO_FORMATS + AUDIO_FORMATS

# Global App State
app_state = {
    "is_downloading": False,
    "is_cancelled": False,
    "progress": 0.0,
    "pct_text": "0%",
    "speed_text": "",
    "eta_text": "",
    "status_text": "Gata de descărcare.",
    "status_color": "muted",
    "logs": [],
    "lock": threading.Lock(),
    "config": {
        "last_path": os.path.join(os.path.expanduser("~"), "Downloads"),
        "engine": ENGINE_LIST[0],
        "format": FORMAT_OPTIONS[0],
        "playlist": False,
        "subtitles": False,
        "thumbnail": True,
        "speed_limit": "",
        "cookies_browser": "Niciunul",
        "theme": "navy",
    }
}

def log_message(msg, color_key="muted"):
    timestamp = time.strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    with app_state["lock"]:
        app_state["logs"].append({"text": line, "color": color_key})
        if len(app_state["logs"]) > 300:
            app_state["logs"].pop(0)

def resolve_config_file():
    if sys.platform == "win32":
        appdata = os.getenv("APPDATA")
        if appdata:
            return os.path.join(appdata, "YT AZS", "ytdlp_config.json")
    else:
        xdg_config = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return os.path.join(xdg_config, "yt-azs", "ytdlp_config.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "ytdlp_config.json")

def load_saved_config():
    cfg_file = resolve_config_file()
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                app_state["config"].update(data)
        except Exception:
            pass

def save_current_config():
    cfg_file = resolve_config_file()
    try:
        folder = os.path.dirname(cfg_file)
        if folder: os.makedirs(folder, exist_ok=True)
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(app_state["config"], f, indent=2, ensure_ascii=False)
    except Exception:
        pass

HTML_PAGE = """<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YT AZS V12.0 - Web Browser Mode</title>
    <style>
        :root {
            --bg: #1A1A1A;
            --surface: #2B2B2B;
            --surface2: #373737;
            --border: #4A4A4A;
            --accent: #58C7FF;
            --accent-dim: #0D8FE6;
            --text: #F2F4F8;
            --muted: #A9B0BA;
            --success: #41C784;
            --warning: #F5C451;
            --danger: #EF6B6B;
            --log-bg: #232323;
        }
        [data-theme="sky"] {
            --bg: #060911;
            --surface: #0C1220;
            --surface2: #111B30;
            --border: #1A2B47;
            --accent: #38BDF8;
            --accent-dim: #0284C7;
            --text: #DCE9F7;
            --muted: #7AA2C8;
            --log-bg: #040609;
        }
        [data-theme="light"] {
            --bg: #EDF1FA;
            --surface: #FFFFFF;
            --surface2: #E2EAF7;
            --border: #BAC8E0;
            --accent: #0284C7;
            --accent-dim: #0369A1;
            --text: #0C1A2E;
            --muted: #3D5A7A;
            --log-bg: #E2EAF7;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }
        body { background: var(--bg); color: var(--text); padding: 20px; transition: all 0.2s ease; }
        .container { max-width: 900px; margin: 0 auto; display: flex; flex-direction: column; gap: 14px; }
        header { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 14px 20px; display: flex; align-items: center; justify-content: space-between; }
        .brand { display: flex; align-items: center; gap: 12px; }
        .brand h1 { font-size: 20px; color: var(--accent); }
        .brand span { font-size: 11px; color: var(--muted); }
        .header-actions { display: flex; gap: 10px; }
        .btn { background: var(--surface2); color: var(--text); border: 1px solid var(--border); border-radius: 8px; padding: 8px 16px; cursor: pointer; font-size: 13px; font-weight: 600; transition: all 0.15s; }
        .btn:hover { background: var(--accent-dim); color: #fff; }
        .btn-primary { background: var(--accent-dim); color: #fff; border: none; }
        .btn-primary:hover { background: var(--accent); }
        .btn-danger { background: var(--surface2); color: var(--danger); }
        .btn-danger:hover { background: var(--danger); color: #fff; }
        .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 16px 20px; display: flex; flex-direction: column; gap: 12px; }
        .card-title { font-size: 12px; font-weight: bold; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; border-left: 3px solid var(--accent); padding-left: 8px; }
        .row { display: flex; gap: 12px; align-items: center; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
        @media(max-width: 700px) { .grid-2 { grid-template-columns: 1fr; } }
        input[type="text"], select { width: 100%; background: var(--surface2); color: var(--text); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; font-size: 13px; outline: none; }
        input[type="text"]:focus, select:focus { border-color: var(--accent); }
        .preview-box { display: flex; gap: 14px; align-items: center; }
        .preview-thumb { width: 120px; height: 68px; background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; object-fit: cover; display: flex; align-items: center; justify-content: center; color: var(--muted); font-size: 11px; flex-shrink: 0; }
        .preview-info { display: flex; flex-direction: column; gap: 4px; overflow: hidden; }
        .preview-title { font-weight: 600; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .preview-meta { font-size: 12px; color: var(--muted); }
        .checkbox-group { display: flex; flex-direction: column; gap: 10px; }
        .checkbox-item { display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--text); cursor: pointer; }
        .checkbox-item input { cursor: pointer; accent-color: var(--accent-dim); width: 16px; height: 16px; }
        .progress-bar-container { background: var(--surface2); border-radius: 6px; height: 10px; overflow: hidden; position: relative; margin: 6px 0; }
        .progress-bar { background: var(--accent); height: 100%; width: 0%; transition: width 0.15s ease; }
        .progress-header { display: flex; justify-content: space-between; font-size: 12px; }
        .progress-meta { display: flex; justify-content: space-between; font-size: 11px; color: var(--muted); }
        .log-box { background: var(--log-bg); border: 1px solid var(--border); border-radius: 8px; height: 140px; overflow-y: auto; padding: 10px; font-family: monospace; font-size: 11px; display: flex; flex-direction: column; gap: 4px; }
        .log-line { color: var(--muted); }
        .log-accent { color: var(--accent); }
        .log-success { color: var(--success); }
        .log-warning { color: var(--warning); }
        .log-danger { color: var(--danger); }
        .action-bar { display: flex; gap: 12px; align-items: center; }
        .btn-large { padding: 14px 28px; font-size: 16px; font-weight: bold; border-radius: 10px; }
        @keyframes rotateSpinner {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .circle-spinner {
            display: inline-block;
            width: 15px;
            height: 15px;
            border-radius: 50%;
            border: 2.5px solid rgba(255, 255, 255, 0.25);
            border-top-color: #ffffff;
            animation: rotateSpinner 0.75s linear infinite;
            vertical-align: middle;
            margin-right: 7px;
        }
        .circle-spinner.accent-spin {
            border: 2.5px solid rgba(56, 189, 248, 0.25);
            border-top-color: var(--accent);
        }
    </style>
</head>
<body data-theme="navy">
<div class="container">
    <header>
        <div class="brand">
            <div>
                <h1>YT AZS V12.0</h1>
                <span>Multi-Source Video Downloader (Web Browser Mode)</span>
            </div>
        </div>
        <div class="header-actions" style="display:flex; align-items:center; gap:8px;">
            <button class="btn" onclick="openAboutModal()" style="width:34px; height:34px; border-radius:50%; padding:0; font-weight:bold; font-size:14px; display:inline-flex; align-items:center; justify-content:center;" title="Despre YT AZS">i</button>
            <button class="btn" onclick="toggleTheme()" id="btn-theme">Light</button>
            <button class="btn" onclick="updateYtdlp()" id="btn-update">Actualizare Surse</button>
        </div>
    </header>

    <!-- Sursa / Engine -->
    <div class="card">
        <div class="card-title">Sursa de descărcare (Download Engine / Backend)</div>
        <select id="engine-select" onchange="saveConfig()">
            <!-- Options populated dynamically -->
        </select>
    </div>

    <!-- URL Input & Preview -->
    <div class="card">
        <div class="card-title">URL Video / Playlist</div>
        <div class="row">
            <input type="text" id="url-input" placeholder="https://www.youtube.com/watch?v=... sau link playlist / video" oninput="onUrlChange()">
            <button class="btn btn-primary" onclick="pasteUrl()">Paste</button>
        </div>
        <div class="preview-box" id="preview-box">
            <img id="preview-img" class="preview-thumb" src="" style="display:none;">
            <div id="preview-placeholder" class="preview-thumb">Fără preview</div>
            <div class="preview-info">
                <div class="preview-title" id="preview-title">Introdu un link YouTube pentru previzualizare</div>
                <div class="preview-meta" id="preview-meta">Detectare automată</div>
            </div>
        </div>
    </div>

    <!-- Format & Optiuni -->
    <div class="grid-2">
        <div class="card">
            <div class="card-title">Format descărcare</div>
            <div class="row">
                <button class="btn btn-primary" style="flex:1" id="type-video" onclick="setType('Video')">Video</button>
                <button class="btn" style="flex:1" id="type-audio" onclick="setType('Audio')">Audio</button>
            </div>
            <select id="format-select" onchange="saveConfig()"></select>
            <div class="row" style="margin-top:6px;">
                <span style="font-size:12px; color:var(--muted); white-space:nowrap;">Limită viteză:</span>
                <input type="text" id="speed-input" placeholder="2M / 500K / gol = nelimitat" oninput="saveConfig()">
            </div>
        </div>

        <div class="card">
            <div class="card-title">Opțiuni</div>
            <div class="checkbox-group">
                <label class="checkbox-item"><input type="checkbox" id="chk-playlist" onchange="saveConfig()"> Playlist complet</label>
                <label class="checkbox-item"><input type="checkbox" id="chk-subs" onchange="saveConfig()"> Subtitrări (RO / EN)</label>
                <label class="checkbox-item"><input type="checkbox" id="chk-thumb" onchange="saveConfig()" checked> Embed thumbnail</label>
            </div>
            <div class="row" style="margin-top:6px;">
                <span style="font-size:12px; color:var(--muted);">Cookies:</span>
                <select id="cookies-select" onchange="saveConfig()">
                    <option value="Niciunul">Niciunul</option>
                    <option value="chrome">Chrome</option>
                    <option value="firefox">Firefox</option>
                    <option value="edge">Edge</option>
                    <option value="brave">Brave</option>
                    <option value="opera">Opera</option>
                    <option value="vivaldi">Vivaldi</option>
                    <option value="chromium">Chromium</option>
                </select>
            </div>
        </div>
    </div>

    <!-- Folder Salvare -->
    <div class="card">
        <div class="card-title">Folder Salvare</div>
        <div class="row">
            <input type="text" id="folder-input" onchange="saveConfig()" placeholder="/cale/spre/folder">
            <button class="btn" onclick="openFolder()">Deschide</button>
        </div>
    </div>

    <!-- Progress & Action -->
    <div class="card">
        <div class="progress-header">
            <span id="status-text" style="color:var(--muted);">Gata de descărcare.</span>
            <span id="pct-text" style="font-weight:bold; color:var(--accent);">0%</span>
        </div>
        <div class="progress-bar-container">
            <div class="progress-bar" id="progress-bar"></div>
        </div>
        <div class="progress-meta">
            <span id="speed-text"></span>
            <span id="eta-text"></span>
        </div>
        <div class="action-bar" style="margin-top:10px;">
            <button class="btn btn-primary btn-large" style="flex:2;" id="btn-download" onclick="startDownload()">DESCARCĂ</button>
            <button class="btn btn-danger btn-large" style="flex:1;" id="btn-cancel" onclick="cancelDownload()">Anulează</button>
        </div>
    </div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div class="card-title">Jurnal Evenimente</div>
            <button class="btn" style="padding:4px 10px; font-size:11px;" onclick="clearLogs()">Curăță</button>
        </div>
        <div class="log-box" id="log-box"></div>
    </div>

    <!-- Footer Copyright -->
    <div style="text-align:center; padding:12px 0 20px 0; font-size:12px; color:var(--muted);">
        © 2026 David Marica - AZS Gherla
    </div>
</div>

<!-- Modal Despre -->
<div id="about-modal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.7); z-index:9999; align-items:center; justify-content:center; backdrop-filter:blur(4px);">
    <div style="background:var(--surface); border:1px solid var(--border); border-radius:14px; width:90%; max-width:650px; max-height:85vh; display:flex; flex-direction:column; overflow:hidden; box-shadow:0 10px 30px rgba(0,0,0,0.5);">
        <div style="padding:16px 20px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center;">
            <div>
                <h2 style="font-size:18px; color:var(--accent);">YT AZS — V12.0</h2>
                <div style="font-size:12px; color:var(--muted);">© 2026 David Marica - AZS Gherla</div>
            </div>
            <button class="btn" onclick="closeAboutModal()" style="font-size:16px; padding:4px 10px;">✕</button>
        </div>
        <div style="padding:16px 20px; overflow-y:auto; display:flex; flex-direction:column; gap:12px; font-size:13px;">
            <div class="card" style="margin:0;">
                <div class="card-title">Surse & Proiecte Oficiale</div>
                <div style="display:flex; flex-direction:column; gap:8px; margin-top:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span><strong>GitHub Proiect Oficial</strong></span>
                        <a href="https://github.com/davidutz24/YT-AZS" target="_blank" class="btn" style="text-decoration:none; padding:4px 8px; font-size:11px;">Deschide ↗</a>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span><strong>YT-DLP</strong> (Motor principal)</span>
                        <a href="https://github.com/yt-dlp/yt-dlp" target="_blank" class="btn" style="text-decoration:none; padding:4px 8px; font-size:11px;">Deschide ↗</a>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span><strong>NewPipe Extractor</strong> (Android InnerTube)</span>
                        <a href="https://github.com/teamnewpipe/newpipeextractor" target="_blank" class="btn" style="text-decoration:none; padding:4px 8px; font-size:11px;">Deschide ↗</a>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span><strong>Cobalt Tools Directory</strong></span>
                        <a href="https://cobalt.directory/" target="_blank" class="btn" style="text-decoration:none; padding:4px 8px; font-size:11px;">Deschide ↗</a>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span><strong>9xBuddy</strong> (Extractor universal)</span>
                        <a href="https://9xbuddy.com/" target="_blank" class="btn" style="text-decoration:none; padding:4px 8px; font-size:11px;">Deschide ↗</a>
                    </div>
                </div>
            </div>
            <div class="card" style="margin:0;">
                <div class="card-title">Descriere & Compatibilitate</div>
                <p style="color:var(--text); line-height:1.5;">
                    YT AZS V12.0 este o aplicație modernă cross-platform (Windows & Linux) pentru descărcarea de conținut video și audio la calități de la 360p până la 4K/8K, MP3 320kbps, FLAC, compatibilă ProPresenter.
                </p>
            </div>
        </div>
        <div style="padding:12px 20px; border-top:1px solid var(--border); display:flex; justify-content:flex-end;">
            <button class="btn btn-primary" onclick="closeAboutModal()">Închide</button>
        </div>
    </div>
</div>

<script>
    let currentType = 'Video';
    const VIDEO_FORMATS = JSON.parse('$$VIDEO_FORMATS$$');
    const AUDIO_FORMATS = JSON.parse('$$AUDIO_FORMATS$$');
    const ENGINE_LIST = JSON.parse('$$ENGINE_LIST$$');
    let previewDebounce = null;

    function openAboutModal() {
        document.getElementById('about-modal').style.display = 'flex';
    }

    function closeAboutModal() {
        document.getElementById('about-modal').style.display = 'none';
    }

    function init() {
        const engSelect = document.getElementById('engine-select');
        ENGINE_LIST.forEach(e => {
            const opt = document.createElement('option');
            opt.value = e;
            opt.textContent = e;
            engSelect.appendChild(opt);
        });

        loadConfig();
        populateFormats();
        setInterval(pollStatus, 400);
    }

    function populateFormats() {
        const fmtSelect = document.getElementById('format-select');
        const opts = currentType === 'Video' ? VIDEO_FORMATS : AUDIO_FORMATS;
        fmtSelect.innerHTML = '';
        opts.forEach(f => {
            const opt = document.createElement('option');
            opt.value = f;
            opt.textContent = f;
            fmtSelect.appendChild(opt);
        });
    }

    function setType(type) {
        currentType = type;
        document.getElementById('type-video').className = type === 'Video' ? 'btn btn-primary' : 'btn';
        document.getElementById('type-audio').className = type === 'Audio' ? 'btn btn-primary' : 'btn';
        populateFormats();
        saveConfig();
    }

    function toggleTheme() {
        const body = document.body;
        const current = body.getAttribute('data-theme') || 'navy';
        const next = current === 'navy' ? 'light' : 'navy';
        body.setAttribute('data-theme', next);
        document.getElementById('btn-theme').textContent = next === 'navy' ? 'Light' : 'Navy';
    }

    function loadConfig() {
        fetch('/api/config')
            .then(r => r.json())
            .then(data => {
                if (data.engine) document.getElementById('engine-select').value = data.engine;
                if (data.last_path) document.getElementById('folder-input').value = data.last_path;
                if (data.speed_limit) document.getElementById('speed-input').value = data.speed_limit;
                if (data.cookies_browser) document.getElementById('cookies-select').value = data.cookies_browser;
                if (data.playlist !== undefined) document.getElementById('chk-playlist').checked = data.playlist;
                if (data.subtitles !== undefined) document.getElementById('chk-subs').checked = data.subtitles;
                if (data.thumbnail !== undefined) document.getElementById('chk-thumb').checked = data.thumbnail;
                if (data.format) {
                    if (data.format.startsWith('Audio')) setType('Audio');
                    else setType('Video');
                    document.getElementById('format-select').value = data.format;
                }
            });
    }

    function saveConfig() {
        const payload = {
            engine: document.getElementById('engine-select').value,
            last_path: document.getElementById('folder-input').value,
            speed_limit: document.getElementById('speed-input').value,
            cookies_browser: document.getElementById('cookies-select').value,
            playlist: document.getElementById('chk-playlist').checked,
            subtitles: document.getElementById('chk-subs').checked,
            thumbnail: document.getElementById('chk-thumb').checked,
            format: document.getElementById('format-select').value,
        };
        fetch('/api/config', { method: 'POST', body: JSON.stringify(payload) });
    }

    function onUrlChange() {
        clearTimeout(previewDebounce);
        const url = document.getElementById('url-input').value.trim();
        if (!url) {
            document.getElementById('preview-title').textContent = 'Introdu un link YouTube pentru previzualizare';
            document.getElementById('preview-meta').textContent = 'Detectare automată';
            document.getElementById('preview-img').style.display = 'none';
            document.getElementById('preview-placeholder').style.display = 'flex';
            return;
        }
        previewDebounce = setTimeout(() => {
            fetch('/api/preview', { method: 'POST', body: JSON.stringify({ url }) })
                .then(r => r.json())
                .then(info => {
                    if (info.title) {
                        document.getElementById('preview-title').textContent = info.title;
                        document.getElementById('preview-meta').textContent = (info.uploader || '') + (info.duration ? ' | ' + info.duration : '');
                    }
                    if (info.thumbnail) {
                        const img = document.getElementById('preview-img');
                        img.src = info.thumbnail;
                        img.style.display = 'block';
                        document.getElementById('preview-placeholder').style.display = 'none';
                    }
                });
        }, 500);
    }

    async function pasteUrl() {
        try {
            const text = await navigator.clipboard.readText();
            document.getElementById('url-input').value = text;
            onUrlChange();
        } catch(e) {
            alert('Permite accesul la clipboard în browser sau lipește manual cu Ctrl+V.');
        }
    }

    function startDownload() {
        const url = document.getElementById('url-input').value.trim();
        if (!url) return alert('Introdu un URL valid!');
        saveConfig();
        fetch('/api/download', {
            method: 'POST',
            body: JSON.stringify({ url })
        }).then(r => r.json()).then(res => {
            if (res.error) alert(res.error);
        });
    }

    function cancelDownload() {
        fetch('/api/cancel', { method: 'POST' });
    }

    function openFolder() {
        fetch('/api/open_folder', { method: 'POST' });
    }

    let isUpdating = false;

    function clearLogs() {
        fetch('/api/clear_logs', { method: 'POST' });
    }

    function updateYtdlp() {
        isUpdating = true;
        fetch('/api/update_ytdlp', { method: 'POST' });
    }

    let lastLogCount = 0;
    function pollStatus() {
        const btnUpdate = document.getElementById('btn-update');
        if (isUpdating) {
            btnUpdate.innerHTML = '<span class="circle-spinner accent-spin"></span> Actualizare...';
            btnUpdate.style.background = "var(--surface2)";
            btnUpdate.style.color = "var(--accent)";
        } else {
            btnUpdate.textContent = "Actualizare Surse";
            btnUpdate.style.background = "";
            btnUpdate.style.color = "";
        }

        fetch('/api/status')
            .then(r => r.json())
            .then(st => {
                document.getElementById('progress-bar').style.width = (st.progress * 100) + '%';
                document.getElementById('pct-text').textContent = st.pct_text || '0%';
                document.getElementById('speed-text').textContent = st.speed_text || '';
                document.getElementById('eta-text').textContent = st.eta_text || '';
                document.getElementById('status-text').textContent = st.status_text || '';

                const btnDl = document.getElementById('btn-download');
                btnDl.disabled = st.is_downloading;
                if (st.is_downloading) {
                    const pctStr = st.pct_text && st.pct_text !== '0%' ? ` (${st.pct_text})` : '...';
                    btnDl.innerHTML = `<span class="circle-spinner"></span> SE DESCARCĂ${pctStr}`;
                    btnDl.style.background = 'var(--success)';
                    btnDl.style.color = '#fff';
                } else {
                    btnDl.textContent = 'DESCARCĂ';
                    btnDl.style.background = '';
                    btnDl.style.color = '';
                }

                if (st.status_text && st.status_text.includes('actualizat')) {
                    isUpdating = false;
                }

                const logBox = document.getElementById('log-box');
                if (st.logs && st.logs.length !== lastLogCount) {
                    lastLogCount = st.logs.length;
                    logBox.innerHTML = '';
                    st.logs.forEach(l => {
                        const d = document.createElement('div');
                        d.className = 'log-line ' + (l.color ? 'log-' + l.color : '');
                        d.textContent = l.text;
                        logBox.appendChild(d);
                    });
                    logBox.scrollTop = logBox.scrollHeight;
                }
            });
    }

    window.onload = init;
</script>
</body>
</html>
"""

class RequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _send_html(self, html, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            page = HTML_PAGE.replace('$$VIDEO_FORMATS$$', json.dumps(VIDEO_FORMATS))
            page = page.replace('$$AUDIO_FORMATS$$', json.dumps(AUDIO_FORMATS))
            page = page.replace('$$ENGINE_LIST$$', json.dumps(ENGINE_LIST))
            self._send_html(page)
        elif path == "/api/config":
            self._send_json(app_state["config"])
        elif path == "/api/status":
            with app_state["lock"]:
                self._send_json({
                    "is_downloading": app_state["is_downloading"],
                    "progress": app_state["progress"],
                    "pct_text": app_state["pct_text"],
                    "speed_text": app_state["speed_text"],
                    "eta_text": app_state["eta_text"],
                    "status_text": app_state["status_text"],
                    "status_color": app_state["status_color"],
                    "logs": list(app_state["logs"]),
                })
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
        try: data = json.loads(body)
        except Exception: data = {}

        if path == "/api/config":
            app_state["config"].update(data)
            save_current_config()
            self._send_json({"ok": True})

        elif path == "/api/preview":
            url = data.get("url", "").strip()
            res = {"title": "", "uploader": "", "duration": "", "thumbnail": ""}
            if url:
                try:
                    # Quick check for youtube ID
                    import yt_dlp
                    ydl_opts = {'quiet': True, 'skip_download': True, 'noplaylist': True}
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        res["title"] = info.get("title", "")
                        res["uploader"] = info.get("uploader", "") or info.get("channel", "")
                        res["duration"] = info.get("duration_string", "")
                        res["thumbnail"] = info.get("thumbnail", "")
                except Exception:
                    res["title"] = f"Video ({url[:30]}...)"
            self._send_json(res)

        elif path == "/api/download":
            url = data.get("url", "").strip()
            if not url:
                self._send_json({"error": "Introdu un URL valid!"}, code=400)
                return

            if app_state["is_downloading"]:
                self._send_json({"error": "O descărcare este deja în curs!"}, code=400)
                return

            app_state["is_downloading"] = True
            app_state["is_cancelled"] = False
            app_state["progress"] = 0.0
            app_state["pct_text"] = "0%"
            app_state["speed_text"] = ""
            app_state["eta_text"] = ""
            app_state["status_text"] = "Se inițiază descărcarea..."
            app_state["status_color"] = "accent"

            job = dict(app_state["config"])
            save_path = job.get("last_path", os.path.expanduser("~"))

            def _bg_download():
                engine_name = job.get("engine", ENGINE_LIST[0])
                engine = get_engine_by_name(engine_name)
                log_message(f"Pornire descărcare: {url} (Sursă: {engine_name})", "accent")

                def progress_cb(**kwargs):
                    with app_state["lock"]:
                        app_state.update(kwargs)

                def is_cancelled():
                    return app_state["is_cancelled"]

                try:
                    ok = engine.download(url, save_path, job, progress_cb, log_message, is_cancelled)
                    if ok:
                        with app_state["lock"]:
                            app_state["progress"] = 1.0
                            app_state["pct_text"] = "100%"
                            app_state["status_text"] = f"Complet! Salvat în {save_path}"
                            app_state["status_color"] = "success"
                        log_message(f"Descărcare completă! Salvat în {save_path}", "success")
                except Exception as e:
                    if app_state["is_cancelled"]:
                        with app_state["lock"]:
                            app_state["status_text"] = "Descărcare anulată."
                            app_state["status_color"] = "danger"
                        log_message("Descărcarea a fost anulată.", "danger")
                    else:
                        with app_state["lock"]:
                            app_state["status_text"] = f"Eroare: {str(e)[:70]}"
                            app_state["status_color"] = "danger"
                        log_message(f"Eroare descărcare: {e}", "danger")
                finally:
                    app_state["is_downloading"] = False

            threading.Thread(target=_bg_download, daemon=True).start()
            self._send_json({"ok": True})

        elif path == "/api/cancel":
            app_state["is_cancelled"] = True
            app_state["status_text"] = "Anulare..."
            app_state["status_color"] = "danger"
            self._send_json({"ok": True})

        elif path == "/api/open_folder":
            p = app_state["config"].get("last_path", "")
            if p and os.path.isdir(p):
                if sys.platform == "win32": os.startfile(p)
                elif sys.platform == "darwin": subprocess.Popen(["open", p])
                else: subprocess.Popen(["xdg-open", p])
            self._send_json({"ok": True})

        elif path == "/api/clear_logs":
            with app_state["lock"]:
                app_state["logs"].clear()
            self._send_json({"ok": True})

        elif path == "/api/update_ytdlp":
            def _up():
                log_message("Actualizare yt-dlp...", "warning")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp", "mutagen"],
                                   capture_output=True, check=True)
                    log_message("yt-dlp a fost actualizat cu succes!", "success")
                except Exception as e:
                    log_message(f"Actualizare eșuată: {e}", "danger")
            threading.Thread(target=_up, daemon=True).start()
            self._send_json({"ok": True})
        else:
            self.send_error(404, "Not Found")

def start_server(port=5000):
    load_saved_config()
    server_address = ('', port)
    httpd = HTTPServer(server_address, RequestHandler)
    url = f"http://localhost:{port}"
    print("==================================================")
    print(f"  YT-AZS V12.0 - Server Web pornit la: {url}")
    print("  Apasă Ctrl+C pentru a opri.")
    print("==================================================")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nOprire server.")
        httpd.server_close()

if __name__ == "__main__":
    port = 5000
    if len(sys.argv) > 1:
        try: port = int(sys.argv[1])
        except Exception: pass
    start_server(port)
