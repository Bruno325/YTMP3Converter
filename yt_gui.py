import os
import subprocess
import threading
import time
import sys
import tempfile
import shutil
import tkinter as tk
from tkinter import filedialog

def log(msg):
    output_box.insert(tk.END, msg + "\n")
    output_box.see(tk.END)

def find_latest_audio_file(folder):
    time.sleep(1)
    audio_extensions = [".mp3"]
    files = [os.path.join(folder, f) for f in os.listdir(folder)
             if os.path.splitext(f)[1].lower() in audio_extensions]
    return max(files, key=os.path.getctime) if files else None

def get_silent_run_args():
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return {"startupinfo": si}
    return {}

def download_youtube_as_mp3(url, output_folder):
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        log("📥 Downloading and converting to MP3...")
        output_template = os.path.join(output_folder, "%(title)s.%(ext)s")

        # Locate yt-dlp and ffmpeg in the same directory as the EXE
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
        else:
            exe_dir = os.path.dirname(__file__)

        yt_dlp_path = os.path.join(exe_dir, "yt-dlp.exe")
        ffmpeg_path = os.path.join(exe_dir, "ffmpeg.exe")

        # Ensure yt-dlp exists
        if not os.path.exists(yt_dlp_path):
            raise FileNotFoundError(f"yt-dlp.exe not found in {exe_dir}")

        # Add ffmpeg location to PATH so yt-dlp can find it
        os.environ["PATH"] += os.pathsep + exe_dir

        result = subprocess.run([
            yt_dlp_path,
            "--no-playlist",
            "-f", "bestaudio",
            "-o", output_template,
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            url
        ], capture_output=True, text=True, **get_silent_run_args())

        if result.stdout:
            log(result.stdout)
        if result.stderr:
            log(result.stderr)

        if result.returncode != 0:
            raise RuntimeError("yt-dlp failed to download or convert the audio.")

        mp3_file = find_latest_audio_file(output_folder)
        if not mp3_file:
            raise FileNotFoundError("MP3 file not found after download.")

        log(f"✅ MP3 saved to: {mp3_file}")

    except Exception as e:
        log(f"❌ Error: {e}")

def start_download():
    url = url_entry_var.get().strip()
    folder = folder_var.get().strip()
    if not url:
        log("⚠️ Please enter a YouTube video URL.")
        return
    threading.Thread(target=download_youtube_as_mp3, args=(url, folder)).start()

def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)

# --- GUI Setup ---
root = tk.Tk()
root.title("YouTube to MP3 Converter")

# --- Determine base path depending on runtime ---
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

# --- Safe icon handling for PyInstaller ---
try:
    icon_source = os.path.join(base_path, "icon.ico")

    if getattr(sys, 'frozen', False):
        temp_icon = os.path.join(tempfile.gettempdir(), "ytmp3_icon.ico")
        if not os.path.exists(temp_icon):
            shutil.copyfile(icon_source, temp_icon)
        root.iconbitmap(temp_icon)
    else:
        root.iconbitmap(icon_source)
except Exception as e:
    print(f"⚠️ Could not load icon: {e}")

# --- Set window size and center it ---
window_width = 1000
window_height = 562

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x = int((screen_width / 2) - (window_width / 2))
y = int((screen_height / 2) - (window_height / 2))
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

# --- YouTube URL ---
tk.Label(root, text="🎵 YouTube URL:").pack(anchor="w", padx=10, pady=(10, 0))
url_frame = tk.Frame(root)
url_frame.pack(fill="x", padx=10, pady=(0, 10))

url_entry_var = tk.StringVar()
url_entry = tk.Entry(url_frame, textvariable=url_entry_var)
url_entry.pack(fill="x", expand=True)

# --- Output Folder ---
tk.Label(root, text="📁 Output Folder:").pack(anchor="w", padx=10, pady=(0, 0))
output_path_frame = tk.Frame(root)
output_path_frame.pack(fill="x", padx=10, pady=(0, 10))

folder_var = tk.StringVar(value=os.path.expanduser("~\\Music\\yt_mp3s"))
folder_entry = tk.Entry(output_path_frame, textvariable=folder_var)
folder_entry.pack(side="left", fill="x", expand=True)

browse_button = tk.Button(output_path_frame, text="Browse", command=browse_folder)
browse_button.pack(side="left", padx=(10, 0))

# --- Download Button ---
download_button = tk.Button(root, text="Download MP3", command=start_download, bg="green", fg="white", height=2)
download_button.pack(pady=(0, 10), padx=10, fill="x")

# --- Output Log ---
output_box = tk.Text(root, height=12)
output_box.pack(padx=10, pady=(0, 10), fill="both", expand=True)

root.mainloop()