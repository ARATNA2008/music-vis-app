# Music Visualiser

A small Python desktop application that estimates musical notes in WAV audio and displays the detected sequence on a treble staff.

## Requirements

- Python 3
- Tkinter, included with most Python installations
- Pillow, for loading the treble-clef image

## Setup and Run

From the repository directory, create and activate a virtual environment, install Pillow, and start the app:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install Pillow
python app.py
```

On macOS or Linux, use `python3` to create the environment and activate it with `source .venv/bin/activate`. Some Linux distributions package Tkinter separately.

Keep `notes.db` and `treble_clef.png` in the repository directory when running the app. Use **Load WAV and Visualise** to select an audio file.

## Audio Input

The current WAV reader expects mono, 16-bit PCM audio. The app divides audio into 2048-sample windows, estimates one dominant frequency per window, and matches it against the notes stored in `notes.db`. Processing is performed in the GUI thread, so longer recordings may take time to process.

The included WAV files are sample inputs. `mysql.sql` is a commented legacy schema/data example; the application uses the bundled SQLite database instead.
