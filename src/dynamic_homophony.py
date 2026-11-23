"""v1_1000 Primes: offline data-driven prime melody and zero-field harmony.

Exports two-track MIDI and numerical records only. Python standard library.
All input and output paths are resolved within this project directory.
"""
from __future__ import annotations
import argparse
import bisect
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import uuid

import audio_core as audio
import render_core as renderer
import zero_field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "v1_1000 Primes"
SCALE = 27/209
HARMONY_SECONDS = 3.9

def first_primes(count):
    if count < 2:
        raise ValueError("At least two primes are required")
    bound = max(20,round(count*(math.log(count)+math.log(max(2,math.log(count)))))+30)
    while True:
        primes = audio.primes_up_to(bound)
        if len(primes) >= count:
            return primes[:count]
        bound *= 2

def prime_notes(count,scale=SCALE):
    primes = first_primes(count)
    notes = []
    for i,p in enumerate(primes):
        onset = .8+(p-2)*scale
        gap = p-primes[i-1] if i else 1
        degree = gap//2
        pitch = 60+12*(degree//5)+audio.PENT[degree%5]
        if not 0 <= pitch <= 127:
            raise ValueError("Prime-gap pitch exceeds MIDI range")
        next_onset = .8+(primes[i+1]-2)*scale if i+1 < count else onset+.9
        length = min(.36,.78*(next_onset-onset))
        notes.append(dict(voice="prime",prime_index=i+1,prime=p,gap=gap,
                          onset_s=onset,duration_s=length,end_s=onset+length,
                          midi_note=pitch,frequency_hz=audio.frequency(pitch),
                          velocity=78,gain=.86,pan=-.12,instrument="soft_pluck"))
    return primes,notes,notes[-1]["onset_s"]+2.2

def analysis_windows(primes,notes,duration,scale=SCALE):
    starts = []
    k = 0
    while .5+HARMONY_SECONDS*k <= notes[-1]["onset_s"]:
        starts.append(.5+HARMONY_SECONDS*k)
        k += 1
    records = []
    xmax = primes[-1]
    for k,onset in enumerate(starts):
        end = starts[k+1]-.18 if k+1 < len(starts) else duration-.65
        a = max(2,min(xmax,2+(onset-.8)/scale))
        b = max(2,min(xmax,2+(end-.8)/scale))
        if b-a < 1e-9:
            a = max(2,b-HARMONY_SECONDS/scale)
        assert a < b
        records.append(dict(chord_index=k+1,onset_s=onset,end_s=end,
                            analysis_x_start=a,analysis_x_end=b))
    return records

def build_score(count,cache,tolerance=.002,scale=SCALE):
    primes,notes,duration = prime_notes(count,scale)
    records = analysis_windows(primes,notes,duration,scale)
    windows = [(r["analysis_x_start"],r["analysis_x_end"]) for r in records]
    gammas,fields,truth,selection = zero_field.adaptive_field(
        primes,windows,cache,scale,HARMONY_SECONDS,tolerance)
    sorted_field = sorted(fields)
    palette = ["C","Am","F","G"]
    pads,chords = [],[]
    previous = None
    for k,(r,field,reference) in enumerate(zip(records,fields,truth)):
        rank = (bisect.bisect_left(sorted_field,field)+.5)/len(sorted_field)
        target = palette[min(3,int(4*rank))]
        local = [n for n in notes if r["onset_s"] <= n["onset_s"] < r["end_s"]]
        def musical_cost(name):
            pcs = {p%12 for p in audio.CHORDS[name]}
            cost = sum(0 if n["midi_note"]%12 in pcs else 1 for n in local)
            cost += sum(1.5 for n in local for p in audio.CHORDS[name]
                        if (n["midi_note"]-p)%12 in {1,6,11})
            cost /= max(1,len(local))
            cost += 0 if name == target else 1.5
            cost += .15 if name == previous else 0
            return cost
        name = min(palette,key=lambda c:(musical_cost(c),c))
        triad = audio.CHORDS[name]
        voicing = [triad[0]+12,triad[2]+12]
        chords.append(dict(r,chord=name,target_chord=target,
                           normalized_zero_field=field,prime_power_reference=reference,
                           normalized_log_window_error=field-reference,
                           field_empirical_quantile=rank,zero_index_first=1,
                           zero_index_last=len(gammas),gamma_max=gammas[-1],
                           all_selected_zeros_contribute=True,midi_notes=voicing,
                           musical_override=name != target,
                           override_reason="melody compatibility" if name != target else "none"))
        for j,pitch in enumerate(voicing):
            pads.append(dict(voice="zero_accompaniment",chord=name,
                             onset_s=r["onset_s"],end_s=r["end_s"],
                             duration_s=r["end_s"]-r["onset_s"],midi_note=pitch,
                             frequency_hz=audio.frequency(pitch),velocity=42,
                             gain=.125,pan=-.28 if j == 0 else .28,instrument="warm_pad"))
        previous = name
    return primes,notes,pads,chords,duration,gammas,selection


def project_path(path):
    """Resolve CLI paths inside this project, independently of the caller's cwd."""
    path = Path(path)
    resolved = (path if path.is_absolute() else PROJECT_ROOT/path).resolve()
    if not resolved.is_relative_to(PROJECT_ROOT):
        raise ValueError("Input and output paths must stay inside the project directory")
    return resolved


def write_json(path,value):
    path.write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count",type=int,default=1000)
    parser.add_argument("--zero-tolerance",type=float,default=.002)
    parser.add_argument("--seconds-per-unit",type=float,default=SCALE)
    parser.add_argument("--data",type=Path,default=Path("data/odlyzko_zeros.csv"))
    parser.add_argument("--out",type=Path,default=Path("outputs"),help="MIDI directory inside this project")
    parser.add_argument("--midi-only",action="store_true",default=True,
                        help="Export MIDI and numerical records only (default and only supported mode)")
    args = parser.parse_args()
    if args.count < 2 or args.zero_tolerance <= 0 or args.seconds_per_unit <= 0:
        parser.error("Count must be at least 2; tolerance and time scale must be positive")
    try:
        cache = project_path(args.data)
        output = project_path(args.out)
        generated = project_path(Path("results/generated"))
    except ValueError as exc:
        parser.error(str(exc))
    if not cache.is_file():
        parser.error("The selected zero-data file is missing from this project")

    print("Building prime melody and adapting the bundled zero spectrum",flush=True)
    primes,notes,pads,chords,duration,gammas,selection = build_score(
        args.count,cache,args.zero_tolerance,args.seconds_per_unit)
    audit = zero_field.audit_zero_source(gammas)
    assert all(all(p%d for d in range(2,math.isqrt(p)+1)) for p in primes)
    assert audio.max_notes(notes) == 1
    assert audio.max_notes(pads) == 2
    assert audio.max_notes(notes+pads) <= 3
    maximum_error = max(abs(c["normalized_log_window_error"]) for c in chords)
    assert maximum_error <= args.zero_tolerance

    tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid.uuid4().hex[:6]
    records = generated/tag
    records.mkdir(parents=True,exist_ok=False)
    output.mkdir(parents=True,exist_ok=True)
    midi_path = output/f"v1_{args.count}_Primes_{tag}.mid"
    assert not midi_path.exists()
    audio.midi(midi_path,[("Felt Piano - Prime Melody",0,notes),
                          ("Warm Pad - Collective Zero Field",89,pads)])
    midi_counts = renderer.verify_midi(midi_path,[len(notes),len(pads)])
    audio.table(records/"prime_events.csv",notes)
    audio.table(records/"zero_accompaniment_events.csv",pads)
    audio.table(records/"chord_plan.csv",chords)
    audio.table(records/"zero_selection_history.csv",selection["history"])
    print("Evaluating the collective zero field at each prime",flush=True)
    fields = [dict(prime_index=i+1,prime=p,
                   normalized_zero_field=zero_field.zero_point(p,gammas),
                   zero_count=len(gammas),gamma_max=gammas[-1]) for i,p in enumerate(primes)]
    audio.table(records/"prime_zero_field.csv",fields)
    used = records/"zeros_used.csv"
    used.write_text("index,real_part,gamma\n"+
                    "".join(f"{i+1},0.5,{g:.9f}\n" for i,g in enumerate(gammas)),encoding="utf-8")
    write_json(records/"provenance.json",dict(
        project_name=PROJECT_NAME,data_provenance="data/provenance.json",
        input_data=str(cache.relative_to(PROJECT_ROOT)).replace("\\","/"),
        cache_sha256=hashlib.sha256(cache.read_bytes()).hexdigest(),
        selected_data_sha256=hashlib.sha256(used.read_bytes()).hexdigest(),
        selected_zero_count=len(gammas),network_required=False))
    write_json(records/"zero_selection.json",selection)
    write_json(records/"zero_source_audit.json",audit)
    write_json(records/"parameters.json",dict(
        project_name=PROJECT_NAME,prime_count=len(primes),first_prime=primes[0],last_prime=primes[-1],
        duration_s=duration,seconds_per_unit=args.seconds_per_unit,harmony_seconds=HARMONY_SECONDS,
        zero_count=len(gammas),zero_selection=selection,midi_only=True,
        data_provenance="data/provenance.json",method_reference="README.md#zero-field-and-reference",
        musical_mapping="Field empirical quartiles suggest C/Am/F/G; melody compatibility selects root/fifth dyads",
        no_single_zero_to_single_prime_mapping=True,no_zero_cycling=True,
        no_ordinate_reference_frequency_normalization=True,point_field_error_guarantee=False))
    from collections import Counter
    validation = dict(
        project_name=PROJECT_NAME,status="PASS",prime_count=len(primes),first_prime=primes[0],
        last_prime=primes[-1],actual_zero_count=len(gammas),chord_count=len(chords),
        planned_score_duration_s=duration,max_simultaneous_midi_notes=audio.max_notes(notes+pads),
        midi_note_on_counts=midi_counts,
        midi_file=str(midi_path.relative_to(PROJECT_ROOT)).replace("\\","/"),
        midi_sha256=hashlib.sha256(midi_path.read_bytes()).hexdigest(),
        maximum_normalized_log_window_error=maximum_error,
        tolerance=args.zero_tolerance,zero_source_audit=audit,zero_selection=selection,
        harmony_counts=dict(Counter(c["chord"] for c in chords)),
        target_harmony_counts=dict(Counter(c["target_chord"] for c in chords)),
        musical_override_count=sum(c["musical_override"] for c in chords),
        no_repeated_zero_playlist=True,no_zero_ordinate_reference_normalization=True,
        audio_files_generated=False,network_used=False)
    write_json(records/"validation.json",validation)
    print(json.dumps(dict(status="PASS",project_name=PROJECT_NAME,prime_count=len(primes),
                          zero_count=len(gammas),midi_file=validation["midi_file"],
                          records=str(records.relative_to(PROJECT_ROOT)).replace("\\","/"),
                          maximum_normalized_log_window_error=maximum_error)),flush=True)


if __name__ == "__main__":
    main()
