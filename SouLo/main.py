from ultralytics import YOLO
import json, torch
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from midifunctions import save_midi_file, send_midi_to_ableton
import random


# TODO still not overlaying the label notes with chords, also problems with detections for some reason

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
}


# --- FUNCTIONS ---

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


# prepare / process the data for mood detection
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


def generate_chords(mood):
    """Generate chords based on the mood."""
    timeline = []
    base_chords = mood_chords.get(mood, mood_chords["serene"])
    chord_interval = 1.0  # Time between chords, can be adjusted
    current_time = 0.0

    for chord in base_chords:
        timeline.append({"timestamp": current_time, "note": chord, "length": chord_interval})
        current_time += chord_interval  # Proceed to the next chord

    return timeline



def generate_melody(detected_objects, chord_timeline):
    """Generate melody based on detected objects and align it with chord duration."""
    timeline = []

    # Determine the total duration of the chord timeline
    total_chord_duration = sum(chord["length"] for chord in chord_timeline)

    for obj in detected_objects:
        x_min, _, x_max, _ = obj["coords"]
        note_length = (x_max - x_min) / 640 * total_chord_duration  # Scale note length to match chord duration

        possible_notes = object_notes.get(obj["label"], ["C"])
        note = random.choice(possible_notes)

        timeline.append({
            "timestamp": obj["center_x"] / 640 * total_chord_duration,  # Scale timing to match chord duration
            "note": note,
            "length": note_length
        })

    return timeline



# --- MAIN ---

def main():
    file_name = "serene_playful"

    yolo_model = YOLO("yolo11n.pt")

    mood_net = train_mood_net()

    conf = 0.35

    results = custom_predict(model=yolo_model, image="../images/test_images/" + file_name + ".png", conf=conf, save=True)
    print(f"Results: {results}\n")

    labels = [obj["label"] for obj in results]

    mood = predict_mood(labels, mood_net)
    print(f"Predicted Mood: {mood}\n")

    chords_timeline = generate_chords(mood)
    melody_timeline = generate_melody(results, chords_timeline)

    save_midi_file(chords_timeline, chords_timeline, filename=file_name + "_chords.mid")
    save_midi_file(melody_timeline, melody_timeline, filename=file_name + "_melody.mid")

if __name__ == '__main__':
    main()