import os
import time
import rtmidi
from mido import Message, MidiFile, MidiTrack

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
            "E": [64, 68, 71],
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



def note_to_midi(note_name):
    note_mapping = {
        'C': 60, 'C#': 61, 'D': 62, 'D#': 63, 'E': 64, 'F': 65, 'F#': 66,
        'G': 67, 'G#': 68, 'A': 69, 'A#': 70, 'B': 71,
        'C5': 72, 'C#5': 73, 'D5': 74, 'D#5': 75, 'E5': 76, 'F5': 77,
        'F#5': 78, 'G5': 79, 'G#5': 80, 'A5': 81, 'A#5': 82, 'B5': 83,
    }
    return note_mapping[note_name]


def send_midi_to_ableton(chords_track, melody_track):
    """Sends MIDI data to separate channels in Ableton Live."""
    midi_out = rtmidi.MidiOut()
    available_ports = midi_out.get_ports()

    virtual_port = None
    for i, port in enumerate(available_ports):
        if "IAC" in port or "LoopMIDI" in port or "Ableton" in port:
            virtual_port = i
            break

    if virtual_port is None:
        print("No virtual MIDI port found. Please set one up and restart.")
        return

    midi_out.open_port(virtual_port)
    print(f"Connected to MIDI port: {available_ports[virtual_port]}")

    def send_notes(notes, channel, duration=1):
        for note in notes:
            midi_out.send_message([0x90 + channel, note, 64])  # Note on with channel
        time.sleep(duration)  # Wait duration
        for note in notes:
            midi_out.send_message([0x80 + channel, note, 64])  # Note off with channel

    # Send chords to channel 1 (0 in MIDI terms)
    for chord in chords_track:
        if chord in chord_notes:
            notes = chord_notes[chord]
        else:
            print(f"Invalid chord: {chord}")
            continue
        
        send_notes(notes, channel=0)

    # Send melody to channel 2 (1 in MIDI terms)
    for note in melody_track:
        if isinstance(note, str):
            note = note_to_midi(note)
        send_notes([note], channel=1)


    midi_out.close_port()
    print("Finished sending MIDI to Ableton.")


def save_midi_file(chords_timeline, melody_timeline, filename="output.mid"):
    """Save chords and melody as separate tracks in a MIDI file."""
    midi = MidiFile()
    
    # Create the chords track
    chords_track = MidiTrack()
    midi.tracks.append(chords_track)
    chords_track.append(Message('program_change', program=1))  # Piano sound
    
    for chord in chords_timeline:
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

        notes = chord_notes.get(chord["chord"], [60])
        start_time = int(chord["timestamp"] * 480)  # Convert seconds to ticks
        
        # Add chord notes
        for note in notes:
            chords_track.append(Message('note_on', note=note, velocity=64, time=start_time))
            chords_track.append(Message('note_off', note=note, velocity=64, time=start_time + int(chord["length"] * 480)))
    
    # Create the melody track
    melody_track = MidiTrack()
    midi.tracks.append(melody_track)
    melody_track.append(Message('program_change', program=1))  # Piano sound
    
    for note in melody_timeline:
        start_time = int(note["timestamp"] * 480)
        length = int(note["length"] * 480)
        pitch = 60 + ["C", "D", "E", "F", "G", "A", "B"].index(note["note"][0])
        melody_track.append(Message('note_on', note=pitch, velocity=64, time=start_time))
        melody_track.append(Message('note_off', note=pitch, velocity=64, time=start_time + length))
    
    # Save the MIDI file
    midi.save(filename)



def chord_to_midi(chord):
    """Convert chord names to MIDI note numbers."""
    chord_map = {
        "C": [60, 64, 67],
        "Cmaj7": [60, 64, 67, 71],
        "Gadd9": [67, 71, 74],
        "Fmaj7": [65, 69, 72, 76],
        "Am": [57, 60, 64],
        "D": [62, 66, 69],
        "A": [69, 73, 76],
        "Bm": [59, 62, 66],
        "Em": [64, 67, 71]
    }
    return chord_map.get(chord, [60])


def note_to_midi(note):
    """Convert note names to MIDI note numbers."""
    note_map = {
        "C": 60, "D": 62, "E": 64, "F": 65, "G": 67, "A": 69, "B": 71
    }
    octave = 4  # Default octave
    if len(note) > 1 and note[1].isdigit():
        octave = int(note[1])
        note = note[0]
    return note_map.get(note, 60) + (octave - 4) * 12  # Adjust by octave


def adjust_chords_to_melody(chords_timeline, melody_timeline):
    melody_end = melody_timeline[-1]["timestamp"] + melody_timeline[-1]["length"]
    chord_end = chords_timeline[-1]["timestamp"] + chords_timeline[-1]["length"]
    
    # Extend chords if melody is longer
    while chord_end < melody_end:
        for chord in chords_timeline:
            new_chord = chord.copy()
            new_chord["timestamp"] = chord_end
            chords_timeline.append(new_chord)
            chord_end = new_chord["timestamp"] + new_chord["length"]
            if chord_end >= melody_end:
                break
                
    return chords_timeline
