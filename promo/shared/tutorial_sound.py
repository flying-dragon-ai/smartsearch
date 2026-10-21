"""Score and effects for the tutorial films: a quiet lo-fi loop under synthesized UI sounds.

Usage: python3 shared/tutorial_sound.py events.json out.wav

The synthesizers and effects are film/sound.py's; this file only writes a calmer score around them.
"""
import importlib.util
import json
import pathlib
import sys
import wave

import numpy as np

_spec = importlib.util.spec_from_file_location('film_sound', pathlib.Path(__file__).resolve().parent.parent / 'film' / 'sound.py')
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

# The same four chords as the feature film, so all three films sound like one family.
PROG, ROOTS = S.PROG, S.ROOTS


def score(dur, T, bpm):
    beat = 60 / bpm
    bar = 4 * beat
    mus = np.zeros((2, int((dur + 3) * S.SR)))
    drums = np.zeros_like(mus)
    start, end = T.get('appIn', 0), T.get('end', dur)
    b = 0
    while b * bar < end:
        t0 = b * bar
        ch = PROG[b % 4]
        S.add(mus, S.chord(ch, bar * 0.95, 0.2), t0, 1.0, -0.1)
        if t0 >= start - 0.01:
            # Bass on 1 and 3, a soft kick and rim, swung hats.
            r = S.note(ROOTS[b % 4])
            S.add(mus, S.bass(r, beat * 1.6, 0.4), t0, 1.0)
            S.add(mus, S.bass(r * 1.5, beat * 0.8, 0.3), t0 + 2 * beat, 1.0)
            S.add(drums, S.kick(0.45), t0, 1.0)
            S.add(drums, S.kick(0.3), t0 + 2.5 * beat, 1.0)
            for s in (1, 3):
                S.add(drums, S.snare(0.16), t0 + s * beat, 1.0, 0.1)
            for k in range(8):
                S.add(drums, S.hat(0.06 if k % 2 else 0.09), t0 + k * beat / 2 + (0.05 if k % 2 else 0), 1.0, 0.3)
        b += 1
    # End card: a ringing chord and a slow arpeggio.
    S.add(mus, S.chord(('F3', 'A3', 'C4', 'E4', 'G4'), 3.0, 0.26), end, 1.0)
    for k, n in enumerate(('C5', 'E5', 'G5', 'B5', 'D6', 'G5', 'E5', 'C6')):
        S.add(mus, S.pluck(S.note(n), 0.5, 0.09), end + 0.4 + k * 0.38, 1.0, -0.3 + 0.08 * k)
    mus = S.reverb(mus, 2.0, 0.32)
    return mus * 0.8 + drums * 0.7


def main():
    events_path, out = sys.argv[1], sys.argv[2]
    data = json.load(open(events_path, encoding='utf-8'))
    dur, T = data['dur'], data['T']
    mix = score(dur, T, data.get('bpm') or 96)
    fx = np.zeros_like(mix)
    for e in data['events']:
        S.add(fx, S.sfx(e['type'], e['gain']), e['t'], e['gain'], e['pan'])
    fx = S.reverb(fx, 0.8, 0.1)
    master = mix * 0.75 + fx * 0.75
    n = int(dur * S.SR)
    master = master[:, :n]
    master[:, -int(0.8 * S.SR):] *= np.linspace(1, 0, int(0.8 * S.SR)) ** 2
    master = np.tanh(master * 0.9) / 0.9
    peak = np.max(np.abs(master))
    master = master / max(peak, 1e-9) * 0.89
    pcm = (np.clip(master.T, -1, 1) * 32767).astype('<i2')
    with wave.open(out, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(S.SR)
        w.writeframes(pcm.tobytes())
    print(f'{out}: {dur}s, {len(data["events"])} cues, peak {peak:.2f} before normalising')


if __name__ == '__main__':
    main()
