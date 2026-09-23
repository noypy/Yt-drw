import os
import threading
import yt_dlp
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.properties import StringProperty, NumericProperty

# Android storage සහ permissions
try:
    from android.storage import app_storage_path
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.INTERNET,
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.READ_EXTERNAL_STORAGE
    ])
    DOWNLOAD_DIR = os.path.join(app_storage_path(), 'Downloads')
except ImportError:
    DOWNLOAD_DIR = os.path.join(os.path.expanduser('~'), 'Downloads')

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class DownloaderUI(BoxLayout):
    status_text = StringProperty('Ready')
    progress_value = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10

        self.add_widget(Label(
            text='YouTube Downloader',
            font_size='24sp',
            size_hint_y=None,
            height=50
        ))

        self.url_input = TextInput(
            hint_text='Paste YouTube URL here',
            multiline=False,
            size_hint_y=None,
            height=50
        )
        self.add_widget(self.url_input)

        self.download_btn = Button(
            text='Download',
            size_hint_y=None,
            height=50
        )
        self.download_btn.bind(on_press=self.start_download)
        self.add_widget(self.download_btn)

        self.progress_bar = ProgressBar(max=100)
        self.add_widget(self.progress_bar)

        self.status_label = Label(
            text=self.status_text,
            size_hint_y=None,
            height=40
        )
        self.add_widget(self.status_label)

        self.add_widget(Label(
            text=f'Save to: {DOWNLOAD_DIR}',
            font_size='12sp',
            size_hint_y=None,
            height=30
        ))

    def update_status(self, text):
        self.status_text = text
        self.status_label.text = text

    def update_progress(self, value):
        self.progress_value = value
        self.progress_bar.value = value

    def start_download(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.update_status('Please enter a URL')
            return
        self.download_btn.disabled = True
        self.update_status('Starting download...')
        threading.Thread(target=self.download_video, args=(url,), daemon=True).start()

    def download_video(self, url):
        def progress_hook(d):
            if d['status'] == 'downloading':
                percent_str = d.get('_percent_str', '0%').strip().replace('%', '')
                try:
                    percent = float(percent_str)
                except ValueError:
                    percent = 0
                Clock.schedule_once(lambda dt: self.update_progress(percent))
                Clock.schedule_once(lambda dt: self.update_status(f'Downloading... {percent:.1f}%'))
            elif d['status'] == 'finished':
                Clock.schedule_once(lambda dt: self.update_progress(100))
                Clock.schedule_once(lambda dt: self.update_status('Download finished!'))

        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'format': 'best[ext=mp4]/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [progress_hook],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            Clock.schedule_once(lambda dt: self.update_status('Download complete! Check Downloads folder.'))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_status(f'Error: {str(e)}'))
        finally:
            Clock.schedule_once(lambda dt: setattr(self.download_btn, 'disabled', False))


class YouTubeDownloaderApp(App):
    def build(self):
        return DownloaderUI()


if __name__ == '__main__':
    YouTubeDownloaderApp().run()
