# Amazon Video Downloader (m3u8)

A simple Python tool to download videos from Amazon Live or other pages serving HLS streams (`.m3u8`).  
It supports both **CLI** and **GUI** modes, allowing you to extract the correct video stream and save it locally.

---

## Features

- Automatically fetches `.m3u8` links from a page.
- Option to select which video to download if multiple streams exist.
- Downloads video using **FFmpeg**, supporting all resolutions.
- Simple GUI using **Tkinter** with folder selection and status updates.
- CLI mode for quick downloads.

---

## Requirements

- Python 3.10+
- [Playwright](https://playwright.dev/python/)
- FFmpeg installed and added to your system PATH.

Install Python dependencies:

```bash
pip install playwright
python -m playwright install
```

---
## Usage

CLI: 

```bash
python main.py --url "PAGE_URL" --output "VIDEO_PATH.mp4"
```
Note:
The first video in the HLS playlist is probably the one you are looking for.


GUI:

```bash
python main.py --gui
```

steps:
1. Enter the page URL.
2. Choose a folder and filename.
3. Click Download and wait for completion.
4. Open folder button becomes active once the video is saved.

Note:
The GUI will automatically select the first video in the HLS playlist.

In Code:

```python
from core.extract_links import get_m3u8_links
from core.download_video import download_video
```