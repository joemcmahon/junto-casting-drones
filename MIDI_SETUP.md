# MIDI Performance Setup Guide

This guide explains how to set up and use `drone_performer.py` to perform drone scores via MIDI into Ableton Live on macOS.

## Installation

### 1. Set up Python virtual environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it (run this every time you use the script)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Make the script executable

```bash
chmod +x drone_performer.py
```

Note: Always activate the virtual environment before running the script:
```bash
source venv/bin/activate
./drone_performer.py --score performance.md
```

## macOS MIDI Setup

The script automatically creates a virtual MIDI port called "Drone Performer" that Ableton Live can receive from.

### Configure Ableton Live to receive MIDI

1. Open Ableton Live
2. Go to **Preferences** > **Link/Tempo/MIDI**
3. In the **MIDI Ports** section, find "Drone Performer" in the input ports list
4. Enable **Track** for the "Drone Performer" port
5. Click the close button to save

### Create MIDI tracks in Ableton

The performer uses multiple MIDI channels:
- **Channel 1 (0)**: Drone note (constant throughout)
- **Channels 2-16 (1-15)**: Individual harmony notes (each note gets its own channel)

You can either:

**Option A: Single track with multiple instruments**
1. Create a MIDI track
2. Set input to "Drone Performer" → "All Channels"
3. Add an Instrument Rack with multiple chains, each listening to different channels
4. Each chain can have different instruments/effects

**Option B: Multiple tracks (simpler)**
1. Create one MIDI track for the drone
   - Set MIDI From: "Drone Performer" → Channel 1
   - Add a pad/drone instrument (e.g., Analog, Wavetable)
2. Create additional tracks for harmony notes
   - Set MIDI From: "Drone Performer" → Channel 2, 3, 4, etc.
   - Add different instruments for each
3. The script will show you which notes are on which channels

**Option C: Single track (easiest)**
1. Create one MIDI track
2. Set MIDI From: "Drone Performer" → "All Channels"
3. Add any instrument - it will receive all notes
4. You won't get per-note routing, but it will work

## Usage

### Perform an existing score

```bash
# Real-time performance (60 minutes = 60 real minutes)
# The script will wait for you to press ENTER before starting
./drone_performer.py --score performance.md

# 10x faster (for testing)
./drone_performer.py --score performance.md --time-scale 0.1

# 6x faster (10-minute piece in ~100 seconds)
./drone_performer.py --score performance.md --time-scale 0.166

# Auto-start without waiting (for automation)
./drone_performer.py --score performance.md --auto-start
```

The script creates the MIDI port, then waits for you to press ENTER. This gives you time to:
- Set up MIDI routing in Ableton
- Arm tracks for recording
- Start Ableton's recording

After you press ENTER, it counts down "3... 2... 1..." then begins performing.

### Generate and perform a new score

```bash
# Generate a 20-minute piece in C whole-tone scale
./drone_performer.py --generate --end 20 --drone C1 --scale C,D,E,F#,G#,A#

# Generate and play fast (10x speed)
./drone_performer.py --generate --end 10 --time-scale 0.1

# Default A major scale, 61 minutes
./drone_performer.py --generate
```

### Additional options

```bash
# Custom fade times (in seconds)
./drone_performer.py --score performance.md --fade-in 10 --fade-out 8

# No fades (immediate start/stop)
./drone_performer.py --score performance.md --fade-in 0 --fade-out 0

# Long, subtle fade (30 seconds each)
./drone_performer.py --score performance.md --fade-in 30 --fade-out 30

# Custom MIDI port name
./drone_performer.py --score performance.md --port-name "My Drone Port"

# Adjust velocity (quieter)
./drone_performer.py --score performance.md --velocity 60

# See all options
./drone_performer.py --help
```

**Fade controls:**

Global fades (entire performance):
- `--fade-in N`: Fade in over N seconds at start (default: 5)
- `--fade-out N`: Fade out over N seconds at end (default: 5)

Per-note fades (each individual note):
- `--note-fade-in N`: Each note fades in over N seconds (default: 1.5)
- `--note-fade-out N`: Each note fades out over N seconds (default: 2.0)

All fades use MIDI CC#7 (Channel Volume) for smooth transitions. Set to 0 to disable.

**Examples:**
```bash
# Subtle, organic transitions (longer per-note fades)
./drone_performer.py --score performance.md --note-fade-in 3 --note-fade-out 4

# Quick, crisp changes (short per-note fades)
./drone_performer.py --score performance.md --note-fade-in 0.5 --note-fade-out 0.5

# No per-note fades, but keep global fades
./drone_performer.py --score performance.md --note-fade-in 0 --note-fade-out 0
```

