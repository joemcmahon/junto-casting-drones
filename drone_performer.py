#!/usr/bin/env python3
"""
Drone Performance MIDI Player
Performs drone scores on multiple MIDI channels for routing to Ableton Live.
Can parse existing scores or generate new ones dynamically.
"""

import re
import time
import argparse
import random
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass
from collections import defaultdict

try:
    import rtmidi
except ImportError:
    print("ERROR: python-rtmidi not installed.")
    print("Install with: pip install python-rtmidi")
    exit(1)


@dataclass
class ScoreBracket:
    """Represents one time bracket in the score"""
    time_seconds: float  # Time in seconds (can be fractional)
    drone: str
    notes: List[str]
    duration_seconds: float  # Duration in seconds (can be fractional)

    def __repr__(self):
        notes_str = ' '.join(sorted(self.notes)) if self.notes else 'nothing'
        # Format time as MM:SS
        total_seconds = int(self.time_seconds)
        mm = total_seconds // 60
        ss = total_seconds % 60
        # Format duration
        if self.duration_seconds < 60:
            duration_str = f"{self.duration_seconds:.1f}s"
        else:
            duration_min = self.duration_seconds / 60.0
            duration_str = f"{duration_min:.1f}m"
        return f"{mm:02d}:{ss:02d} Playing {self.drone} (drone) + {notes_str} for {duration_str}"


class MIDINoteConverter:
    """Convert note names (like A4, C#3) to MIDI note numbers"""

    NOTE_MAP = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

    @staticmethod
    def note_to_midi(note: str) -> int:
        """Convert note like 'C#4' to MIDI number (middle C=60)"""
        match = re.match(r'([A-G])(#|b)?(\d+)', note)
        if not match:
            raise ValueError(f"Invalid note format: {note}")

        note_name, accidental, octave = match.groups()
        midi_num = MIDINoteConverter.NOTE_MAP[note_name]

        if accidental == '#':
            midi_num += 1
        elif accidental == 'b':
            midi_num -= 1

        # MIDI octave: C4 (middle C) = 60
        # Our octave numbering: octave 4 means MIDI octave 4
        midi_num += (int(octave) + 1) * 12

        return midi_num


