#!/usr/bin/env python3
"""Score and sound effects for 同一个问题, synthesized from the cue list in events.json.

    python3 film/sound.py out/film/events.json out/film/mix_raw.wav

Music follows the picture's sections (times in events.json["T"]): a soft intro, a tape stop into a
"buffering" loop while the built-in side is stuck, a rebuild at the upgrade, a 120 BPM groove for the
three rounds, a break for the merge and an impact into the end card. Every cue type maps to one
synthesized sound; pan places it on the side of the split where it happens.
"""
import json
import sys
import wave

import numpy as np
from scipy import signal

SR = 48000
RNG = np.random.default_rng(7)


def secs(n):
    return np.arange(int(n * SR)) / SR


def note(name):
    """'A4' → Hz."""
    steps = {'C': -9, 'D': -7, 'E': -5, 'F': -4, 'G': -2, 'A': 0, 'B': 2}
    n = steps[name[0]] + (1 if '#' in name else -1 if 'b' in name[1:2] else 0)
    octave = int(name[-1])
    return 440.0 * 2 ** ((n + 12 * (octave - 4)) / 12)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype='band', fs=SR, output='sos')
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype='low', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype='high', fs=SR, output='sos'), x)


def noise(n):
    return RNG.standard_normal(int(n * SR))


# ---------------------------------------------------------------- instruments
def ep(freq, dur, vel=0.5):
    """Electric piano: two-operator FM with a fading bell partial."""
    t = secs(dur + 0.9)
    idx = 1.6 * np.exp(-t * 5) + 0.15
    tone = np.sin(2 * np.pi * freq * t + idx * np.sin(2 * np.pi * freq * t))
    tone += 0.18 * np.sin(2 * np.pi * freq * 4.0 * t) * np.exp(-t * 14)
    amp = np.exp(-t * 1.1) * np.minimum(1, t / 0.004)
    amp *= np.where(t < dur, 1, np.exp(-(t - dur) * 7))
    return vel * tone * amp


def chord(names, dur, vel=0.32, spread=0.012):
    parts = [np.pad(ep(note(n), dur, vel), (int(i * spread * SR), 0)) for i, n in enumerate(names)]
    out = np.zeros(max(len(p) for p in parts))
    for p in parts:
        out[:len(p)] += p
    return out


def bass(freq, dur, vel=0.55):
    t = secs(dur + 0.08)
    saw = signal.sawtooth(2 * np.pi * freq * t)
    tone = 0.7 * np.sin(2 * np.pi * freq * t) + 0.3 * lp(saw, 900)
    amp = np.minimum(1, t / 0.006) * np.exp(-t * 2.2) * np.where(t < dur, 1, np.exp(-(t - dur) * 40))
    return vel * tone * amp


def pluck(freq, dur=0.35, vel=0.3):
    t = secs(dur)
    tone = signal.square(2 * np.pi * freq * t, 0.3) * 0.5 + np.sin(2 * np.pi * freq * t)
    return vel * lp(tone, 3500) * np.exp(-t * 9) * np.minimum(1, t / 0.003)


def kick(vel=0.9):
    t = secs(0.45)
    f = 46 + 110 * np.exp(-t * 32)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    click = hp(noise(0.45), 2500) * np.exp(-t * 300) * 0.25
    return vel * (body + click)


def snare(vel=0.6):
    t = secs(0.3)
    return vel * (0.8 * bp(noise(0.3), 1200, 7000) * np.exp(-t * 17) + 0.5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 26))


def hat(vel=0.2, open_=False):
    d = 0.35 if open_ else 0.08
    t = secs(d)
    return vel * hp(noise(d), 7500) * np.exp(-t * (11 if open_ else 55))


def clap(vel=0.45):
    t = secs(0.3)
    env = sum(np.exp(-np.maximum(t - o, 0) * 90) * (t >= o) for o in (0, 0.011, 0.023)) + 0.4 * np.exp(-np.maximum(t - 0.03, 0) * 14) * (t >= 0.03)
    return vel * bp(noise(0.3), 900, 3500) * env


