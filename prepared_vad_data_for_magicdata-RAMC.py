#!/usr/bin/env python

 
from pathlib import Path
import argparse
import os 
from typing import Dict
from datetime import timedelta

from vad.data_models.audio_data import AudioData
from vad.data_models.voice_activity import VoiceActivity
from vad.data_models.voice_activity import Activity
from vad.data_models.voice_activity import VoiceActivityVersion


from vad.data_models.vad_data import VADDataPair 
from vad.data_models.vad_data import VADDataList


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--data_path", help="the path for kaldi format magicdata-RAMC ")
    parser.add_argument("--type", help="train , dev, test")
    args = parser.parse_args()
    return args


def rttm_to_dict(rttm: str):
    rttm_dict = dict()
    with open(rttm,'r')as f:
        # SPEAKER CTS-CN-F2F-2019-11-15-160 1 1.008 7.5 <NA> <NA> G00000697 <NA> <NA>
        # SPEAKER CTS-CN-F2F-2019-11-15-160 1 11.355 2.78 <NA> <NA> G00000697 <NA> <NA>
        for line in f:
            items = line.strip().split()
            uttid, start_time_seconds, duration_seconds= items[1],items[3],items[4]
            end_time_seconds = float(start_time_seconds) +  float(duration_seconds)
            if uttid not in rttm_dict.keys():
                rttm_dict[uttid] = []
            rttm_dict[uttid].append((timedelta(seconds=float(start_time_seconds)),timedelta(seconds=float(end_time_seconds))))
    return rttm_dict

def wavscp_to_dict(wav_scp: str):
    wavscp2dict=dict()
    with open(wav_scp,'r')as f:
        for line in f:
            line = line.strip().split()
            wavscp2dict[line[0]] = line[1]
    return wavscp2dict

def gen_vad_json(wav_scp: str, rttm_dict: Dict , output_dir: str):
    with open(wav_scp, 'r')as f:
        for line in f:
            line = line.strip().split()
            audio_path = line[-1]
            uttid = line[0]
            segments = rttm_dict[uttid]

            audio_data = AudioData.load(Path(audio_path))
            activities = []
            for start_time, end_time in segments:
                activities.append(Activity(start=start_time, end=end_time))

            vad = VoiceActivity(
                duration=audio_data.duration,
                activities=activities,
                probs_sample_rate=None,
                probs=None,
            )
            vad.save(path=Path(f"{output_dir}/{uttid}.json"), version=VoiceActivityVersion.v03)


"""
def gen_vad_net_input_format_data(vad_samples_file: str, wavscp_to_dict: Dict, output_dir: str ):
    vaddatapairs = []
    for uttid, audio_path in wavscp_to_dict.items():
        vad_json_path = f"{output_dir}/{uttid}.json"
        vaddatapairs.append(VADDataPair(audio_path=Path(audio_path)),voice_activity_path=Path(vad_json_path))

    vaddatalist = VADDataList(pairs=vaddatapairs)
    vaddatalist.save(vad_samples_file)

"""
        


if __name__== "__main__":
    args=get_args()
    data_path = os.path.join(args.data_path,args.type)
    rttm = f"{data_path}/rttm"
    wav_scp = f"{data_path}/wav.scp"
    output_dir=f"{data_path}/vad_json"
    vad_samples_file = f"{data_path}/vad-{args.type}-samples.jsonl"
    os.makedirs(output_dir,exist_ok=True)
    rttm_dict = rttm_to_dict(rttm)

    ## generate format vad json file for every wavform utterance
    gen_vad_json(wav_scp, rttm_dict, output_dir)

    wavscp2dict = wavscp_to_dict(wav_scp)
    
    ## generate input format data of vad net 
    vaddatapairs = []
    for uttid, audio_path in wavscp2dict.items():
        vad_json_path = f"{output_dir}/{uttid}.json"
        vaddatapairs.append(VADDataPair(audio_path=Path(audio_path),voice_activity_path=Path(vad_json_path)))

    vaddatalist = VADDataList(pairs=vaddatapairs)
    vaddatalist.save(Path(vad_samples_file))


