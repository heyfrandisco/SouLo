import os
import time
import rtmidi
from mido import Message, MidiFile, MidiTrack

def send_midi_to_ableton(base_chords, timeline):
    """Sends MIDI data to a virtual MIDI port connected to Ableton Live."""
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

    # Send chords (background harmony) at regular intervals
    for chord in base_chords:
        notes = chord_to_midi(chord)
        for note in notes:
            midi_out.send_message([0x90, note, 64])  # Note on
        time.sleep(1)  # Wait 1 second between chords
        for note in notes:
            midi_out.send_message([0x80, note, 64])  # Note off

    # Send timeline notes
    for item in timeline:
        time.sleep(item["timestamp"])  # Wait until timestamp
        note = note_to_midi(item["note"])
        midi_out.send_message([0x90, note, 64])  # Note on
        time.sleep(0.5)  # Hold note for 0.5 seconds
        midi_out.send_message([0x80, note, 64])  # Note off

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
