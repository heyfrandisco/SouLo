from ultralytics import YOLO
import json, torch
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from midifunctions import save_midi_file, send_midi_to_ableton, adjust_chords_to_melody
import random
import argparse
from mido import MidiFile, MidiTrack, Message, MetaMessage
import tkinter as tk
from tkinter import ttk, filedialog


# --- VARIABLES ---
training_data = [
    (["tree", "river", "bird", "cat"], "serene"),
    (["bird", "cage", "chair"], "house"),
    (["car", "building", "streetlight", "traffic"], "urban"),
    (["boat", "water", "fish", "seaweed", "sea"], "marine"),
    (["lion", "zebra", "tree", "elephant", "grass"], "wildlife"),
    (["dog", "ball", "grass", "cat"], "playful"),
    (["sun", "sand", "palm", "ocean"], "beach"),
    (["snow", "mountain", "ski", "pine"], "winter"),
    (["fire", "tent", "guitar", "stars"], "campfire"),
    (["robot", "screen", "keyboard", "lights"], "futuristic"),
    (["flower", "butterfly", "bee", "sun"], "spring"),
    (["moon", "stars", "owl", "mist"], "night"),
]


mood_chords = {
    "serene": ["Cmaj7", "Gadd9", "Fmaj7", "Am7"],
    "house": ["C", "Am", "F", "G", "Dm"],
    "urban": ["D", "A", "Bm", "G", "E"],
    "wildlife": ["C", "E", "F", "G", "D"],
    "playful": ["G", "D", "Em", "C", "A"],
    "beach": ["Fmaj7", "Cadd9", "Am", "G", "D7"],
    "winter": ["Dm", "Am", "F", "C", "Em"],
    "campfire": ["C", "G", "Am", "F", "Dm7"],
    "futuristic": ["Em", "Bm", "D", "A", "F#m"],
    "spring": ["Cmaj7", "Fmaj7", "D7", "Am", "E"],
    "night": ["Am", "Em", "Dm", "F", "G"],
    "marine": ["G", "C", "Am", "F", "Em"],
}


object_notes = {
    "tree": ["G", "A", "F"],
    "river": ["F", "D", "C"],
    "bird": ["E", "G", "A"],
    "cage": ["C", "E", "G"],
    "chair": ["D", "F", "A"],
    "car": ["A", "C", "E"],
    "dog": ["B", "D", "G"],
    "lion": ["G", "C", "E"],
    "zebra": ["F", "D", "A"],
    "ball": ["C", "G", "E"],
    "cat": ["E", "F", "A"],
    "traffic": ["D", "E", "G"],
    "building": ["G", "F", "C"],
    "boat": ["G", "E", "F"],
    "water": ["F", "A", "D"],
    "fish": ["E", "G", "C"],
    "seaweed": ["D", "F", "A"],
    "sea": ["G", "F", "A"],
    "elephant": ["C", "G", "D"],
    "grass": ["F", "A", "C"],
    "sun": ["C", "E", "G"],
    "sand": ["A", "C", "D"],
    "palm": ["G", "F", "A"],
    "ocean": ["F", "D", "C"],
    "snow": ["C", "E", "F"],
    "mountain": ["D", "A", "F"],
    "ski": ["A", "C", "E"],
    "pine": ["F", "G", "D"],
    "fire": ["B", "G", "E"],
    "tent": ["D", "A", "F"],
    "guitar": ["G", "B", "D"],
    "stars": ["E", "C", "G"],
    "robot": ["C", "E", "G"],
    "screen": ["D", "G", "B"],
    "keyboard": ["G", "A", "C"],
    "lights": ["A", "E", "G"],
    "flower": ["F", "C", "A"],
    "butterfly": ["E", "G", "D"],
    "bee": ["G", "A", "B"],
    "moon": ["C", "E", "F"],
    "owl": ["B", "G", "D"],
    "mist": ["F", "E", "G"],
    "person": ["A", "D", "F", "G", "E", "B"]
}

chord_notes = {
            "C": [60, 64, 67],
            "G": [67, 71, 74],
            "Am": [69, 72, 76],
            "F": [65, 69, 72],
            "Dm": [62, 65, 69],
            "Em": [64, 67, 71],
            "Cmaj7": [60, 64, 67, 71],
            "Gadd9": [67, 71, 74, 62],
            "Fmaj7": [65, 69, 72, 76],
            "Am7": [69, 72, 76, 79],
            "D": [62, 66, 69],
            "A": [69, 73, 76],
            "Bm": [71, 74, 78],
            "D7": [62, 66, 69, 72],
            "F#m": [66, 69, 73],
            "Cadd9": [60, 64, 67, 74],
        }


# --- FUNCTIONS ---
# -- ML Functions --

# function to get extra data from the yolo model
# this data will later be used to map the position of the note on the musical "grid"
def custom_predict(model, image, conf, save):
    results = model(image, conf=conf, save=save)

    detected_objects = []
    for result in results:
        for box in result.boxes:
            coords = box.xyxy.tolist()[0]
            x_min, y_min, x_max, y_max = coords[:4]

            center_x = (x_min + x_max) / 2
            center_y = (y_min + y_max) / 2

            label = model.names[int(box.cls)]
            score = box.conf

            detected_objects.append({
                "label": label,
                "coords": coords,
                "center_x": center_x,
                "center_y": center_y,
                "confidence": float(score)
            })

    return detected_objects


# prepare / pro cess the data for mood detection
def prepare_data(data):
    texts = [" ".join(objects) for objects, _ in data]
    labels = [mood for _, mood in data]
    return texts, labels


