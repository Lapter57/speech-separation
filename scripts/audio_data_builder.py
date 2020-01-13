import sys
sys.path.append("../lib")
import utils
import avhandler as avh
import os
import numpy as np
import librosa
import itertools
from argparse import ArgumentParser

DIR = ("{path}/{dirname}")

def init_dir(path):
    if not os.path.isdir(path):
        os.mkdir(path) 

def init_dirs(path):
    init_dir(path)
    mix_path = DIR.format(path=path, dirname="mix")
    clean_path = DIR.format(path=path, dirname="clean")
    crm_path = DIR.format(path=path, dirname="crm")
    init_dir(mix_path)
    init_dir(clean_path)
    init_dir(crm_path)
    return mix_path, clean_path, crm_path

def build_clean_data(clean_path, speaker_paths):
    for path in speaker_paths:
        audio, sr = librosa.load(path, sr=16000)
        audio = utils.stft(audio)
        filename = utils.basename(path)
        np.save(("{}/{}.npy").format(clean_path, filename), audio)

def build_mix_data(mix_path, speaker_paths, num_speakers=2, noise_path=None):
    split_speakers = np.array_split(speaker_paths, num_speakers)
    cross_product = itertools.product(*split_speakers)
    for paths in cross_product:
        mix, noise_file = avh.mix_audio(paths, noise_path)
        mix = utils.stft(mix)
        filename = ""
        for path in paths:
            filename += utils.basename(path) + "."
        if noise_path:
            filename += utils.NOISE_PREFIX + utils.basename(noise_file) + "."
        np.save(("{}/{}npy").format(mix_path, filename), mix)

def build_crm_data(crm_path, mix_path, clean_path):
    mix_files = utils.get_files(mix_path)
    clean_files = utils.get_files(clean_path)
    mix_npys = np.array([(utils.basename(f), np.load(f)) for f in mix_files])
    for mix_npy in mix_npys:
        clean_filenames = utils.get_clean_in_mix(mix_npy[0])
        for clean_filename in clean_filenames:
            clean_file = utils.find_paths_contains(clean_filename, clean_files)[0]
            clean_audio = np.load(clean_file)
            cRM = utils.cRM(clean_audio, mix_npy[1])
            filename = ("clean:{} mix:{}").format(clean_filename, mix_npy[0])
            np.save(("{}/{}.npy").format(crm_path, filename), cRM)
        
def build(path, speaker_path, usage=2, num_speakers=2, noise_path=None):
    mix_path, clean_path, crm_path = init_dirs(path)
    
    speaker_paths = utils.get_files(speaker_path)
    np.random.shuffle(speaker_paths)
    speaker_paths = speaker_paths[:usage]
    
    build_clean_data(clean_path, speaker_paths)
    build_mix_data(mix_path, speaker_paths, num_speakers, noise_path)
    build_crm_data(crm_path, mix_path, clean_path)
    
    
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--path", action="store",
                        dest="path", required=True,
                        help="Path to the folder where audio data will be saved")
    parser.add_argument("--speakers", action="store",
                        dest="speaker_path", required=True,
                        help="Path to the folder where the audio data of the speakers is stored")
    parser.add_argument("--usage", action="store", type=int,
                        dest="usage", default=2,
                        help="Data usage to generate audio data (default=2)")
    parser.add_argument("--nums", action="store", type=int,
                        dest="num_speakers", default=2,
                        help="Number of speakers used in the mix (default=2)")
    parser.add_argument("--noise", action="store",
                        dest="noise_path",
                        help="Path to the folder where the audio data of the noise is stored. If specified, noise will be used during build")
    args = parser.parse_args()
    
    build(args.path, args.speaker_path, args.usage,
          args.num_speakers, args.noise_path)