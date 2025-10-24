"""
This module contains classes and functions to represent melodies and extract information
from MIDI sequence data.
"""

__author__ = "David Whyatt"
import json


class Melody:
    """Class to represent a melody from a MIDI sequence. This class is used to extract
    information from a json file containing MIDI sequence data, formatted accordingly:
    A note is represented as a string in the format:
    'Note(start=0.0, end=0.25, pitch=60, velocity=100)'
    We don't need the velocity, so we can ignore it here.

    Attributes:
        pitches (list[int]): List of MIDI note pitches in order of appearance
        starts (list[float]): List of note start times in order of appearance
        ends (list[float]): List of note end times in order of appearance
    """

    def __init__(self, midi_data: dict, tempo: float = None):
        """Initialize a Melody object from MIDI sequence data.

        Args:
            midi_data (dict): Dictionary containing MIDI sequence data
            tempo (float, optional): Tempo in BPM. If None, uses tempo from midi_data if available.
        """
        self._midi_data = midi_data
        # Split on 'Note(' and remove the first empty string
        self._midi_sequence = midi_data["MIDI Sequence"].split("Note(")[1:]

        # Use tempo from midi_data if available, otherwise use provided tempo or default
        if tempo is not None:
            self._tempo = tempo
        elif "tempo" in midi_data:
            self._tempo = midi_data["tempo"]
        else:
            self._tempo = 100.00  # Default fallback tempo
            
        # Store tempo changes if available
        self._tempo_changes = midi_data.get("tempo_changes", [(0.0, self._tempo)])

    @property
    def id(self) -> str:
        """Get the ID (file path) of the MIDI file.

        Returns:
            str: File path or ID of the MIDI file
        """
        return self._midi_data.get("ID", "")
    
    @property
    def pitches(self) -> list[int]:
        """Extract pitch values from MIDI sequence.

        Returns:
            list[int]: List of MIDI pitch values in order of appearance
        """
        pitches = []
        for note in self._midi_sequence:
            # Find pitch value between 'pitch=' and the next comma or closing parenthesis
            pitch_start = note.find("pitch=") + 6
            # Look for comma after pitch, but not the comma that ends the note
            pitch_end = note.find(",", pitch_start)
            if pitch_end == -1:  # Handle the last note which ends with ')'
                pitch_end = note.find(")", pitch_start)
            elif note[pitch_end + 1:pitch_end + 2] == ")":  # If comma is followed by ), it's the end of note
                pitch_end = note.find(")", pitch_start)
            if pitch_end != -1:  # Only process if we found a valid pitch
                pitch_str = note[pitch_start:pitch_end]
                # Clean up any trailing characters
                pitch_str = pitch_str.rstrip(",)")
                pitch = int(pitch_str)
                pitches.append(pitch)
        return pitches

    @property
    def starts(self) -> list[float]:
        """Extract start times from MIDI sequence.

        Returns:
            list[float]: List of MIDI note start times in order of appearance
        """
        starts = []
        for note in self._midi_sequence:
            # Find start time between 'start=' and the next comma
            start_start = note.find("start=") + 6
            start_end = note.find(",", start_start)
            if start_end != -1:  # Only process if we found a valid start time
                start = float(note[start_start:start_end])
                starts.append(start)
        return starts

    @property
    def ends(self) -> list[float]:
        """Extract end times from MIDI sequence.

        Returns:
            list[float]: List of MIDI note end times in order of appearance
        """
        ends = []
        for note in self._midi_sequence:
            # Find end time between 'end=' and the next comma or closing parenthesis
            end_start = note.find("end=") + 4
            end_end = note.find(",", end_start)
            if end_end == -1:  # Handle the last note which ends with ')'
                end_end = note.find(")", end_start)
            if end_end != -1:  # Only process if we found a valid end time
                end = float(note[end_start:end_end])
                ends.append(end)
        return ends

    @property
    def tempo(self) -> float:
        """Extract tempo from Class input.

        Returns:
            float: Tempo of the melody in beats per minute
        """
        return self._tempo
    
    @property
    def tempo_changes(self) -> list[tuple[float, float]]:
        """Get tempo changes from the melody.

        Returns:
            list[tuple[float, float]]: List of (time_in_seconds, tempo_in_bpm) tuples
        """
        return self._tempo_changes
    

    @property
    def meter(self) -> tuple[int, int]:
        """Extract the first time signature from the melody.
        
        Returns:
            tuple[int, int]: First time signature as (numerator, denominator)
                           Defaults to (4, 4) if no time signature information available
        """
        time_sig_info = self._midi_data.get("time_signature_info")
        if time_sig_info and "first_time_signature" in time_sig_info:
            return time_sig_info["first_time_signature"]
        return (4, 4)  # Default to 4/4 if no information available

    @property
    def time_signatures(self) -> list[tuple[float, int, int]]:
        """Get all time signatures present in the melody.
        
        Returns:
            list[tuple[float, int, int]]: List of tuples (time_in_seconds, numerator, denominator).
                If none are available, falls back to a single entry using the first meter at time 0.0.
        """
        time_sig_info = self._midi_data.get("time_signature_info")
        if time_sig_info and "all_time_signatures" in time_sig_info:
            return time_sig_info["all_time_signatures"]
        num, den = self.meter
        return [(0.0, num, den)]

    @property  
    def proportion_of_time_in_first_meter(self) -> float:
        """Calculate the proportion of time spent in the first time signature.
        
        Returns:
            float: Proportion (0.0 to 1.0) that the first time signature comprises 
                   of the total melody duration. 1.0 means the melody uses only 
                   one time signature throughout.
        """
        time_sig_info = self._midi_data.get("time_signature_info")
        if time_sig_info and "proportion_of_time_in_first_meter" in time_sig_info:
            return time_sig_info["proportion_of_time_in_first_meter"]
        return 0.0

    @property
    def total_duration(self) -> float:
        """Get the total duration of the MIDI sequence in seconds.
        
        Returns:
            float: Total duration of the MIDI sequence in seconds, including any 
                   leading or trailing silence. This matches jSymbolic's 
                   DurationInSecondsFeature implementation.
        """
        return self._midi_data.get("total_duration", 0.0)
    
    @property
    def key_signature(self) -> tuple:
        """Get the first key signature in the melody.
        
        Returns:
            tuple or None: (key_name, mode) where key_name is a string like 'C', 'Am', 'F#'
                          and mode is either 'major' or 'minor'. Returns None if no key signature found.
        """
        key_sig_info = self._midi_data.get("key_signature_info")
        if key_sig_info:
            return key_sig_info.get("first_key_signature")
        return None
    
    @property
    def key_signatures(self) -> list:
        """Get all key signatures present in the melody.
        
        Returns:
            list[tuple]: List of tuples (key_name, mode) for all key signatures.
                        Empty list if no key signatures are found.
        """
        key_sig_info = self._midi_data.get("key_signature_info")
        if key_sig_info:
            return key_sig_info.get("all_key_signatures", [])
        return []
    
    @property
    def has_key_signature(self) -> bool:
        """Check if the MIDI file contains any key signature information.
        
        Returns:
            bool: True if at least one key signature was found, False otherwise.
        """
        key_sig_info = self._midi_data.get("key_signature_info")
        if key_sig_info:
            return key_sig_info.get("has_key_signature", False)
        return False
    
    @property
    def key_fifths(self) -> int:
        """Get the circle of fifths position of the first key signature.
        
        Returns:
            int or None: Position on circle of fifths (-7 to 7) where:
                        0 = C major / A minor
                        Positive = sharps (G=1, D=2, A=3, E=4, B=5, F#=6, C#=7)
                        Negative = flats (F=-1, Bb=-2, Eb=-3, Ab=-4, Db=-5, Gb=-6, Cb=-7)
                        Returns None if no key signature found.
        """
        key_sig_info = self._midi_data.get("key_signature_info")
        if key_sig_info:
            return key_sig_info.get("fifths")
        return None
    
    @property
    def key_mode(self) -> int:
        """Get the mode of the first key signature as an integer.
        
        Returns:
            int or None: 1 for major, -1 for minor. Returns None if no key signature found.
        """
        key_sig_info = self._midi_data.get("key_signature_info")
        if key_sig_info:
            return key_sig_info.get("mode")
        return None

    

def read_midijson(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)
