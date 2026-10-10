import wave, struct, math, sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# =========================
# BACKEND
# =========================

#WAV reader
def readWAV(filename):
    wav = wave.open(filename, 'r')
    n_channels, sampwidth, framerate, n_frames, _, _ = wav.getparams()
    frames = wav.readframes(n_frames)
    wav.close()
    samples = struct.unpack("%dh" % n_frames, frames)
    return samples, framerate

#DFT algorithm
def DFT(chunk, rate):
    windowSize = len(chunk)
    maxFreqBin = windowSize // 2
    magnitudes = []

    for k in range(maxFreqBin):
        real = 0
        imaginary = 0

        for s in range(windowSize):
            amp = chunk[s]
            angle = 2 * math.pi * k * s / windowSize
            real += amp * math.cos(angle)
            imaginary += amp * math.sin(angle)

        magnitude = math.sqrt(real**2 + imaginary**2)
        magnitudes.append(magnitude)

    maxMag = magnitudes[1]
    dominantBin = 1

    for i in range(2, len(magnitudes)):
        if magnitudes[i] > maxMag:
            maxMag = magnitudes[i]
            dominantBin = i

    dominantFreq = round(dominantBin * rate / windowSize)
    return dominantFreq

#db subroutine
def lookupNote(freq):
    TOLERANCE = 10
    conn = sqlite3.connect("notes.db")
    cur = conn.cursor()

    cur.execute(
        'SELECT noteName, octave, noteFreq FROM notes ORDER BY ABS(noteFreq - ?) LIMIT 1',
        (freq,)
    )

    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        if abs(freq - row[2]) > TOLERANCE:
            return "Unknown", freq
        
        return f"{row[0]}{row[1]}", f"{row[2]}"

    return "Unknown", freq

#streaming loop
def processAudio(filename):
    samples, rate = readWAV(filename)
    print(rate)
    print(samples[:10])

    windowSize = 2048
    notesDetected = []
    noteTally = {}
    matchingLog = []

    currentNote = None

    for start in range(0, len(samples), windowSize):
        chunk = samples[start:start + windowSize]

        if len(chunk) < windowSize:
            continue

        #goes through dft
        detectedFreq = DFT(chunk, rate)

        #goes through db
        note, matchedFreq = lookupNote(detectedFreq)

        matchingLog.append(f"Detected: {detectedFreq}Hz -> Match: {matchedFreq}Hz, ({note})")

        if note is None:
            continue

        #only detect when note changes
        if currentNote != note:
            if currentNote is not None:
                notesDetected.append(currentNote)

            noteTally[note] = noteTally.get(note, 0) + 1
            currentNote = note

    #save final note
    if currentNote is not None:
        notesDetected.append(currentNote)

    return notesDetected, noteTally, matchingLog


# =========================
# FRONTEND
# =========================

class MusicVisualiser:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Visualiser")

        #top frame
        top_frame = tk.Frame(root)
        top_frame.pack(pady=10)

        self.btn_load = tk.Button(
            top_frame,
            text="Load WAV and Visualise",
            command=self.load_file
        )
        self.btn_load.pack()

        #canvas
        self.canvas = tk.Canvas(root, width=800, height=300, bg="white")
        self.canvas.pack(pady=10)

        #output box
        self.output_box = tk.Text(root, height=40, width=110)
        self.output_box.pack(pady=10)

        self.notePositions = {      #posisitons of all notes on stave (height)
            "C4": 145, "C#4": 145, 
            "D4": 140, "D#4": 140,
            "E4": 135, 
            "F4": 130, "F#4": 130,
            "G4": 125, "G#4": 125,
            "A4": 120, "A#4": 120,
            "B4": 115,
            "C5": 110, "C#5": 110,
            "D5": 105, "D#5": 105,
            "E5": 100,
            "F5": 95,  "F#5": 95,
            "G5": 90,  "G#5": 90,
            "A5": 85,  "A#5": 85
        }

        self.ledgerNotes = ["C4", "C#4", "A5", "A#5"] #array of ledger notes in db

        self.sharpNotes = ["C#4", "D#4", "F#4", "G#4", "A#4", "C#5", "D#5", "F#5", "G#5", "A#5"] #array of all sharp notes

        self.draw_staff()

    def log(self, msg):
        self.output_box.insert(tk.END, msg + "\n")
        self.output_box.see(tk.END)

    def draw_staff(self):
        self.canvas.delete("all")

        start_y = 100
        spacing = 10

        for i in range(5):
            y = start_y + i * spacing
            self.canvas.create_line(50, y, 750, y, width=2)

        # treble image clef:
        try:
            img = Image.open("treble_clef.png")
            img = img.resize((30, 50))
            self.tk_img = ImageTk.PhotoImage(img)
            self.canvas.create_image(70, 120, image=self.tk_img)
        except:
            pass

    def draw_notes(self, notes):
        x = 140

        for note in notes:
            if note in self.notePositions:
                y = self.notePositions[note]

                self.canvas.create_oval(
                    x, y, x+15, y+10,
                    width=2, outline="black"
                )

                if note in self.ledgerNotes:
                    self.canvas.create_line(x-5, y+5, x+20, y+5, width=2)
                
                if note in self.sharpNotes:
                    self.canvas.create_text(x-10, y+5, text="♯", font=("Arial", 14))

                x += 40
                if x > 730:
                    break

    def load_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("All files", "*.*")]
        )

        if file_path:
            if not file_path.lower().endswith(".wav"):
                messagebox.showerror("Error", "Please select a valid .wav file.")
                return

            self.draw_staff()

            # show processing
            self.output_box.delete("1.0", tk.END)
            self.output_box.insert(tk.END, "Processing... please wait.\n")
            self.root.update()

            try:
                notesDetected, noteTally, matchingLog = processAudio(file_path)

                # results
                self.output_box.delete("1.0", tk.END)
                self.log("DONE!")

                self.log("\n--- Matching Log ---")
                for entry in matchingLog:
                    self.log(entry)

                self.log("\n--- Notes Detected ---")
                self.log(str(notesDetected))

                self.log("\n--- Note Tally ---")
                for note, count in noteTally.items():
                    self.log(f"{note}: {count}")

                # draw notes
                if notesDetected:
                    self.draw_notes(notesDetected)
                else:
                    messagebox.showinfo("Result", "No notes detected.")

            except FileNotFoundError:
                messagebox.showerror("Error", "The file 'notes.db' is missing. Please run the setup first.")
        
            except wave.Error:
                messagebox.showerror("Error", "Invalid WAV file. Please ensure it is a standard 16-bit PCM WAV.")
                
            except struct.error:
                messagebox.showerror("Error", "Audio data is corrupted or in an unsupported format.")

            except Exception as e:
                # The catch-all for anything else (like math overflows or UI issues)
                messagebox.showerror("Unexpected Error", f"An error occurred: {str(e)}")


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicVisualiser(root)
    root.mainloop()