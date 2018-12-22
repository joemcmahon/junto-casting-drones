# Disquiet Junto 364: Casting Drones

This script, when run, generates a "score" for a drone for the Disquiet Junto's
"Casting Drones" project. The score is made up of _brackets_, each 1 to 3 minutes
long. Each bracket describes what should be happening during that bracket. Notes
on what is changing between the current bracket and the next are printed after
each bracket.

 - Bracket lines give a time offset and the notes that should currently be playing:

    xx:00 Playing dd (drone) + N1 N2...NN  for y minutes

 - Change lines describe the change to be done to transform the current bracket into the next. Note that only one of the lines will be seen for any one bracket-to-bracket change:
 
 -- `Adding n notes: N1..NN`: From 1 to 4 notes will be added to the notes already playing
 -- `Dropping one note: N1`: The designated note should stop playing
 -- `Dropping two notes: N1 and N2`: Both the designated notes should stop playing
 -- `Changing x notes: N1 (drop O1)...Nx (drop Ox)`: From 1 to 4 notes will change; the old note should stop playing and the new note should begin playing

## Command line switches

 - `--end=nn` denotes the minute at which the piece should end. Default is 61 minutes (the length needed to be used on the Dronecast podcast).
 - `--delay=nn` sets the delay scaling for the script to print out the score. Default is zero (print without pauses). If you choose a non-zero value, you can simulate a performance of the script, time-compressed, up to `--delayscale=60`, which is real-time.
 - `--drone` specifies the drone note. This should be a note in the English standard A..G range; sharps and flats are permitted, using `#` for sharp and `b` for flat. (Double-sharps and double-flats are supported, but give the musicians a break!) This note will be notated in the `1` octave (`A1`, `C#1`, `Eb1`, etc.).
 - `--scale` specifies the scale. Use the same note specification as for the `--drone` note, except you may specify any number of distinct notes; the program will automatically scale these in octaves 3..5 to eliminate low-register beating. Examples: `--scale=A,B,C#,D,E,F#,G#` or `--scale=C,D,E,F#,G#,A#`)

A `fade in` line at 0:00 is printed to indicate the start of the piece and a `fade out` line at the `--end` minute indicates the end.

# Example output

This command line defines a 20-minute drone using the C whole-tone scale:

    ./casting.pl --end=20 --scale=C,D,E,F#,G#,A# --drone=C

Output looks similar to this (remember the score is randomly generated):

		00:00 fade in
		00:00 Playing C (drone) + nothing for 2 minutes
					Add 1 notes: D4
		02:00 Playing C (drone) + D4 for 1 minute
					Add 3 notes: A#4 C4 F#5
		03:00 Playing C (drone) + A#4 C4 D4 F#5 for 2 minutes
					Change 4 notes: G#3 (drop D4) D3 (drop F#5) F#5 (drop A#4) E5 (drop C4)
		05:00 Playing C (drone) + D3 G#3 E5 F#5 for 2 minutes
					Change 1 notes: A#5 (drop G#3)
		07:00 Playing C (drone) + D3 A#5 E5 F#5 for 1 minute
					Change 1 notes: C5 (drop D3)
		08:00 Playing C (drone) + A#5 C5 E5 F#5 for 1 minute
					Change 1 notes: D4 (drop F#5)
		09:00 Playing C (drone) + D4 A#5 C5 E5 for 3 minutes
					Change 2 notes: G#4 (drop E5) E3 (drop A#5)
		12:00 Playing C (drone) + E3 D4 G#4 C5 for 1 minute
					Drop one note: C5
		13:00 Playing C (drone) + E3 D4 G#4 for 2 minutes
					Change 3 notes: F#4 (drop D4) F#3 (drop G#4) E4 (drop E3)
		15:00 Playing C (drone) + F#3 E4 F#4 for 2 minutes
					Change 3 notes: F#5 (drop F#4) D3 (drop F#3) C5 (drop E4)
		17:00 Playing C (drone) + D3 C5 F#5 for 2 minutes
					Change 3 notes: E4 (drop F#5) D4 (drop D3) D5 (drop C5)
		19:00 Playing C (drone) + D4 E4 D5 for 1 minute
		20:00 fade out