## Performance Controls

The script shows real-time status with:
- **Note changes**: When notes start/stop, shows which notes and their MIDI channels
- **Live ticker**: Updates every second showing elapsed time in current bracket
- **Visual indicator**: Animated dots show the performance is running

Example output:
```
[   2.0s] 02:00 Playing A1 (drone) + E3 F#3 F#4
            Started: E3 (ch2), F#3 (ch3), F#4 (ch4)
[   4.2s] Playing for  2.2s / 120.0s ...
```

The ticker line updates in place every second. When notes change, a new section prints.

- **Stop performance**: Press `Ctrl+C` - the script will gracefully stop all notes

## Troubleshooting

### "python-rtmidi not installed" error

Make sure you've activated the virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Ableton not receiving MIDI

**Important**: Each time you restart the script, the virtual MIDI port is recreated. Ableton may need to reconnect:

1. **After restarting the script**: Go to Ableton's MIDI preferences and check "Drone Performer"
2. If the port shows as disconnected (grayed out), toggle it off and back on
3. Verify your MIDI track's input is still set to "Drone Performer"
4. Some versions of Ableton auto-reconnect, others require manual reconnection

**Quick test with debug mode**:
```bash
./drone_performer.py --generate --end 2 --time-scale 0.1 --debug --auto-start
```

This will show every MIDI message being sent. You should see output like:
```
[MIDI] Note ON:  A1   = MIDI# 33 on channel  1 (vel=80) -> [144, 33, 80]
[MIDI] Note ON:  E3   = MIDI# 52 on channel  2 (vel=80) -> [145, 52, 80]
```

If you see these messages but Ableton isn't receiving them:
1. Check that "Drone Performer" is enabled in Ableton's MIDI preferences
2. Make sure your MIDI track(s) input is set correctly
3. Try toggling the "Track" checkbox off and on in MIDI preferences
4. Create a simple MIDI track with input "Drone Performer" → "All Channels" to test

### Port already in use

If you see an error about the port being in use:
1. Close any other running instances of `drone_performer.py`
2. Try using a different port name: `--port-name "Drone Performer 2"`

### Notes sustaining after stopping

The script should send note-off messages when stopped, but if notes sustain:
1. In Ableton, press the panic button (usually in the MIDI track)
2. Or send MIDI panic: Go to a MIDI track and use the "All Notes Off" function

## Tips for Better Performance

### Recording in Ableton

1. **Start the script**: Run `./drone_performer.py --score performance.md`
2. **Wait at the prompt**: The script creates the MIDI port and waits
3. **Set up Ableton**: Create MIDI tracks with input from "Drone Performer"
4. **Arm tracks**: Arm the MIDI track(s) you want to record
5. **Start Ableton recording**: Click the record button in Ableton
6. **Press ENTER**: In the terminal, press ENTER to start the performance
7. **Countdown**: The script counts "3... 2... 1..." then begins
8. **Let it play**: The script handles all note changes automatically
9. When done, you'll have MIDI clips you can edit in Ableton

### Time Scaling Strategies

- `--time-scale 1.0`: Real-time, use for actual performances
- `--time-scale 0.1`: 10x faster, great for quick testing (6-minute performance of a 60-minute piece)
- `--time-scale 0.5`: 2x faster, still musical but quicker
- `--time-scale 0.05`: 20x faster, very quick preview (3 minutes for a 60-minute piece)

### Creating Variations

Each time you run with `--generate`, you get a different score:
```bash
# Generate several variations quickly
./drone_performer.py --generate --end 10 --time-scale 0.1

# When you hear one you like, save it by redirecting stderr
./drone_performer.py --generate --end 60 2> my_score.txt
```

## Architecture Notes

The script uses:
- **Channel 0 (MIDI channel 1)**: Constant drone note
- **Channels 1-15 (MIDI channels 2-16)**: Individual notes, dynamically allocated
- Each unique note gets a consistent channel throughout the performance
- Notes are sent as MIDI Note On/Off messages with configurable velocity

## Examples

### Quick test of existing score
```bash
./drone_performer.py --score performance.md --time-scale 0.05
```

### Generate a short ambient piece
```bash
./drone_performer.py --generate --end 5 --drone E1 --scale E,F#,G#,A,B --time-scale 1.0
```

### Record a full performance
```bash
# In Ableton: Set up instruments and arm tracks
# Then run:
./drone_performer.py --score performance.md --time-scale 1.0
```
