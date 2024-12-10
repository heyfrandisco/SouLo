from ultralytics import YOLO
import json, torch
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from midifunctions import save_midi_file, send_midi_to_ableton


# TODO chatgpt gives for only only octave, make it more flexible splitting C1 into "C" "1"

# --- VARIABLES ---
training_data = [
    (["tree", "river", "bird", "cat"], "serene"),
    (["bird", "cage", "chair"], "house"),
    (["car", "building", "streetlight"], "urban"),
    (["boat", "water", "fish", "seaweed", "sea"], "marine"),
    (["lion", "zebra", "tree"], "wildlife"),
    (["dog", "ball", "grass", "cat"], "playful")
]

mood_chords = {
    "serene": ["Cmaj7", "Gadd9", "Fmaj7"],
    "house": ["C", "Am", "F", "G"],
    "urban": ["D", "A", "Bm", "G"],
    "wildlife": ["C", "E", "F", "G"],
    "playful": ["G", "D", "Em", "C"]
}

object_notes = {
    "tree": "G",
    "river": "F",
    "bird": "E",
    "cage": "C",
    "chair": "D",
    "car": "A",
    "dog": "B",
    "lion": "G",
    "zebra": "F",
    "ball": "C"
}


# --- FUNCTIONS ---

# function to get extra data from the yolo model
# this data will later be used to map the position of the note on the musical "grid"
def custom_predict(model, image, conf):
    results = model(image, conf=conf)

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


def generate_music(detected_objects, mood):
    timeline = []
    base_chords = mood_chords.get(mood, mood_chords["serene"])

    # TODO change center_x to length (= duration)
    for obj in detected_objects:
        timestamp = obj["center_x"] / 640
        note = object_notes.get(obj["label"], "C")
        timeline.append({"timestamp": timestamp, "note": note})

    return base_chords, timeline


# --- MAIN ---

def main():
    file_name = "dtm"
    
    yolo_model = YOLO("yolo11n.pt")
    
    mood_net = train_mood_net()

    conf = 0.8

    results = custom_predict(model=yolo_model, image="../images/"+file_name+".png", conf=conf)
    print(f"Results: {results}\n")
    
    labels = [obj["label"] for obj in results]

    mood = predict_mood(labels, mood_net)
    print(f"Predicted Mood: {mood}\n")
    
    base_chords, timeline = generate_music(results, mood)
    print(f"Base Chords: {base_chords}")
    print(f"Timeline: {timeline}")
    
    save_midi_file(base_chords, timeline, filename=file_name+".mid")


if __name__ == '__main__':
    main()