def crash(vel=0.35, dur=1.8):
    t = secs(dur)
    return vel * hp(noise(dur), 4500) * np.exp(-t * 2.4) * np.minimum(1, t / 0.002)


def tom(freq=140, vel=0.55):
    t = secs(0.35)
    f = freq * (1 + 0.5 * np.exp(-t * 20))
    return vel * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def bell(freq, dur=0.6, vel=0.3, ratio=1.4):
    t = secs(dur)
    return vel * np.sin(2 * np.pi * freq * t + 2.2 * np.exp(-t * 6) * np.sin(2 * np.pi * freq * ratio * t)) * np.exp(-t * 5) * np.minimum(1, t / 0.002)


def sweep(f0, f1, dur, wave='sine'):
    t = secs(dur)
    f = f0 * (f1 / f0) ** (t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return signal.square(ph, 0.5) if wave == 'square' else np.sin(ph)


# ---------------------------------------------------------------- sound effects
def sfx(kind, g=1.0):
    if kind == 'key':
        t = secs(0.05)
        f = RNG.uniform(2200, 3400)
        return 0.5 * (hp(noise(0.05), 1800) * np.exp(-t * 260) + 0.4 * np.sin(2 * np.pi * f * t) * np.exp(-t * 200))
    if kind == 'enter':
        t = secs(0.14)
        return 0.9 * (bp(noise(0.14), 600, 4000) * np.exp(-t * 90) + 0.6 * np.sin(2 * np.pi * 140 * t) * np.exp(-t * 40))
    if kind == 'blip':
        return 0.35 * sweep(880, 1320, 0.07) * np.exp(-secs(0.07) * 25)
    if kind == 'tick':
        t = secs(0.05)
        return 0.6 * lp(np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 90), 2500)
    if kind == 'thud':
        t = secs(0.25)
        return 0.9 * (np.sin(2 * np.pi * 95 * t) * np.exp(-t * 18) + 0.3 * lp(noise(0.25), 400) * np.exp(-t * 25))
    if kind == 'squeak':
        t = secs(0.18)
        return 0.25 * np.sin(2 * np.pi * np.cumsum(1250 + 260 * np.sin(2 * np.pi * 28 * t)) / SR) * np.sin(np.pi * t / 0.18)
    if kind == 'sad':
        # Two drooping notes, a little "wah wah".
        out = np.zeros(int(0.9 * SR))
        for i, (a, b) in enumerate(((392, 370), (349, 311))):
            t = secs(0.4)
            f = a + (b - a) * (t / 0.4)
            v = lp(signal.sawtooth(2 * np.pi * np.cumsum(f) / SR), 1200) * np.sin(np.pi * t / 0.4) ** 0.6
            out[int(i * 0.42 * SR):int(i * 0.42 * SR) + len(v)] += 0.28 * v
        return out
    if kind == 'rip':
        t = secs(0.5)
        crackle = (RNG.random(len(t)) < 0.08) * RNG.uniform(0.3, 1, len(t))
        crackle = np.convolve(crackle, np.ones(40) / 40, mode='same')
        return 1.6 * bp(noise(0.5), 1200, 6000) * crackle * np.exp(-t * 3) * np.minimum(1, t / 0.02)
    if kind == 'boing':
        return 0.22 * sweep(300, 950, 0.16, 'square') * np.exp(-secs(0.16) * 6)
    if kind == 'land':
        t = secs(0.16)
        return 0.7 * (np.sin(2 * np.pi * 120 * t) * np.exp(-t * 30) + 0.25 * bp(noise(0.16), 300, 2000) * np.exp(-t * 50))
    if kind == 'pop':
        t = secs(0.09)
        return 0.45 * np.sin(2 * np.pi * np.cumsum(520 + 700 * (t / 0.09)) / SR) * np.exp(-t * 35)
    if kind == 'upgrade':
        out = np.zeros(int(1.2 * SR))
        for i, n in enumerate(('C6', 'E6', 'G6', 'C7')):
            v = bell(note(n), 0.7, 0.2, 2.0)
            out[int(i * 0.06 * SR):int(i * 0.06 * SR) + len(v)] += v
        t = secs(1.2)
        out += 0.18 * hp(noise(1.2), 6000) * np.exp(-t * 3) * np.minimum(1, t / 0.05)
        return out
    if kind == 'go':
        t = secs(0.9)
        stab = sum(lp(signal.sawtooth(2 * np.pi * note(n) * t), 2500) for n in ('C4', 'E4', 'G4', 'C5')) * 0.12 * np.exp(-t * 4)
        return np.concatenate([kick(1.0), np.zeros(int(0.45 * SR))])[:len(t)] + stab + crash(0.3, 0.9)
    if kind == 'slam':
        out = kick(0.9) + np.pad(snare(0.5), (0, len(kick()) - len(snare())))
        return np.concatenate([out, np.zeros(int(0.5 * SR))]) + np.pad(tom(110, 0.5), (0, len(out) + int(0.5 * SR) - len(tom())))
    if kind == 'stream':
        t = secs(1.4)
        flutter = 0.5 + 0.5 * signal.square(2 * np.pi * 22 * t + 3 * np.sin(2 * np.pi * 3 * t))
        return 0.12 * bp(noise(1.4), 2500, 7000) * flutter * np.sin(np.pi * t / 1.4)
    if kind == 'whoosh':
        t = secs(0.45)
        x = noise(0.45)
        # band-pass that rises through the swell
        y = np.concatenate([bp(x[i:i + 2400], 300 + 6 * i / 48, 900 + 12 * i / 48) for i in range(0, len(x), 2400)])[:len(x)]
        return 0.8 * y * np.sin(np.pi * t / 0.45) ** 2
    if kind == 'ching':
        return bell(2093, 0.6, 0.28, 1.41) + bell(3136, 0.6, 0.12, 1.41)
    if kind == 'step':
        t = secs(0.03)
        return 0.18 * signal.square(2 * np.pi * 620 * t) * np.exp(-t * 120)
    if kind == 'marker':
        t = secs(1.4)
        return 0.22 * bp(noise(1.4), 2500, 6500) * np.minimum(1, t / 0.15) * np.exp(-np.maximum(t - 1.1, 0) * 12)
    if kind == 'chime':
        return bell(note('E6'), 0.7, 0.18)
    if kind == 'stamp':
        t = secs(0.35)
        return 1.0 * (np.sin(2 * np.pi * 70 * t) * np.exp(-t * 14) + 0.45 * lp(noise(0.35), 900) * np.exp(-t * 30) + 0.3 * bp(noise(0.35), 1500, 4000) * np.exp(-t * 80))
    if kind == 'success':
        a, b = bell(note('G5'), 0.5, 0.22, 2.0), bell(note('C6'), 0.8, 0.26, 2.0)
        out = np.zeros(int(1.0 * SR))
        out[:len(a)] += a
        out[int(0.12 * SR):int(0.12 * SR) + len(b)] += b
        return out
    if kind == 'buzz':
        t = secs(0.4)
        return 0.22 * lp(signal.square(2 * np.pi * 138 * t) + signal.square(2 * np.pi * 146 * t), 1500) * np.minimum(1, t / 0.01) * np.exp(-np.maximum(t - 0.3, 0) * 30)
    if kind == 'tickok':
        t = secs(0.08)
        return 0.3 * (np.sin(2 * np.pi * 1568 * t) + 0.5 * np.sin(2 * np.pi * 2349 * t)) * np.exp(-t * 45)
    if kind == 'riser':
        t = secs(1.6)
        x = hp(noise(1.6), 2000) * (t / 1.6) ** 2 * 0.35
        x += 0.12 * sweep(200, 1600, 1.6) * (t / 1.6) ** 1.5
        return x
    if kind == 'impact':
        t = secs(2.2)
        sub = np.sin(2 * np.pi * np.cumsum(60 * np.exp(-t * 1.2) + 28) / SR) * np.exp(-t * 2.2)
        k = np.pad(kick(1.0), (0, len(t) - len(kick())))
        return 0.9 * sub + k + crash(0.45, 2.2)
    if kind == 'sparkle':
        out = np.zeros(int(0.9 * SR))
        for i in range(7):
            v = bell(RNG.uniform(3000, 6000), 0.25, 0.07, 1.5)
            o = int(RNG.uniform(0, 0.6) * SR)
            out[o:o + len(v)] += v
        return out
    if kind == 'peek':
        return 0.3 * sweep(600, 950, 0.12) * np.exp(-secs(0.12) * 10)
    if kind == 'click':
        # A soft mouse click: press and release, low-passed so it doesn't spike the peaks.
        t = secs(0.06)
        down = lp(hp(noise(0.06), 2000), 7000) * np.exp(-t * 400)
        up = np.pad(lp(hp(noise(0.03), 2500), 7000) * np.exp(-secs(0.03) * 500), (int(0.035 * SR), 0))[:len(t)]
        return 0.32 * down + 0.18 * up + 0.12 * np.sin(2 * np.pi * 1900 * t) * np.exp(-t * 300)
    if kind == 'meter':
        # A bar filling up: the higher the probability (carried in the cue's gain), the higher it climbs.
        p = min(1.0, max(0.0, (g - 0.35) / 0.5))
        t = secs(0.24)
        return 0.3 * sweep(420, 700 + 900 * p, 0.24) * np.minimum(1, t / 0.01) * np.exp(-t * 7) + np.pad(sfx('tick') * 0.4, (int(0.2 * SR), 0))[:len(t)]
    if kind == 'select':
        out = np.zeros(int(0.9 * SR))
        a, b = bell(note('E6'), 0.7, 0.24, 2.0), bell(note('B6'), 0.6, 0.14, 2.0)
        out[:len(a)] += a
        out[int(0.05 * SR):int(0.05 * SR) + len(b)] += b
        pp = sfx('pop')
        out[:len(pp)] += pp
        return out
    if kind == 'tapestop':
        return np.zeros(1)   # applied to the music bus instead
    raise ValueError(kind)