# train the mood model / function
def train_mood_net():
    texts, labels = prepare_data(training_data)

    model = make_pipeline(CountVectorizer(), RandomForestClassifier())
    model.fit(texts, labels)

    return model


def predict_mood(labels, mood_model):
    input_text = " ".join(labels)
    return mood_model.predict([input_text])[0]


# -- MIDI FUNCTIONS --
def create_midi(mood, filename="output.mid", bpm=120, chord_duration=1):
    """
    Create a MIDI file based on a mood's chord progression.
    
    Args:
        mood (str): The mood whose chords to use.
        filename (str): The name of the MIDI file to save.
        bpm (int): The beats per minute for the MIDI file.
        chord_duration (float): Duration of each chord in beats.
    """
    # Retrieve chord progression
    if mood not in mood_chords:
        print(f"Mood '{mood}' not found.")
        return
    
    chords = random.sample(mood_chords[mood],4)
    
    
    ticks_per_beat = 480
    time_per_chord = int(ticks_per_beat * chord_duration)
    

    midi = MidiFile()
    track = MidiTrack()
    midi.tracks.append(track)
    
    grid = list()
    
    
    tempo = int(60_000_000 / bpm)  # Microseconds per beat
    track.append(MetaMessage('set_tempo', tempo=tempo, time=0))
    
    for chord in chords:
        if chord not in chord_notes:
            print(f"Chord '{chord}' not defined.")
            continue
        
        grid.append(chord)
        
        for note in chord_notes[chord]:
            track.append(Message('note_on', note=note, velocity=64, time=0))

        track.append(Message('note_off', note=chord_notes[chord][0], velocity=64, time=time_per_chord))
        for note in chord_notes[chord][1:]:
            track.append(Message('note_off', note=note, velocity=64, time=0))

    midi.save(filename)
    print(f"MIDI file saved as '{filename}'.")
    
    return grid


def create_midi_melody(labels, data, filename="output.mid", bpm=120, note_duration=1):
    """
    Create a MIDI file based on all identified objects' notes.
    
    Args:
        mood (str): The mood whose chords to use.
        filename (str): The name of the MIDI file to save.
        bpm (int): The beats per minute for the MIDI file.
        note_duration (float): Duration of each chord in beats.
    """
    
    midi = MidiFile()
    track = MidiTrack()
    midi.tracks.append(track)
    
    grid = list()
    
    tempo = int(60_000_000 / bpm)
    track.append(MetaMessage('set_tempo', tempo=tempo, time=0))
    
    ticks_per_beat = 480
    time_per_note = int(ticks_per_beat * round((note_duration*4)/len(labels), 1))
        
    for label in labels:
        if label not in object_notes:
            print(f"label '{label}' not found.")
            note = random.choice(["C", "D", "E", "F", "G", "A", "B"])
            grid.append(note)
        
        else:
            note = random.choice(object_notes[label])
            grid.append(note)
        
        pitch = 60 + ["C", "D", "E", "F", "G", "A", "B"].index(note)
            
        track.append(Message('note_on', note=pitch, velocity=64, time=0))
        track.append(Message('note_off', note=pitch, velocity=64, time=time_per_note))

    midi.save(filename)
    print(f"MIDI file saved as '{filename}'.")
    
    return grid


# --- MAIN ---
def script(file_path, bpm, chord_duration, confidence):
    yolo_model = YOLO("yolo11n.pt")
    mood_net = train_mood_net()

    results = custom_predict(
        model=yolo_model,
        image=file_path,
        conf=confidence,
        save=False
    )
    
    labels = [obj["label"] for obj in results]
    print(f"Labels: {labels}\n")

    mood = predict_mood(labels, mood_net)
    print(f"Predicted Mood: {mood}\n")

    file_name = file_path.split('/')[-1].split('.')[0]
    
    chord_notes = create_midi(mood=mood, filename=file_name + "_chords.mid", bpm=bpm, chord_duration=chord_duration)
    melody_notes = create_midi_melody(labels=labels, data=results, filename=file_name + "_melody.mid", bpm=bpm, note_duration=chord_duration)
    
    send_midi_to_ableton(chords_track=chord_notes, melody_track=melody_notes)


def main():
    root = tk.Tk()
    root.title("MIDI Generator")

    tk.Label(root, text="Select File").grid(row=0, column=0)
    file_path_var = tk.StringVar()
    
    def select_file():
        file_path = filedialog.askopenfilename(
            filetypes=[("All Files", "*.*")]
        )
        file_path_var.set(file_path)

    file_button = tk.Button(root, text="Browse", command=select_file)
    file_button.grid(row=0, column=1)

    tk.Label(root, text="BPM").grid(row=1, column=0)
    bpm_entry = tk.Entry(root)
    bpm_entry.insert(0, "130")
    bpm_entry.grid(row=1, column=1)

    tk.Label(root, text="Chord Duration").grid(row=2, column=0)
    chord_duration_entry = tk.Entry(root)
    chord_duration_entry.insert(0, "2.0")
    chord_duration_entry.grid(row=2, column=1)

    tk.Label(root, text="YOLO Confidence").grid(row=3, column=0)
    confidence_entry = tk.Entry(root)
    confidence_entry.insert(0, "0.4")
    confidence_entry.grid(row=3, column=1)

    def on_submit():
        file_path = file_path_var.get()
        bpm = int(bpm_entry.get())
        chord_duration = float(chord_duration_entry.get())
        confidence = float(confidence_entry.get())

        if file_path:
            script(file_path, bpm, chord_duration, confidence)
        else:
            print("File selection is required.")

    submit_button = tk.Button(root, text="Generate MIDI", command=on_submit)
    submit_button.grid(row=4, columnspan=2)

    root.mainloop()


if __name__ == '__main__':
    main()