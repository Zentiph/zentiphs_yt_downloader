"""
Welcome to the YouTube Downloader!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This code kinda sucks balls, but it works and that's what matters.
The interesting video scraping stuff start at line 157.
Feel free to use this to download videos, and build off it yourself or study and learn from it.

This code is written by Gavin Borne and is licensed under the MIT License.
"""

# imports

import os
import pytube
import subprocess
import sys
import threading

import tkinter as tk
from tkinter import filedialog, messagebox, PhotoImage, scrolledtext, simpledialog

from re import sub
from typing import Union


def resource_path(rel_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, rel_path)


dirs_data = resource_path("vd_data/dirs.txt")

if not os.path.exists(dirs_data):
    os.makedirs(dirs_data)

font_setup = ("Fixedsys", 16)


class YouTubeDownloader(tk.Tk):
    """App class.
    """

    def __init__(self) -> None:
        """App constructor.
        """

        super().__init__()
        self.title("Zentiph's YT Downloader")
        self.geometry("680x680")
        self.resizable(False, False)

        # logo (top)
        self.logo_img = PhotoImage(file=resource_path("vd_data/zytd_logo.png"))
        self.logo_label = tk.Label(self, image=self.logo_img)
        self.logo_label.grid(row=0, column=0, columnspan=2,
                             sticky="ns", padx=10, pady=10)

        # download + settings (middle left)
        self.download_frame = tk.Frame(self)
        self.download_frame.grid(row=1, column=0, columnspan=1,
                                 sticky="nsw", padx=10, pady=10)

        self.set_audio_dir_button = tk.Button(
            self.download_frame, text="Set audio folder", font=font_setup, command=self.set_audio_dir)
        self.set_video_dir_button = tk.Button(
            self.download_frame, text="Set video folder", font=font_setup, command=self.set_video_dir)
        self.set_audio_dir_button.pack(pady=20)
        self.set_video_dir_button.pack(pady=20)

        self.download_button = tk.Button(
            self.download_frame, width=15, text="Download", font=font_setup, bg="light green", command=self.start_download)
        self.download_button.pack(pady=10)

        # inputs (middle right)
        self.input_frame = tk.Frame(self)
        self.input_frame.grid(row=1, column=1, columnspan=1,
                              sticky="ne", padx=10, pady=10)

        self.url_label = tk.Label(
            self.input_frame, text="Enter YouTube URL:", font=font_setup)
        self.url_label.pack(fill='x', pady=10)

        self.url_entry = tk.Entry(self.input_frame, width=60)
        self.url_entry.pack(pady=10)

        self.filename_label = tk.Label(
            self.input_frame, text="Enter filename (optional):", font=font_setup)
        self.filename_label.pack(fill='x', pady=10)

        self.filename_entry = tk.Entry(self.input_frame, width=60)
        self.filename_entry.pack(pady=10)

        self.download_type = tk.StringVar(value="mp4")
        self.radio_video = tk.Radiobutton(
            self.input_frame, text="Video (.mp4)", font=font_setup, variable=self.download_type, value="mp4")
        self.radio_audio = tk.Radiobutton(
            self.input_frame, text="Audio (.mp3)", font=font_setup, variable=self.download_type, value="mp3")
        self.radio_video.pack(fill='x')
        self.radio_audio.pack(fill='x', pady=10)

        # logs (bottom)
        self.log_frame = tk.Frame(self)
        self.log_frame.grid(row=2, column=0, columnspan=2,
                            sticky="s", padx=10, pady=10)

        self.status = tk.Label(self.log_frame, text="Status: Idle",
                               font=("fixedsys", 10), fg="gray")
        self.status.pack(fill='x')

        self.logs = scrolledtext.ScrolledText(
            self.log_frame, height=15, width=80)
        self.logs.pack(anchor='w')

        self.download_dirs = {
            'video': None,
            'audio': None
        }

        # update download dirs with previously selected dirs
        with open(dirs_data, 'r') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                type_, path = line.split(": ")
                path = None if path == 'None' else path
                self.download_dirs[type_] = path

    @staticmethod
    def _update_dirs(dirs) -> None:
        """Updates the download directories in the data directory.

        :param dirs: The directories to update.
        :type dirs: dict
        """

        with open(dirs_data, "w") as file:
            for type_, path in dirs.items():
                file.write(f"{type_}: {path}\n")

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Removes any unsupported characters from the filename.

        :param filename: The filename to sanitize.
        :type filename: str
        :return: The sanitized filename.
        :rtype: str
        """

        return sub(r'[\\/*?:"<>|]', '', filename)

    # downloading funcs

    def _download_audio(self) -> None:
        """Downloads the audio of a video. Prompts the user for a URL and file name.
        """

        if self.download_dirs['audio'] is None:
            self.set_audio_dir()

        url = self.url_entry.get()
        filename = self.filename_entry.get()

        self.after(0, self.update_status,
                   "Status: Downloading (may take a minute)", "blue")

        video = pytube.YouTube(url)
        stream = video.streams.get_audio_only()

        if filename is None or filename.strip() == '':
            self.after(0, self.append_log,
                       "No file name was provided. A default name will be used.")
            filename = self._sanitize_filename(f"{video.title[:12]}")
            if filename.strip() == '':
                filename = "audio"

        download_dir = self.download_dirs['audio']
        if not os.path.exists(download_dir):
            raise FileNotFoundError(f"{download_dir} does not exist.")

        webm_file_path = os.path.join(download_dir, filename + ".webm")
        stream.download(output_path=download_dir, filename=filename + ".webm")

        self.after(0, self.update_status, "Status: Converting", "purple")
        self.after(0, self.append_log, "Attempting to convert to MP3...")

        mp3_file_path = os.path.join(download_dir, filename + ".mp3")

        try:
            cmd = [
                "ffmpeg",
                "-i",
                webm_file_path,
                "-codec:a",
                "libmp3lame",
                "-qscale:a",
                "2",
                mp3_file_path
            ]

            subprocess.run(cmd)

        except FileNotFoundError:
            self.after(0, self.update_status, "Status: Failure", "red")
            self.after(0, self.append_log,
                       "MP3 conversion unsuccessful; ffmpeg was not found. Please install ffmpeg for best results at https://ffmpeg.org/download.html")

        if os.path.exists(mp3_file_path):
            self.after(0, self.update_status, "Status: Cleaning up", "gray")
            os.remove(webm_file_path)
            self.after(0, self.update_status, "Status: Success", "green")
            self.after(0, self.append_log,
                       f"Conversion successful. Check your audio downloads folder: {self.download_dirs['audio']}")
        else:
            self.after(0, self.update_status, "Status: Failure", "red")
            self.after(0, self.append_log, "MP3 conversion unsuccessful.")

    def _download_video(self) -> None:
        """Downloads the video. Prompts the user for a URL and file name.
        """

        if self.download_dirs['video'] is None:
            self.set_video_dir()

        url = self.url_entry.get()
        filename = self.filename_entry.get()

        self.after(0, self.update_status, "Status: Fetching streams", "blue")

        video = pytube.YouTube(url)
        streams = video.streams.filter(
            progressive=True).order_by("resolution").desc()

        if len(streams) != 0:
            selected_stream = streams[0]
        else:
            self.after(0, self.update_status, "Status: Failure", "red")
            self.after(0, self.append_log,
                       "Error fetching streams: none found.")

        if filename is None or filename.strip() == '':
            self.after(0, self.append_log,
                       "No file name provided. A default name will be used.")
            filename = self._sanitize_filename(f"{video.title[:12]}")
            if filename.strip() == '':
                filename = "video"

        download_dir = self.download_dirs['video']
        if not os.path.exists(download_dir):
            raise FileNotFoundError(f"{download_dir} does not exist.")

        self.after(0, self.update_status,
                   "Status: Downloading (may take a minute)", "blue")
        self.after(0, self.append_log,
                   f"Downloading {selected_stream.title} at {selected_stream.resolution} {selected_stream.fps} fps...")

        selected_stream.download(output_path=download_dir,
                                 filename=filename + ".mp4")

        self.after(0, self.update_status, "Status: Success", "green")
        self.after(0, self.append_log,
                   f"Download successful. Check your video downloads folder: {self.download_dirs['video']}")

    def set_audio_dir(self) -> None:
        """Sets the audio download directory to the user's choice.
        """

        audio_dir = filedialog.askdirectory(
            title="Select the location to download audio files.")
        self.download_dirs['audio'] = audio_dir
        self._update_dirs(self.download_dirs)

    def set_video_dir(self) -> None:
        """Sets the video download directory to the user's choice.
        """

        video_dir = filedialog.askdirectory(
            title="Select the location to download video files.")
        self.download_dirs['video'] = video_dir
        self._update_dirs(self.download_dirs)

    def update_status(self, msg: str, color: str) -> None:
        self.status.config(text=msg, fg=color)

    def append_log(self, msg: str) -> None:
        self.logs.insert(tk.END, msg + '\n')
        self.logs.see(tk.END)

    def start_download(self) -> None:
        threading.Thread(target=self.download, daemon=True).start()

    def download(self) -> None:
        url = self.url_entry.get().strip()
        download_type = self.download_type.get()

        if not url:
            messagebox.showinfo(
                "URL required", "You must enter a URL to download.")
            return

        self.after(0, self.update_status, "Status: Initializing", "gray")

        if download_type == "mp4":
            self._download_video()
        elif download_type == "mp3":
            self._download_audio()
        else:
            raise Exception(f"Unknown download_type {download_type}.")


if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()
