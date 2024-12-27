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


def save_midi_file(base_chords, timeline, filename="output.mid"):
    """Save the generated music as a MIDI file in a specific folder."""
    output_dir = "midi_outputs"
    os.makedirs(output_dir, exist_ok=True)

    filepath = os.path.join(output_dir, filename)

    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Add chords
    for chord_event in base_chords:
        chord = chord_event["note"]  # Extract the chord name
        chord_notes = chord_to_midi(chord)  # Convert chord to a list of MIDI note numbers
        for note in chord_notes:
            track.append(Message('note_on', note=note, velocity=64, time=0))
        for note in chord_notes:
            track.append(Message('note_off', note=note, velocity=64, time=480))  # Time in ticks

    # Add melody
    for item in timeline:
        ticks = int(item["timestamp"] * 480)  # Convert timestamp to MIDI ticks
        length_ticks = int(item["length"] * 480)  # Convert length to MIDI ticks
        note = note_to_midi(item["note"])
        track.append(Message('note_on', note=note, velocity=64, time=ticks))
        track.append(Message('note_off', note=note, velocity=64, time=length_ticks))

    mid.save(filepath)
    print(f"MIDI file saved as {filepath}")



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