class DroneScoreParser:
    """Parse score files in the performance.md format"""

    @staticmethod
    def parse_score_file(filename: str) -> List[ScoreBracket]:
        """Parse a score file and return list of brackets"""
        brackets = []

        with open(filename, 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        for i, line in enumerate(lines):
            if 'fade in' in line or 'fade out' in line:
                continue

            # Parse: "00:00 Playing A1 (drone) + E3 F#4 B4 for 2 minutes"
            match = re.match(r'(\d+):(\d+)\s+Playing\s+(\S+)\s+\(drone\)\s+\+\s+(.*?)\s+for\s+(\d+)\s+minute', line)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                time_seconds = minutes * 60 + seconds
                drone = match.group(3)
                notes_str = match.group(4).strip()
                duration_minutes = int(match.group(5))
                duration_seconds = duration_minutes * 60

                # Parse notes, filtering out invalid ones
                notes = []
                if notes_str and notes_str != 'nothing':
                    for note in notes_str.split():
                        # Clean up typos like "B43" or "E35" - take only valid note format
                        if re.match(r'^[A-G](#|b)?[1-6]$', note):
                            notes.append(note)

                brackets.append(ScoreBracket(time_seconds, drone, notes, duration_seconds))

        return brackets


class DroneScoreGenerator:
    """Generate drone scores algorithmically (ported from Perl script)"""

    def __init__(self, drones: List[str] = None, scale: List[str] = None,
                 max_minutes: int = 61, drone_time: float = 60.0):
        self.drones = drones or ["A1"]
        self.scale = scale or ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        self.max_seconds = max_minutes * 60  # Convert to seconds
        self.drone_time = drone_time  # in seconds
        self.step_choices = [60, 60, 120, 120, 120, 180]  # Convert minutes to seconds

    def _get_drone_for_time(self, seconds: float) -> str:
        """Get the appropriate drone note for a given time in seconds"""
        # Calculate which drone index we should be at
        drone_index = int(seconds // self.drone_time) % len(self.drones)
        return self.drones[drone_index]

    def generate_score(self) -> List[ScoreBracket]:
        """
        Generate a complete score where:
        - Drones cycle continuously on their own timeline
        - Note brackets are independent and can span multiple drone changes
        - We create sub-brackets when drones change during a note bracket
        """
        # Generate note change times (independent of drone changes)
        change_times = []
        max_offset = min(self.drone_time, min(self.step_choices))
        now = random.uniform(0, max_offset)
        while now < self.max_seconds:
            change_times.append(now)
            step = random.choice(self.step_choices)
            now += step

        # Generate all drone change times
        drone_times = []
        t = 0
        while t < self.max_seconds:
            drone_times.append(t)
            t += self.drone_time

        # Create final bracket timeline
        brackets = []
        notes = []

        # Process each note bracket (from one note change to the next)
        for i in range(len(change_times)):
            # Update notes BEFORE creating this bracket (so first bracket can have notes)
            valid = False
            while not valid:
                action = random.randint(1, 6)
                valid = (action < 5 or
                        (action == 5 and len(notes) > 1) or
                        (action == 6 and len(notes) > 2))

            if action <= 4:
                notes = self._add_or_change_notes(action, notes)
            elif action == 5:
                notes = self._drop_one_note(notes)
            elif action == 6:
                notes = self._drop_two_notes(notes)

            # Now create bracket(s) with the updated notes
            bracket_start = change_times[i]
            bracket_end = change_times[i + 1] if i + 1 < len(change_times) else self.max_seconds

            # Find all drone changes within this note bracket
            drone_changes_in_bracket = [t for t in drone_times if bracket_start <= t < bracket_end]

            # If no drone changes, create one bracket for the whole duration
            if not drone_changes_in_bracket:
                current_drone = self._get_drone_for_time(bracket_start)
                brackets.append(ScoreBracket(bracket_start, current_drone, notes.copy(),
                                            bracket_end - bracket_start))
            else:
                # Create sub-brackets for each drone change
                sub_start = bracket_start
                for drone_change_time in drone_changes_in_bracket:
                    current_drone = self._get_drone_for_time(sub_start)
                    brackets.append(ScoreBracket(sub_start, current_drone, notes.copy(),
                                                drone_change_time - sub_start))
                    sub_start = drone_change_time

                # Final sub-bracket from last drone change to end of note bracket
                current_drone = self._get_drone_for_time(sub_start)
                brackets.append(ScoreBracket(sub_start, current_drone, notes.copy(),
                                            bracket_end - sub_start))

        return brackets

    def _get_unused_notes(self, current_notes: List[str]) -> List[str]:
        """Get all possible notes not currently playing"""
        all_notes = []
        for octave in range(3, 6):
            for note in self.scale:
                all_notes.append(f"{note}{octave}")

        return [n for n in all_notes if n not in current_notes]

    def _add_or_change_notes(self, count: int, notes: List[str]) -> List[str]:
        """Add or change notes"""
        if count > len(notes):
            # Add notes
            unused = self._get_unused_notes(notes)
            to_add = min(count, len(unused))
            new_notes = random.sample(unused, to_add)
            return notes + new_notes
        else:
            # Change notes
            result = notes.copy()
            unused = self._get_unused_notes(result)
            for _ in range(min(count, len(result), len(unused))):
                if result and unused:
                    result.pop(0)
                    result.append(random.choice(unused))
                    unused = self._get_unused_notes(result)
            return result

    def _drop_one_note(self, notes: List[str]) -> List[str]:
        """Drop one note"""
        if notes:
            result = notes.copy()
            result.pop(0)
            return result
        return notes

    def _drop_two_notes(self, notes: List[str]) -> List[str]:
        """Drop two notes"""
        if len(notes) >= 2:
            result = notes.copy()
            result.pop(0)
            result.pop(0)
            return result
        return notes


class MIDIPerformer:
    """Perform a score via MIDI output"""

    def __init__(self, port_name: str = "Drone Performer", velocity: int = 80, debug: bool = False,
                 note_fade_in: float = 1.5, note_fade_out: float = 2.0,
                 drone_fade_in: float = 3.0, drone_fade_out: float = 3.0):
        self.velocity = velocity
        self.debug = debug
        self.note_fade_in = note_fade_in
        self.note_fade_out = note_fade_out
        self.drone_fade_in = drone_fade_in
        self.drone_fade_out = drone_fade_out
        self.midi_out = rtmidi.MidiOut()

        # Create virtual MIDI port
        try:
            self.midi_out.open_virtual_port(port_name)
            print(f"✓ Created virtual MIDI port: '{port_name}'")
            print(f"  Configure Ableton Live to receive MIDI from this port")
            if self.debug:
                print(f"  Debug mode: Will show all MIDI messages")
        except Exception as e:
            print(f"ERROR: Could not create virtual MIDI port: {e}")
            exit(1)

        # Track which notes are on which channels
        self.note_channels: Dict[str, int] = {}
        self.next_channel = 1  # Start at channel 1 (MIDI channel 2); channel 0 reserved for drone
        self.active_notes: Set[str] = set()
        self.channel_volumes: Dict[int, int] = {0: 127}  # Track volume per channel
        self.current_drone: str = None  # Track the current drone note

    def _allocate_channel(self, note: str) -> int:
        """Allocate a MIDI channel for a harmony note (channels 1-15, MIDI channels 2-16)"""
        if note not in self.note_channels:
            self.note_channels[note] = self.next_channel
            self.next_channel += 1
            if self.next_channel > 15:  # Wrap around to channel 1 (MIDI channel 2)
                self.next_channel = 1
        return self.note_channels[note]

    def _send_note_on(self, note: str, channel: int = 0):
        """Send MIDI note on"""
        midi_note = MIDINoteConverter.note_to_midi(note)
        # MIDI: [status, note, velocity], status = 0x90 + channel
        message = [0x90 + channel, midi_note, self.velocity]
        self.midi_out.send_message(message)
        if self.debug:
            midi_channel = channel + 1  # Display as MIDI channel 1-16
            print(f"  [MIDI] Note ON:  {note:4s} = MIDI#{midi_note:3d} on MIDI channel {midi_channel:2d} (vel={self.velocity}) -> {message}")

    def _send_note_off(self, note: str, channel: int = 0):
        """Send MIDI note off"""
        midi_note = MIDINoteConverter.note_to_midi(note)
        # MIDI: [status, note, velocity], status = 0x80 + channel
        message = [0x80 + channel, midi_note, 0]
        self.midi_out.send_message(message)
        if self.debug:
            midi_channel = channel + 1  # Display as MIDI channel 1-16
            print(f"  [MIDI] Note OFF: {note:4s} = MIDI#{midi_note:3d} on MIDI channel {midi_channel:2d} -> {message}")

    def _send_volume(self, channel: int, volume: int):
        """Send MIDI CC#7 (Channel Volume) message"""
        # MIDI CC: [status, controller, value], status = 0xB0 + channel
        # CC#7 = Channel Volume (0-127)
        volume = max(0, min(127, volume))  # Clamp to valid range
        message = [0xB0 + channel, 7, volume]
        self.midi_out.send_message(message)
        if self.debug:
            midi_channel = channel + 1  # Display as MIDI channel 1-16
            print(f"  [MIDI] Volume:   MIDI ch{midi_channel:2d} = {volume:3d}/127 -> {message}")

    def _set_all_volumes(self, volume: int):
        """Set volume on all active channels"""
        # Set drone channel
        self._send_volume(0, volume)
        self.channel_volumes[0] = volume
        # Set all allocated harmony channels
        for channel in set(self.note_channels.values()):
            self._send_volume(channel, volume)
            self.channel_volumes[channel] = volume

    def _fade_channel_in(self, channel: int, duration: float):
        """Fade a channel from 0 to 127 over duration seconds"""
        if duration <= 0:
            self._send_volume(channel, 127)
            self.channel_volumes[channel] = 127
            return

        steps = max(10, int(duration * 20))  # 20 updates per second
        for i in range(steps + 1):
            volume = int((i / steps) * 127)
            self._send_volume(channel, volume)
            self.channel_volumes[channel] = volume
            if i < steps:
                time.sleep(duration / steps)

    def _fade_channel_out(self, channel: int, duration: float):
        """Fade a channel from current volume to 0 over duration seconds"""
        if duration <= 0:
            self._send_volume(channel, 0)
            self.channel_volumes[channel] = 0
            return

        start_volume = self.channel_volumes.get(channel, 127)
        steps = max(10, int(duration * 20))  # 20 updates per second
        for i in range(steps + 1):
            volume = int(start_volume * (1 - i / steps))
            self._send_volume(channel, volume)
            self.channel_volumes[channel] = volume
            if i < steps:
                time.sleep(duration / steps)

    def _update_notes(self, new_notes: Set[str], drone: str, skip_fades: bool = False) -> tuple[list, list]:
        """
        Update which notes are playing

        Args:
            new_notes: Set of notes that should be playing
            drone: The drone note for this bracket
            skip_fades: If True, skip individual note fades (used during global fade-in)

        Returns:
            (stopped_notes, started_notes) - lists of (note, channel) tuples
        """
        stopped_notes = []
        started_notes = []

        # Handle drone transitions on channel 0
        if self.current_drone != drone:
            # Drone is changing
            if self.current_drone is not None:
                # Fade out and stop the old drone (unless skipping fades)
                if not skip_fades:
                    self._fade_channel_out(0, self.drone_fade_out)
                self._send_note_off(self.current_drone, 0)
                self.active_notes.discard(self.current_drone)
                stopped_notes.append((self.current_drone, 0))

            # Start new drone at volume 0
            self._send_volume(0, 0)
            self.channel_volumes[0] = 0
            # Send note on
            self._send_note_on(drone, 0)
            self.active_notes.add(drone)
            self.current_drone = drone
            started_notes.append((drone, 0))
            # Fade in (unless skipping fades for global fade-in)
            if not skip_fades:
                self._fade_channel_in(0, self.drone_fade_in)

        # Stop notes that should no longer play (with fade out)
        to_stop = self.active_notes - new_notes - {drone}
        for note in sorted(to_stop):
            channel = self._allocate_channel(note)
            # Fade out before stopping (unless skipping fades)
            if not skip_fades:
                self._fade_channel_out(channel, self.note_fade_out)
            self._send_note_off(note, channel)
            self.active_notes.discard(note)
            stopped_notes.append((note, channel))

        # Start new notes (with fade in)
        to_start = new_notes - self.active_notes
        for note in sorted(to_start):
            channel = self._allocate_channel(note)
            # Start at volume 0
            self._send_volume(channel, 0)
            self.channel_volumes[channel] = 0
            # Send note on
            self._send_note_on(note, channel)
            self.active_notes.add(note)
            started_notes.append((note, channel))
            # Fade in after starting (unless skipping fades for global fade-in)
            if not skip_fades:
                self._fade_channel_in(channel, self.note_fade_in)

        return stopped_notes, started_notes

    def _stop_all_notes(self):
        """Stop all currently playing notes"""
        for note in list(self.active_notes):
            if note in self.note_channels:
                channel = self.note_channels[note]
            else:
                channel = 0
            self._send_note_off(note, channel)
        self.active_notes.clear()

    def perform(self, brackets: List[ScoreBracket], time_scale: float = 1.0,
                fade_in: float = 5.0, fade_out: float = 5.0):
        """
        Perform a score

        Args:
            brackets: List of score brackets to perform
            time_scale: Time multiplier (1.0 = real time, 0.1 = 10x faster, etc.)
            fade_in: Fade in duration in seconds (scaled time)
            fade_out: Fade out duration in seconds (scaled time)
        """
        print(f"\n{'='*60}")
        print(f"Starting performance (time scale: {time_scale}x)")
        if fade_in > 0:
            print(f"Fade in: {fade_in}s, Fade out: {fade_out}s")
        print(f"{'='*60}\n")

        start_time = time.time()

        # Start with volume at 0 for fade-in
        if fade_in > 0:
            self._set_all_volumes(0)

        try:
            for i, bracket in enumerate(brackets):
                # Wait until the bracket's start time
                target_time = bracket.time_seconds * time_scale
                current_time = time.time() - start_time
                sleep_time = target_time - current_time

                if sleep_time > 0:
                    time.sleep(sleep_time)

                # Update playing notes
                notes_set = set(bracket.notes)
                # Skip individual note fades if we're in the global fade-in period
                current_time = time.time() - start_time
                skip_fades = fade_in > 0 and current_time < fade_in
                stopped_notes, started_notes = self._update_notes(notes_set, bracket.drone, skip_fades)

                # Print the bracket change
                actual_time = time.time() - start_time
                notes_str = ' '.join(sorted(bracket.notes)) if bracket.notes else 'nothing'
                # Format time as MM:SS
                total_seconds = int(bracket.time_seconds)
                mm = total_seconds // 60
                ss = total_seconds % 60
                print(f"\n[{actual_time:6.1f}s] {mm:02d}:{ss:02d} Playing {bracket.drone} (drone) + {notes_str}")

                # Show what changed (display MIDI channels 1-16)
                if stopped_notes:
                    stopped_str = ', '.join([f"{note} (MIDI ch{ch+1})" for note, ch in stopped_notes])
                    print(f"            Stopped: {stopped_str}")
                if started_notes:
                    started_str = ', '.join([f"{note} (MIDI ch{ch+1})" for note, ch in started_notes])
                    print(f"            Started: {started_str}")

                # Calculate when this bracket ends
                is_last_bracket = (i + 1 >= len(brackets))
                if not is_last_bracket:
                    next_bracket_time = brackets[i + 1].time_seconds * time_scale
                    bracket_duration = next_bracket_time - target_time
                else:
                    # Last bracket - sustain for a few seconds before fade out
                    # Give notes time to breathe after fading in
                    sustain_time = 3.0  # seconds
                    bracket_duration = sustain_time

                # Ticker: update the current line every second until the next bracket
                elapsed_in_bracket = 0
                while elapsed_in_bracket < bracket_duration:
                    current_time = time.time() - start_time
                    elapsed_in_bracket = current_time - target_time

                    # Handle fade-in during the first fade_in seconds
                    if fade_in > 0 and current_time < fade_in:
                        volume = int((current_time / fade_in) * 127)
                        self._set_all_volumes(volume)

                    # Format the ticker line
                    total_elapsed = time.time() - start_time
                    ticker = f"\r[{total_elapsed:6.1f}s] Playing for {elapsed_in_bracket:4.1f}s / {bracket_duration:4.1f}s"

                    # Add visual indicator
                    beats = int(elapsed_in_bracket) % 4
                    ticker += " " + "." * beats + " " * (3 - beats)

                    print(ticker, end='', flush=True)

                    # Calculate remaining time and sleep if positive
                    remaining = bracket_duration - elapsed_in_bracket
                    if remaining <= 0:
                        break

                    # Sleep briefly before next update (max 1 second)
                    time.sleep(min(1.0, remaining))

        except KeyboardInterrupt:
            print("\n\nPerformance interrupted by user")

        finally:
            # Fade out
            print(f"\n\n[{(time.time() - start_time):6.1f}s] Fading out...")
            if fade_out > 0:
                # Capture current volume of each active channel
                initial_volumes = self.channel_volumes.copy()
                fade_start = time.time()
                steps = max(10, int(fade_out * 20))  # 20 updates per second

                for i in range(steps + 1):
                    elapsed = time.time() - fade_start
                    if elapsed >= fade_out:
                        break

                    # Fade each channel from its current volume to 0
                    progress = elapsed / fade_out
                    for channel, start_vol in initial_volumes.items():
                        volume = int(start_vol * (1 - progress))
                        self._send_volume(channel, volume)
                        self.channel_volumes[channel] = volume

                    time.sleep(fade_out / steps)

                # Ensure all volumes are at 0
                for channel in initial_volumes.keys():
                    self._send_volume(channel, 0)
                    self.channel_volumes[channel] = 0

            self._stop_all_notes()
            print(f"\n{'='*60}")
            print(f"Performance complete")
            print(f"{'='*60}\n")

    def close(self):
        """Close MIDI connection"""
        self._stop_all_notes()
        del self.midi_out


def main():
    parser = argparse.ArgumentParser(
        description='Perform drone scores via MIDI for Ableton Live',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Perform existing score at real-time
  %(prog)s --score performance.md

  # Perform existing score 10x faster (for testing)
  %(prog)s --score performance.md --time-scale 0.1

  # Generate and perform new score with single drone
  %(prog)s --generate --end 20 --drone C1 --scale C,D,E,F#,G#,A#

  # Generate with cycling drones (changes every 30 seconds)
  %(prog)s --generate --end 10 --drone B1,F#1,G#1,A#1 --dronetime 30 --scale B,C#,D#,F,F#,G#,A#

  # Generate 10-minute score at 6x speed
  %(prog)s --generate --end 10 --time-scale 0.166
        """
    )

    # Mode selection
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--score', type=str, help='Score file to perform (e.g., performance.md)')
    mode.add_argument('--generate', action='store_true', help='Generate new score algorithmically')

    # Generation options
    parser.add_argument('--end', type=int, default=61, help='End time in SCORE minutes (default: 61)')
    parser.add_argument('--drone', type=str, default='A1', help='Drone note(s), comma-separated for cycling (default: A1)')
    parser.add_argument('--dronetime', type=float, default=60.0, help='Time per drone in PERFORMANCE seconds when cycling (default: 60.0)')
    parser.add_argument('--scale', type=str, help='Scale notes, comma-separated (default: A,B,C,D,E,F,G)')

    # Performance options
    parser.add_argument('--time-scale', type=float, default=1.0,
                       help='Time scale multiplier: 1.0=real-time, 0.1=10x faster (default: 1.0)')
    parser.add_argument('--velocity', type=int, default=80,
                       help='MIDI velocity (1-127, default: 80)')
    parser.add_argument('--port-name', type=str, default='Drone Performer',
                       help='Virtual MIDI port name (default: "Drone Performer")')
    parser.add_argument('--auto-start', action='store_true',
                       help='Start immediately without waiting for user (default: wait for Enter key)')
    parser.add_argument('--debug', action='store_true',
                       help='Show detailed MIDI message debug output')
    parser.add_argument('--fade-in', type=float, default=5.0,
                       help='Global fade in duration in seconds (default: 5.0, 0=no fade)')
    parser.add_argument('--fade-out', type=float, default=5.0,
                       help='Global fade out duration in seconds (default: 5.0, 0=no fade)')
    parser.add_argument('--note-fade-in', type=float, default=1.5,
                       help='Per-note fade in duration in seconds (default: 1.5, 0=instant)')
    parser.add_argument('--note-fade-out', type=float, default=2.0,
                       help='Per-note fade out duration in seconds (default: 2.0, 0=instant)')
    parser.add_argument('--drone-fade-in', type=float, default=3.0,
                       help='Drone fade in duration in seconds (default: 3.0, 0=instant)')
    parser.add_argument('--drone-fade-out', type=float, default=3.0,
                       help='Drone fade out duration in seconds (default: 3.0, 0=instant)')

    args = parser.parse_args()

    # Get the score
    if args.score:
        print(f"Loading score from: {args.score}")
        brackets = DroneScoreParser.parse_score_file(args.score)
        print(f"Loaded {len(brackets)} brackets")
    else:
        # Parse drone list and scale
        drones = args.drone.split(',')
        scale = args.scale.split(',') if args.scale else None

        # Convert dronetime from performance time to score time
        # Performance time = score time × time_scale
        # Therefore: score time = performance time / time_scale
        drone_time_score = args.dronetime / args.time_scale

        # Show what we're generating
        drone_str = ' -> '.join(drones) if len(drones) > 1 else drones[0]
        print(f"Generating score: {args.end} minutes (score time)")
        print(f"  Drone(s): {drone_str}")
        if len(drones) > 1:
            print(f"  Drone time: {args.dronetime}s per drone (performance time)")
            print(f"             = {drone_time_score:.1f}s in score time")
        print(f"  Scale: {scale or 'default'}")

        generator = DroneScoreGenerator(drones, scale, args.end, drone_time_score)
        brackets = generator.generate_score()
        print(f"Generated {len(brackets)} brackets")

    # Perform
    performer = MIDIPerformer(args.port_name, args.velocity, args.debug,
                             args.note_fade_in, args.note_fade_out,
                             args.drone_fade_in, args.drone_fade_out)
    try:
        # Wait for user to set up Ableton Live
        if not args.auto_start:
            print("\n" + "="*60)
            print("MIDI port is ready!")
            print("="*60)
            print("\nNow set up Ableton Live:")
            print("  1. Open Preferences → Link/Tempo/MIDI")
            print("  2. Enable 'Track' for the MIDI input port")
            print("  3. Create MIDI track(s) with input from this port")
            print("  4. Arm track(s) for recording if desired")
            print("  5. Start Ableton recording if desired")
            print("\nPress ENTER when ready to start the performance...")
            print("(or use --auto-start flag to skip this prompt)")
            print("="*60)
            input()
            print("\nStarting in 3...")
            time.sleep(1)
            print("2...")
            time.sleep(1)
            print("1...\n")
            time.sleep(1)

        performer.perform(brackets, args.time_scale, args.fade_in, args.fade_out)
    finally:
        performer.close()


if __name__ == '__main__':
    main()
