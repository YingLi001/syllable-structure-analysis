'''
@Project   : SMAAT Project
@File      : csv_to_textgrid.py
@Author    : Ying Li
@Student ID: 20909226
@School    : EECMS
@University: Curtin University
'''

'''This file aims to generating the boundaries in textgrid format according to the provided csv timstamps.'''
import csv
from praatio import textgrid
import librosa
import os


def read_csv(path):
    try:
        words = []
        intervals = []
        intervals_no_labels = []
        with open(path, encoding='utf-16', newline='') as f:
            reader = csv.reader(f)
            next(reader, None)  # skip the headers
            initial_timestamp = 0
            for row in reader:
                items = row[0].split('\t')
                # Check if the row has at least 4 elements
                if len(items) < 4:
                    raise ValueError(f"ATTENTION!!! Invalid row encountered: {row}. Please open the CSV file in a text editor and "
                                     f"ensure each row contains at least 4 elements and does not include extra newlines.")
                words.append(items[0])
                onset_time = convert_time_format(items[2])
                intervals.append((initial_timestamp, onset_time, ''))
                intervals_no_labels.append((initial_timestamp, onset_time, ''))
                offset_time = convert_time_format(items[3])

                intervals.append((onset_time, offset_time, items[0]))
                intervals_no_labels.append((onset_time, offset_time, ''))
                initial_timestamp = offset_time

            return intervals, intervals_no_labels
    except Exception as e:
        print(f"ATTENTION!!! Error reading CSV file at {path}: {e}")
        raise  # Re-throw the exception after logging it


def convert_time_format(time):
    #     convert time into seconds
    try:
        times = time.split(':')
        if len(times) != 4:
            raise ValueError(f"ATTENTION!!! Invalid time format: {time}")
        hours = int(times[0])
        minutes = int(times[1])
        seconds = int(times[2])
        frames = int(times[3])
        total_frames = hours * 60 * 60 * 60 + minutes * 60 * 60 + seconds * 60 + frames
        frame_rate = 60
        final_seconds = total_frames/frame_rate
        return final_seconds
    except Exception as e:
        print(f"ATTENTION!!! Error converting time format: {time}. Error: {e}")
        return 0
def generate_textgrid(wav_file_path, intervals, intervals_no_labels, output_path):
    try:
        # generate TextGrid files
        duration = librosa.get_duration(path=wav_file_path)
        intervals.append((intervals[-1][1], duration, ''))
        intervals_no_labels.append((intervals_no_labels[-1][1], duration, ''))
        tg = textgrid.Textgrid()
        word_tier = textgrid.IntervalTier('word', intervals, 0, duration)
        syllable_tier = textgrid.IntervalTier('syllable', intervals_no_labels, 0, duration)
        phonetic_tier = textgrid.IntervalTier('phonetic', intervals_no_labels, 0, duration)
        error_tier = textgrid.IntervalTier('error', intervals_no_labels, 0, duration)
        tg.addTier(word_tier)
        tg.addTier(syllable_tier)
        tg.addTier(phonetic_tier)
        tg.addTier(error_tier)
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        tg.save(output_path, format="long_textgrid", includeBlankSpaces=False, minTimestamp=0, maxTimestamp=duration)
        print(f"TextGrid file saved at {output_path}")

    except Exception as e:
        print(f"ATTENTION!!! Error generating TextGrid for {wav_file_path}: {e}")

if __name__ == '__main__':
    try:
        # Please update the following three paths manually for each raw audio file
        wav_file_path = "/wav/path/to/your/local/path/of/the/audio/file/C002.wav"
        csv_file_path = "/csv/path/to/your/local/path/of/the/csv/file/C002.csv"
        output_textgrid_path = "/output/path/to/your/local/path/of/the/textgrid/file/C002.TextGrid"

        intervals, intervals_no_labels = read_csv(csv_file_path)
        if not intervals:
            print("ATTENTION!!! No valid intervals generated. Exiting.")
        else:
            generate_textgrid(wav_file_path, intervals, intervals_no_labels, output_textgrid_path)
    except Exception as e:
        print(f"ATTENTION!!! Script stopped due to an error: {e}")
