#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YT-AZS V12.0 - Multi-Source Download Engines
Ordered sources:
  1. Auto (Fallback inteligent pe toate sursele)
  2. YT-DLP (Standard / Calitate Maximă)
  3. YT-DL (Classic / youtube-dl)
  4. NewPipe Extractor (Android InnerTube)
  5. 9xBuddy (Universal Extractor)
  6. Cobalt Tools (API & Redirecționare cobalt.directory)
"""

import os
import sys
import time
import json
import re
import subprocess
import webbrowser
from urllib.request import Request, urlopen
import yt_dlp

# Detect FFmpeg
FFMPEG_PATH = None
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    pass

if not FFMPEG_PATH or not os.path.exists(FFMPEG_PATH):
    import shutil
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg and os.path.exists(sys_ffmpeg):
        FFMPEG_PATH = sys_ffmpeg

CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

ENGINE_LIST = [
    "Auto (Fallback inteligent pe toate sursele)",
    "YT-DLP (Standard / Calitate Maxima)",
    "YT-DL (Classic / youtube-dl)",
    "NewPipe Extractor (Android InnerTube)",
    "9xBuddy (Universal Extractor)",
    "Cobalt Tools (API / cobalt.directory)",
]

DEFAULT_COBALT_INSTANCES = [
    "https://api.cobalt.rpkiinval.id",
    "https://lime.clxxped.lol",
    "https://cobaltapi.kittycat.boo",
    "https://kitty.tame.gg",
    "https://cobalt-api.lamps-dev.dev",
    "https://cobaltapi.squair.xyz",
    "https://fox.kittycat.boo",
    "https://api-cobalt.eversiege.network",
    "https://bergung-api.hoffnungfuerdiezukunft.net",
]


def clean_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def format_bytes(size: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def format_seconds(seconds: float) -> str:
    try:
        sec = int(seconds)
        if sec < 0:
            return "--:--"
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
    except Exception:
        return "--:--"


def sanitize_filename(name: str) -> str:
    name = re.sub(r"[\\/*?:\"<>|]", "", name)
    name = name.strip().strip(". ")
    return name or "download"


class BaseEngine:
    def __init__(self, name: str):
        self.name = name

    def download(self, url: str, save_path: str, job: dict,
                 progress_cb, log_cb, is_cancelled_fn) -> bool:
        raise NotImplementedError


class YtDlpEngine(BaseEngine):
    def __init__(self, name="YT-DLP Standard", player_clients=None, extra_args=None):
        super().__init__(name)
        self.player_clients = player_clients
        self.extra_args = extra_args or {}

    def _expected_ext(self, sel: str) -> str:
        if "Audio" in sel:
            if "MP3" in sel: return "mp3"
            elif "M4A" in sel: return "m4a"
            elif "FLAC" in sel: return "flac"
            elif "OPUS" in sel: return "opus"
            elif "OGG" in sel: return "ogg"
            return "wav"
        if "MP4" in sel: return "mp4"
        if "WEBM" in sel: return "webm"
        return "mkv"

    def _parse_speed(self, s: str):
        if not s: return None
        s = s.strip().upper()
        try:
            if s.endswith("M"): return int(float(s[:-1]) * 1024 * 1024)
            elif s.endswith("K"): return int(float(s[:-1]) * 1024)
            return int(s)
        except Exception:
            return None

    def download(self, url: str, save_path: str, job: dict,
                 progress_cb, log_cb, is_cancelled_fn) -> bool:
        sel = job.get("format", "Video - MP4 (1080p H.264+AAC)")
        do_thumb = job.get("thumbnail", True)
        playlist_enabled = job.get("playlist", False)
        speed_raw = job.get("speed_limit", "")
        browser = job.get("cookies_browser", "Niciunul")

        dl_state = {
            "phase": 0,
            "phase_count": 1 if "Audio" in sel else 2,
            "last_filename": "",
            "playlist_pos": None,
            "playlist_total": None,
        }

        def hook(d):
            if is_cancelled_fn():
                raise Exception("Anulat de utilizator.")

            fname = d.get("filename", "") or ""
            playlist_idx = d.get("playlist_index")
            playlist_count = d.get("playlist_count")
            try:
                dl_state["playlist_pos"] = int(playlist_idx) if playlist_idx is not None else None
            except Exception:
                pass
            try:
                dl_state["playlist_total"] = int(playlist_count) if playlist_count is not None else None
            except Exception:
                pass

            if d.get("status") == "downloading":
                if fname and fname != dl_state["last_filename"]:
                    dl_state["last_filename"] = fname
                    dl_state["phase"] += 1
                    phase = dl_state["phase"]
                    n_phases = dl_state["phase_count"]
                    base = os.path.basename(fname).lower()
                    if any(x in base for x in [".f140.", ".f251.", ".m4a.", "audio"]):
                        s_label = "Audio"
                    elif any(x in base for x in [".f137.", ".f248.", ".f299.", "video"]):
                        s_label = "Video"
                    else:
                        s_label = f"Stream {phase}"
                    log_cb(f"[{self.name}] Descarcare {s_label} ({phase}/{n_phases})...", "accent")
                    progress_cb(progress=0.0)

                p_str = clean_ansi(d.get("_percent_str", "0%")).replace("%", "").strip()
                speed = clean_ansi(d.get("_speed_str", "")).strip()
                eta = clean_ansi(d.get("_eta_str", "")).strip()
                raw_total = clean_ansi(d.get("_total_bytes_str", d.get("_total_bytes_estimate_str", ""))).strip()
                total = "" if not raw_total or raw_total.upper() == "N/A" else raw_total

                try:
                    pct = float(p_str) / 100.0
                    phase = dl_state["phase"]
                    n_phases = max(dl_state["phase_count"], 1)

                    if playlist_enabled and dl_state["playlist_pos"] and dl_state["playlist_total"]:
                        item_progress = ((max(phase, 1) - 1) + pct) / n_phases
                        combined = ((dl_state["playlist_pos"] - 1) + item_progress) / dl_state["playlist_total"]
                    elif n_phases > 1 and phase > 0:
                        combined = ((phase - 1) + pct) / n_phases
                    else:
                        combined = pct

                    combined = max(0.0, min(combined, 1.0))
                    phase_pct = int(combined * 100)
                    size_part = f" din {total}" if total else ""

                    if playlist_enabled and dl_state["playlist_pos"]:
                        txt = f"Playlist {dl_state["playlist_pos"]}/{dl_state["playlist_total"] or "?"} | {p_str}%{size_part}"
                    elif n_phases > 1:
                        txt = f"Stream {phase}/{n_phases}: {p_str}%{size_part}"
                    else:
                        txt = f"Se descarca: {p_str}%{size_part}"

                    progress_cb(
                        progress=combined,
                        pct_text=f"{phase_pct}%",
                        speed_text=f"Viteza: {speed}" if speed else "",
                        eta_text=f"ETA: {eta}" if eta else "",
                        status_text=txt,
                        status_color="warning"
                    )
                except Exception:
                    pass

            elif d.get("status") == "finished":
                fn = os.path.basename(fname)
                log_cb(f"[{self.name}] Stream finalizat: {fn}", "success")

        ydl_opts = {
            "outtmpl": os.path.join(save_path, "%(title)s.%(ext)s"),
            "progress_hooks": [hook],
            "noplaylist": not playlist_enabled,
            "postprocessors": [{"key": "FFmpegMetadata"}],
            "quiet": True,
            "no_warnings": True,
            "concurrent_fragment_downloads": 8,
            "buffersize": 1024 * 64,
            "http_chunk_size": 1024 * 1024 * 10,
            "socket_timeout": 30,
            "extractor_retries": 5,
            "retries": 10,
            "fragment_retries": 10,
            "continuedl": True,
        }

        if FFMPEG_PATH:
            ydl_opts["ffmpeg_location"] = FFMPEG_PATH

        if speed_raw:
            sp = self._parse_speed(speed_raw)
            if sp:
                ydl_opts["ratelimit"] = sp

        if browser and browser != "Niciunul":
            ydl_opts["cookiesfrombrowser"] = (browser, None, None, None)

        if job.get("subtitles"):
            ydl_opts.update({
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["ro", "en"],
                "embedsubtitles": True,
            })

        if self.player_clients:
            ydl_opts.setdefault("extractor_args", {}).setdefault("youtube", {})["player_client"] = self.player_clients

        if self.extra_args:
            for k, v in self.extra_args.items():
                ydl_opts[k] = v

        def thumb_postproc():
            return [
                {"key": "FFmpegThumbnailsConvertor", "format": "jpg"},
                {"key": "EmbedThumbnail"},
            ]

        if "Audio" in sel:
            if "MP3" in sel: ext, q = "mp3", "320"
            elif "M4A" in sel: ext, q = "m4a", "192"
            elif "FLAC" in sel: ext, q = "flac", "0"
            elif "OPUS" in sel: ext, q = "opus", "0"
            elif "OGG" in sel: ext, q = "vorbis", "0"
            else: ext, q = "wav", "0"

            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": ext, "preferredquality": q},
                {"key": "FFmpegMetadata"},
            ]
            if do_thumb:
                ydl_opts["writethumbnail"] = True
                ydl_opts["postprocessors"] += thumb_postproc()
        else:
            ext = "mp4" if "MP4" in sel else ("webm" if "WEBM" in sel else "mkv")

            def H264_FMT(h=None):
                hf = f"[height<={h}]" if h else ""
                return (
                    f"bestvideo{hf}[vcodec^=avc1][ext=mp4]+bestaudio[acodec^=mp4a][ext=m4a]"
                    f"/bestvideo{hf}[ext=mp4]+bestaudio[ext=m4a]"
                    f"/bestvideo{hf}+bestaudio/best"
                )

            if "ProPresenter" in sel or "1080p" in sel: fmt = H264_FMT(1080)
            elif "720p" in sel: fmt = H264_FMT(720)
            elif "480p" in sel: fmt = H264_FMT(480)
            elif "360p" in sel: fmt = H264_FMT(360)
            else: fmt = "bestvideo+bestaudio/best"

            ydl_opts["format"] = fmt
            ydl_opts["merge_output_format"] = ext

            if do_thumb:
                ydl_opts["writethumbnail"] = True
                ydl_opts["postprocessors"] += thumb_postproc()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True


class CobaltEngine(BaseEngine):
    def __init__(self, name="Cobalt Tools"):
        super().__init__(name)
        self.cached_instances = []
        self.last_fetch_time = 0

    def _get_instances(self) -> list:
        now = time.time()
        if self.cached_instances and (now - self.last_fetch_time < 3600):
            return self.cached_instances

        instances = list(DEFAULT_COBALT_INSTANCES)
        try:
            req = Request("https://cobalt.directory/api/working?type=api",
                          headers={"User-Agent": "Mozilla/5.0 (YT-AZS V12)"})
            with urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                yt_insts = data.get("data", {}).get("youtube", [])
                if yt_insts:
                    instances = yt_insts + [i for i in instances if i not in yt_insts]
        except Exception:
            pass

        self.cached_instances = instances
        self.last_fetch_time = now
        return instances

    def _http_chunk_download(self, stream_url: str, output_path: str, progress_cb, log_cb, is_cancelled_fn) -> bool:
        req = Request(stream_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; YT-AZS V12)",
            "Accept": "*/*",
        })
        with urlopen(req, timeout=20) as resp:
            total_size = int(resp.headers.get("Content-Length", 0))
            chunk_size = 1024 * 64
            downloaded = 0
            start_time = time.time()
            last_update = start_time

            temp_path = output_path + ".part"
            with open(temp_path, "wb") as f:
                while True:
                    if is_cancelled_fn():
                        f.close()
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        raise Exception("Anulat de utilizator.")

                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    now = time.time()
                    if now - last_update >= 0.1:
                        last_update = now
                        elapsed = max(now - start_time, 0.001)
                        speed = downloaded / elapsed
                        speed_str = f"{format_bytes(speed)}/s"

                        if total_size > 0:
                            pct = min(downloaded / total_size, 1.0)
                            rem_bytes = total_size - downloaded
                            eta_sec = rem_bytes / speed if speed > 0 else 0
                            eta_str = f"ETA: {format_seconds(eta_sec)}"
                            txt = f"Cobalt direct stream: {int(pct * 100)}% ({format_bytes(downloaded)} / {format_bytes(total_size)})"
                        else:
                            pct = 0.5
                            eta_str = ""
                            txt = f"Cobalt direct stream: {format_bytes(downloaded)}"

                        progress_cb(
                            progress=pct,
                            pct_text=f"{int(pct * 100)}%" if total_size > 0 else "...",
                            speed_text=f"Viteza: {speed_str}",
                            eta_text=eta_str,
                            status_text=txt,
                            status_color="warning"
                        )

            if os.path.exists(output_path):
                try: os.remove(output_path)
                except Exception: pass
            os.rename(temp_path, output_path)
            return True

    def download(self, url: str, save_path: str, job: dict,
                 progress_cb, log_cb, is_cancelled_fn) -> bool:
        sel = job.get("format", "Video - MP4 (1080p H.264+AAC)")
        is_audio = "Audio" in sel

        instances = self._get_instances()
        log_cb(f"[{self.name}] Incercare descarcare stream API Cobalt ({len(instances)} instante)...", "accent")

        quality = "1080"
        if "720p" in sel: quality = "720"
        elif "480p" in sel: quality = "480"
        elif "360p" in sel: quality = "360"
        elif "4K" in sel or "Maxim" in sel: quality = "max"

        audio_format = "mp3"
        if "M4A" in sel: audio_format = "m4a"
        elif "FLAC" in sel: audio_format = "flac"
        elif "OGG" in sel: audio_format = "ogg"
        elif "WAV" in sel: audio_format = "wav"
        elif "OPUS" in sel: audio_format = "opus"

        # Both v10 and v7 compatibility payload
        payload = {
            "url": url,
            "videoQuality": quality,
            "vQuality": quality,
            "downloadMode": "audio" if is_audio else "auto",
            "isAudioOnly": is_audio,
            "audioFormat": audio_format,
            "aFormat": audio_format,
            "filenameStyle": "basic",
        }
        body_bytes = json.dumps(payload).encode("utf-8")

        stream_url = None
        target_filename = "download"

        for inst in instances:
            if is_cancelled_fn():
                raise Exception("Anulat de utilizator.")
            endpoint = inst if inst.endswith("/") else inst + "/"
            try:
                log_cb(f"[{self.name}] Interogare instanta: {inst}", "muted")
                req = Request(
                    endpoint,
                    data=body_bytes,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                )
                with urlopen(req, timeout=4.5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    status = data.get("status")
                    if status in ("tunnel", "redirect", "stream", "picker"):
                        stream_url = data.get("url")
                        target_filename = data.get("filename") or "download"
                        log_cb(f"[{self.name}] Stream obtinut cu succes de pe {inst}!", "success")
                        break
            except Exception:
                continue

        if stream_url:
            ext = "mp3" if is_audio else "mp4"
            clean_title = sanitize_filename(os.path.splitext(target_filename)[0])
            final_filename = f"{clean_title}.{ext}"
            final_path = os.path.join(save_path, final_filename)
            log_cb(f"[{self.name}] Descarcare directa fisier: {final_filename}", "accent")
            self._http_chunk_download(stream_url, final_path, progress_cb, log_cb, is_cancelled_fn)
            return True

        # Fallback: Open cobalt.directory in the browser
        log_cb("[Cobalt Tools] Instantele API publice necesita verificare JWT in browser.", "warning")
        log_cb("[Cobalt Tools] Redirectionare: Se deschide https://cobalt.directory/ in browser...", "accent")

        try:
            webbrowser.open("https://cobalt.directory/")
        except Exception:
            pass

        progress_cb(
            progress=1.0,
            pct_text="Deschis",
            status_text="Cobalt deschis in browser (cobalt.directory)!",
            status_color="success"
        )
        return True


class AutoFallbackEngine(BaseEngine):
    def __init__(self, name="Auto Fallback"):
        super().__init__(name)
        self.engines = [
            ("YT-DLP Standard", YtDlpEngine("YT-DLP Standard")),
            ("YT-DL Classic", YtDlpEngine("YT-DL Classic", player_clients=["web", "mweb", "android"], extra_args={"compat_opts": ["no-youtube-prefer-utc-upload-date"]})),
            ("NewPipe Extractor", YtDlpEngine("NewPipe Extractor", player_clients=["android", "android_creator", "web"])),
            ("9xBuddy Universal", YtDlpEngine("9xBuddy Universal", extra_args={"extractor_retries": 5, "socket_timeout": 20})),
            ("Cobalt Tools", CobaltEngine("Cobalt Tools")),
        ]

    def download(self, url: str, save_path: str, job: dict,
                 progress_cb, log_cb, is_cancelled_fn) -> bool:
        errors = []
        for engine_name, engine in self.engines:
            if is_cancelled_fn():
                raise Exception("Anulat de utilizator.")
            try:
                log_cb(f"[Auto Fallback] Incercare descarcare cu motorul: {engine_name}...", "accent")
                res = engine.download(url, save_path, job, progress_cb, log_cb, is_cancelled_fn)
                if res:
                    log_cb(f"[Auto Fallback] Actiune finalizata cu succes folosind: {engine_name}!", "success")
                    return True
            except Exception as ex:
                if is_cancelled_fn():
                    raise
                err_msg = str(ex).strip()
                errors.append(f"{engine_name}: {err_msg[:80]}")
                log_cb(f"[Auto Fallback] {engine_name} a esuat ({err_msg[:75]}). Se trece la urmatorul motor...", "warning")

        raise Exception("Toate sursele disponibile au esuat. Detalii erori:\n" + "\n".join(errors))


def get_engine_by_name(engine_name: str) -> BaseEngine:
    if "Auto" in engine_name:
        return AutoFallbackEngine()
    elif "NewPipe" in engine_name:
        return YtDlpEngine("NewPipe Extractor", player_clients=["android", "android_creator", "web"])
    elif "YT-DL (" in engine_name or "Classic" in engine_name:
        return YtDlpEngine("YT-DL Classic", player_clients=["web", "mweb", "android"], extra_args={"compat_opts": ["no-youtube-prefer-utc-upload-date"]})
    elif "9xBuddy" in engine_name or "Universal" in engine_name:
        return YtDlpEngine("9xBuddy Universal", extra_args={"extractor_retries": 5, "socket_timeout": 20})
    elif "Cobalt" in engine_name:
        return CobaltEngine("Cobalt Tools")
    else:
        return YtDlpEngine("YT-DLP Standard")