# ---------------------------------------------------------------- mixing helpers
def add(bus, x, t, gain=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= bus.shape[1] or i + len(x) <= 0:
        return
    x = x[max(0, -i):]
    i = max(0, i)
    n = min(len(x), bus.shape[1] - i)
    a = (pan + 1) * np.pi / 4
    bus[0, i:i + n] += gain * np.cos(a) * x[:n]
    bus[1, i:i + n] += gain * np.sin(a) * x[:n]


def reverb(x, seconds=1.6, mix=0.25):
    """Stereo FFT convolution with decaying noise as the impulse response."""
    t = secs(seconds)
    out = np.zeros_like(x)
    for ch in range(2):
        ir = RNG.standard_normal(len(t)) * np.exp(-t * 4.2)
        ir = lp(ir, 6000)
        ir /= np.sqrt(np.sum(ir ** 2))
        out[ch] = signal.fftconvolve(x[ch], ir)[:x.shape[1]]
    return x + mix * out


def tape_stop(bus, t0, dur=0.45):
    """Slow the bus down to a halt from t0, then silence it for a beat."""
    i0, n = int(t0 * SR), int(dur * SR)
    src = bus[:, i0:i0 + n * 2].copy()
    speed = np.linspace(1, 0, n) ** 1.3
    pos = np.cumsum(speed)
    for ch in range(2):
        bus[ch, i0:i0 + n] = np.interp(pos, np.arange(src.shape[1]), src[ch]) * np.linspace(1, 0.2, n)
    bus[:, i0 + n:i0 + n + int(0.25 * SR)] = 0


# ---------------------------------------------------------------- the score
PROG = [('F3', 'A3', 'C4', 'E4'), ('E3', 'G3', 'B3', 'D4'), ('D3', 'F3', 'A3', 'C4'), ('C3', 'E3', 'G3', 'B3')]
ROOTS = ['F2', 'E2', 'D2', 'C2']
MOTIF = ['E5', 'G5', 'A5', 'G5', 'E5', 'D5', 'C5', 'D5']


def score(dur, T):
    beat, bar = 0.5, 2.0
    mus = np.zeros((2, int((dur + 2) * SR)))
    drums = np.zeros_like(mus)

    # Intro: soft chords and a shaker, no kick.
    for b in range(2):
        add(mus, chord(PROG[b], 1.9, 0.26), b * bar, 1.0, -0.1)
        for k in range(8):
            add(drums, hat(0.08), b * bar + k * beat / 2 + (0.03 if k % 2 else 0), 1.0, 0.3)
    tape_stop(mus, T['stuck'])
    tape_stop(drums, T['stuck'])

    # Stuck: a muffled Dm7 stab that keeps stalling, panned left.
    stuck = np.zeros_like(mus)
    t = T['stuck'] + 0.7
    i = 0
    while t < T['upgrade']:
        if i % 5 not in (3, 4):
            add(stuck, chord(PROG[2], 0.18, 0.2, 0.0), t, 1.0, -0.5)
        t += beat / 2
        i += 1
    crushed = np.round(lp(stuck, 1100) * 24) / 24
    mus += crushed * 0.8

    # Rebuild: snare roll from the split to the upgrade, a fill into GO.
    n_roll = int((T['upgrade'] - (T['split'] + 1.0)) / 0.0625)
    for k in range(n_roll):
        tt = T['split'] + 1.0 + k * 0.0625
        add(drums, snare(0.08 + 0.35 * k / n_roll), tt, 1.0, 0.3)
    add(mus, chord(('C4', 'E4', 'G4', 'B4'), 1.0, 0.25), T['upgrade'], 1.0, 0.3)
    for k, f in enumerate((180, 160, 140, 120)):
        add(drums, tom(f, 0.4), T['ready'] + k * beat / 2, 1.0, -0.4 + 0.25 * k)

    def groove(b0, b1, claps=False, lead=False, octave=False):
        for b in range(b0, b1):
            t0 = b * bar
            ch = PROG[b % 4]
            add(drums, kick(0.85), t0)
            add(drums, kick(0.6), t0 + 1.5 * beat)
            add(drums, kick(0.75), t0 + 2 * beat)
            for s in (1, 3):
                add(drums, snare(0.5), t0 + s * beat, 1.0, 0.05)
                if claps:
                    add(drums, clap(0.32), t0 + s * beat + 0.005, 1.0, -0.2)
            for k in range(8):
                add(drums, hat(0.13 if k % 2 == 0 else 0.08, open_=(k == 7)), t0 + k * beat / 2 + (0.04 if k % 2 else 0), 1.0, 0.35)
            # Bass: root on 1, a push before 3, fifth-ish walk at the end of the bar.
            r = note(ROOTS[b % 4])
            add(mus, bass(r, 0.42), t0, 1.0)
            add(mus, bass(r, 0.2, 0.45), t0 + 1.5 * beat, 1.0)
            add(mus, bass(r, 0.42), t0 + 2 * beat, 1.0)
            add(mus, bass(r * 1.5, 0.2, 0.4), t0 + 3.5 * beat, 1.0)
            # Chords on the offbeats.
            for k in (0.5, 2.5):
                add(mus, chord(ch, 0.3, 0.2), t0 + k * beat, 1.0, -0.15)
            if lead:
                for k, n in enumerate(MOTIF):
                    if (b + k) % 3 == 2:
                        continue
                    f = note(n) * (2 if octave else 1)
                    add(mus, pluck(f, 0.3, 0.14), t0 + k * beat / 2, 1.0, 0.25)

    # Four rounds, three bars each; every bar index comes from the timetable.
    b_route, b_r1, b_r2, b_r3, b_merge, b_end = (round(T[k] / bar) for k in ('route', 'r1', 'r2', 'r3', 'merge', 'end'))
    groove(b_route, b_r1)                                  # round 1: routing
    # While Jev scores the channels, a quiet sixteenth-note arpeggio "computes".
    t, k = T['bars'], 0
    while t < T['pick']:
        add(mus, pluck(note(('A4', 'C5', 'E5', 'G5')[k % 4]) * (2 if k % 8 >= 4 else 1), 0.18, 0.07), t, 1.0, 0.35)
        t += beat / 4
        k += 1
    add(drums, crash(0.22, 1.2), T['pick'], 1.0, 0.3)
    groove(b_r1, b_r2, lead=True)                          # round 2: search
    groove(b_r2, b_r3, lead=True)                          # round 3: read
    groove(b_r3, b_merge, claps=True, lead=True, octave=True)   # round 4: answer
    for r in (T['route'], T['r1'], T['r2'], T['r3']):
        add(drums, crash(0.3), r, 1.0, 0.1)

    # Merge: a break on a held chord, a riser into the cheer.
    add(mus, chord(('D3', 'F3', 'A3', 'C4', 'E4'), 1.6, 0.28), T['merge'], 1.0)
    add(mus, sfx('riser') * 0.7, T['jump'] - 0.6, 1.0)
    groove(b_merge + 1, b_end, claps=True, lead=True)      # cheer and montage
    add(drums, crash(0.35), (b_merge + 1) * bar, 1.0, -0.1)

    # End card: impact, then a ringing chord and a slow arpeggio.
    add(mus, chord(('F3', 'A3', 'C4', 'E4', 'G4'), 2.4, 0.3), T['end'], 1.0)
    add(mus, chord(('C3', 'E3', 'G3', 'B3', 'D4'), 2.4, 0.3), T['end'] + 2.2, 1.0)
    for k, n in enumerate(('C5', 'E5', 'G5', 'B5', 'D6', 'G5', 'E5', 'C6')):
        add(mus, pluck(note(n), 0.5, 0.11), T['end'] + 0.5 + k * 0.4, 1.0, -0.3 + 0.08 * k)

    mus = reverb(mus, 1.8, 0.3)
    return mus * 0.85 + drums * 0.9


def main():
    events_path, out = sys.argv[1], sys.argv[2]
    data = json.load(open(events_path, encoding='utf-8'))
    dur, T = data['dur'], data['T']
    mix = score(dur, T)
    fx = np.zeros_like(mix)
    for e in data['events']:
        if e['type'] == 'tapestop':
            continue
        add(fx, sfx(e['type'], e['gain']), e['t'], e['gain'], e['pan'])
    fx = reverb(fx, 1.0, 0.12)
    master = mix * 0.62 + fx * 0.9
    # Fade out the tail, soft-clip, write 16-bit stereo; loudness is set later with ffmpeg loudnorm.
    n = int(dur * SR)
    master = master[:, :n]
    master[:, -int(0.8 * SR):] *= np.linspace(1, 0, int(0.8 * SR)) ** 2
    master = np.tanh(master * 0.9) / 0.9
    peak = np.max(np.abs(master))
    master = master / max(peak, 1e-9) * 0.89
    pcm = (np.clip(master.T, -1, 1) * 32767).astype('<i2')
    with wave.open(out, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f'{out}: {dur}s, {len(data["events"])} cues, peak {peak:.2f} before normalising')


if __name__ == '__main__':
    main()
