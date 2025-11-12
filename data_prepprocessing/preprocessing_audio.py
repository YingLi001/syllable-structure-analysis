'''
@Project   : SMAAT Project
@File      : preprocessing_audio.py
@Author    : Ying Li
@Student ID: 20909226
@School    : EECMS
@University: Curtin University
'''

import textgrid
from pydub import AudioSegment
import soundfile as sf
import librosa
import os
import argparse

"""
Overview:
This module provides utilities to preprocess speech audio and corresponding TextGrid annotations.
Main capabilities:
- Resample a WAV audio file to a target sampling rate (default 16000 Hz).
- Parse Praat TextGrid files to extract syllable- and word-level boundaries (supports optional VOT trimming).
- Segment a (resampled) audio file into individual WAV clips using extracted boundaries and save them
    into a participant-specific output folder structure.

Assumptions and conventions:
- Expected TextGrid tier ordering:
    - tier 0: orthographic/word tier
    - tier 1: syllable tier
    - tier 2: phonetic tier (used by extract_words)
- The script treats empty interval marks as silent/ignored.
- Default output base directory is set in segment_audio; adjust output_directory_base as needed.
- Default resampling rate is 16000 Hz.

CLI usage example:
python refactored_preprocessing_audio.py /path/to/file.TextGrid TD Band_3 302_Bonnie A006_03201225_C028

"""
def resample_audio(audio_file_path, target_sr=16000):
    """
    Resample the audio file to the target sample rate.
    """
    audio, sr = librosa.load(audio_file_path, sr=target_sr)
    output_file_path = f"{audio_file_path[:-4]}_{target_sr}Hz.wav"
    sf.write(output_file_path, audio, target_sr)
    print(f"Resampled audio saved to {output_file_path}")
    return output_file_path


def extract_syllables(textgrid_file_path, VOT=0):
    """
    Extract syllables from the TextGrid file.
    """
    tg = textgrid.TextGrid.fromFile(textgrid_file_path)
    syllable_results = []

    word_intervals = int(str(tg[0]).split(" ")[2].strip())
    syllable_intervals = int(str(tg[1]).split(" ")[2].strip())

    for word_interval in range(word_intervals):
        if tg[0][word_interval].mark == "":
            continue
        
        word_interval_start = tg[0][word_interval].minTime
        word_interval_end = tg[0][word_interval].maxTime
        flag = 0
        
        for syllable_interval in range(syllable_intervals):
            syllable = tg[1][syllable_interval]
            if syllable.minTime == word_interval_start and syllable.maxTime < word_interval_end:
                flag = 1
                syllable_results.append({
                    "start": syllable.minTime - VOT,
                    "stop": syllable.maxTime,
                    "utterance": syllable.mark
                })
            elif syllable.maxTime == word_interval_end and syllable.minTime > word_interval_start:
                syllable_results.append({
                    "start": syllable.minTime,
                    "stop": syllable.maxTime + VOT,
                    "utterance": syllable.mark
                })
            elif syllable.minTime > word_interval_start and syllable.minTime < word_interval_end:
                syllable_results.append({
                    "start": syllable.minTime,
                    "stop": syllable.maxTime,
                    "utterance": syllable.mark
                })
        
        if flag == 0:
            syllable_results.append({
                "start": tg[0][word_interval].minTime - VOT,
                "stop": tg[0][word_interval].maxTime + VOT,
                "utterance": tg[0][word_interval].mark
            })
    
    print(syllable_results)
    return syllable_results


def extract_words(textgrid_file_path, VOT=0):
    """
    Extract words from the TextGrid file based on the phonetic tier.
    This function assumes that the phonetic tier is the third tier in the TextGrid.
    """
    tg = textgrid.TextGrid.fromFile(textgrid_file_path)
    word_results = []
    # extract word boundaries from phonetic tire
    word_intervals = int(str(tg[2]).split(" ")[2].strip())
    
    for word_interval in range(word_intervals):
        # empty phonetic intervals has been ignored !!!
        if tg[2][word_interval].mark == "":
            continue
        
        word = tg[0][word_interval]
        if '/' in word.mark:
            word.mark = word.mark.split('/')[1]

        word_results.append({
            'start': tg[2][word_interval].minTime - VOT,
            'stop': tg[2][word_interval].maxTime + VOT,
            'utterance': word.mark
        })
    
    print(word_results)
    return word_results


def segment_audio(audio_file_path, boundaries, children_type, band_id, participant_id, audio_id, output_directory_base="/mnt/data/ying/SMAAT_1st_iterative_learning/"):
    """
    Segment the audio file based on provided start/stop boundaries and save individual clips to a participant-specific folder.
    """
    participant_directory = os.path.join(output_directory_base, children_type, band_id, "new_TG", participant_id, "individual_wavs")
    if not os.path.exists(participant_directory):
        os.makedirs(participant_directory)

    sound = AudioSegment.from_wav(audio_file_path)

    for boundary in boundaries:
        begin = boundary['start'] * 1000  # Convert to ms
        end = boundary['stop'] * 1000  # Convert to ms
        audio_clip = sound[begin:end]

        export_path = os.path.join(participant_directory, f"{participant_id}_{audio_id}_{boundary['utterance']}.wav")
        audio_clip.export(export_path, format='wav')
    
    print(f"Audio segmentation complete for participant {participant_id}_{audio_id}.")


def process_audio(textgrid_path, children_type, band_id, participant_id, audio_id):
    print('Start')

    textgrid_file_path = textgrid_path
    audio_file_path = f'/mnt/data/ying/SMAAT_1st_iterative_learning/{children_type}/{band_id}/new_TG/{participant_id}/{audio_id}.wav'
    
    # Step 1: Extract words from TextGrid
    print('Extracting words...')
    words = extract_words(textgrid_file_path)

    # Step 2: Resample the audio
    print('Resampling audio...')
    resampled_audio_path = resample_audio(audio_file_path)

    # Step 3: Segment the audio based on word boundaries
    print('Segmenting audio...')
    segment_audio(resampled_audio_path, words, children_type, band_id, participant_id, audio_id)

    print("Finished.")

def main():

    # Set up the argument parser
    parser = argparse.ArgumentParser(description="Processing audio sampling rate and splite a long audio file into segments at the word level.")
    parser.add_argument('textgrid_path', type=str, help="Path to the textgrid file.")
    parser.add_argument('children_type', type=str, default="TD", help="Type of children ('TD' or 'SSD').")
    parser.add_argument('band_id', type=str, default="Band_3", help="Band ID ('Band_1', 'Band_2', 'Band_3', or 'Band_4').")
    parser.add_argument('participant_id', type=str, help="Participant ID (e.g., '302_Bonnie').")
    parser.add_argument('audio_id', type=str, help="Audio ID (e.g., 'A006_03201225_C028').")

    # Parse the arguments
    args = parser.parse_args()

    # Process the participant folder based on the parsed arguments
    process_audio(
        textgrid_path=args.textgrid_path,
        children_type=args.children_type,
        band_id=args.band_id,
        participant_id=args.participant_id,
        audio_id=args.audio_id
    )

if __name__ == '__main__':
    main()
