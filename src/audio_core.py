"""Musical event and MIDI utilities for v1_1000 Primes."""
from __future__ import annotations
import csv
import math
import struct

# Concurrency checks use this time grid; no waveform files are rendered.
SR = 48000
PENT = [0, 2, 4, 7, 9]
CHORDS = {"C": (36, 40, 43), "Am": (33, 36, 40),
          "F": (29, 33, 36), "G": (31, 35, 38)}

def primes_up_to(limit: int) -> list[int]:
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for p in range(2, math.isqrt(limit) + 1):
        if sieve[p]:
            sieve[p*p:limit+1:p] = b"\x00" * (((limit-p*p)//p) + 1)
    return [p for p in range(2, limit + 1) if sieve[p]]

def varlen(n: int) -> bytes:
    out = [n & 0x7f]
    while n >> 7:
        n >>= 7
        out.insert(0, 0x80 | (n & 0x7f))
    return bytes(out)

def frequency(note):
    return 440*2**((note-69)/12)

def midi(path, parts):
    tracks = []
    for channel, (label, program, notes) in enumerate(parts):
        label_bytes = label.encode("ascii")
        events = [(0, b"\xff\x03"+varlen(len(label_bytes))+label_bytes),
                  (0, bytes([0xc0|channel, program]))]
        if channel == 0:
            events.append((0, b"\xff\x51\x03\x07\xa1\x20"))
        for n in notes:
            start = round(n["onset_s"]*960)
            end = round(n["end_s"]*960)
            events.extend([(start, bytes([0x90|channel, n["midi_note"], n["velocity"]])),
                           (end, bytes([0x80|channel, n["midi_note"], 0]))])
        track, previous = bytearray(), 0
        for tick, message in sorted(events, key=lambda e: (e[0], e[1])):
            track.extend(varlen(tick-previous)+message)
            previous = tick
        track.extend(b"\x00\xff\x2f\x00")
        tracks.append(b"MTrk"+struct.pack(">I", len(track))+track)
    path.write_bytes(b"MThd"+struct.pack(">IHHH",6,1,len(tracks),480)+b"".join(tracks))

def max_notes(events):
    bounds = [(round(e["onset_s"]*SR),1) for e in events]
    bounds += [(round(e["onset_s"]*SR)+round(e["duration_s"]*SR),-1) for e in events]
    active = peak = 0
    for _, delta in sorted(bounds):
        active += delta
        peak = max(peak, active)
    assert active == 0
    return peak

def table(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
