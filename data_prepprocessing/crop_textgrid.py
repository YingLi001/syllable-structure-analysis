'''
@Project   : SMAAT Project
@File      : crop_textgrid.py
@Author    : Ying Li
@Student ID: 20909226
@School    : EECMS
@University: Curtin University
'''

import os
from praatio import textgrid
import argparse
import sys

"""
This script processes TextGrid files by cropping them based on a specified phonetic tier and adjusting timestamps to start from zero.
Note: In load_textgrid_file function, the 'includeEmptyIntervals' parameter is set to True to include empty intervals in the TextGrid.
This is important for ensuring that all intervals are processed correctly, even if they are empty. Therefore, in the crop_textgrid function,
it generate short textgrids according to the phonetic tier. If word tier is correct (word tier always have content) but phonetic tier is empty 
(e.g. /a/ /i/ /u/ ...), they can also generate short textgrids. 

When we calcualte the error rate across all participants, we are using the PROMPT Word list, 40 words across four stages. Therefore, 
if we generated any textgrids with empty phonetic intervals, we will not use these textgrids for error rate calculation.
"""

def ensure_directory_exists(directory_path):
    """Ensure the given directory exists. Create it if not."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def load_textgrid_file(file_path):
    """Load a TextGrid file."""
    return textgrid.openTextgrid(file_path, includeEmptyIntervals=True)

def get_labels_from_word_tier(tg):
    """Extract labels from the 'word' tier in the TextGrid."""
    word_tier = tg.getTier("word")
    labels = []
    for start, end, label in word_tier.entries:
        label = label.split("/")[1] if '/' in label else label
        labels.append(label)
    return labels

def crop_textgrid(tg, split_tier_name, output_directory, participant_id, audio_id):
    """Crop the TextGrid based on the split tier and save cropped TextGrids."""
    # Ensure output directory exists
    ensure_directory_exists(output_directory)

    # Get the split tier: phonetic tier
    split_tier = tg.getTier(split_tier_name)

    # Get labels from 'word' tier
    labels = get_labels_from_word_tier(tg)
    # print("labels",labels)

    # Prepare lists for crop start and end times: empty intervals will be ignored
    crop_start = [start for start, _, _ in split_tier.entries]
    crop_end = [end for _, end, _ in split_tier.entries] 
    # # Round crop_start and crop_end to 2 decimals
    # crop_start = [round(start, 2) for start in crop_start]
    # crop_end = [round(end, 2) for end in crop_end]
        # print("start",start)
        # print("end",end)
        # print("label",label)
        # print("crop_start",crop_start)
        # print("crop_end",crop_end)

    # Crop and save TextGrid files: the reason for using i is that we need to use labels[i] to put the word in the filename path.
    if len(labels) == len(crop_start):
        for i in range(len(crop_start)):
            cropped_tg = tg.crop(crop_start[i], crop_end[i], mode="truncated", rebaseToZero=False)
            # print("len(crop_start) after", len(crop_start))
            # print("cropped_tg",cropped_tg)
            new_tg_filename = os.path.join(output_directory, f"{participant_id}_{audio_id}_{labels[i]}.TextGrid")
            # print("new_tg_filename", new_tg_filename)
            cropped_tg.save(new_tg_filename, format="long_textgrid", includeBlankSpaces=False)
        return output_directory
    else:
        sys.exit(f"Stopping script. Word labels are {len(labels)} while phonetic labels are {len(crop_start)}. Empty phonetic interval(s) were founded!")


def adjust_timestamps_in_textgrid(textgrid_lines):
    """Adjust timestamps in TextGrid content based on global xmin."""
    global_xmin = float([line.split('=')[1].strip() for line in textgrid_lines if 'xmin' in line][0])
    # print(global_xmin)
    for i, line in enumerate(textgrid_lines):
        if 'xmin' in line or 'xmax' in line:
            current_value = float(line.split('=')[1].strip())
            current_value_str = line.split('=')[1].strip() # used for replacement for integer, e.g., 52, float(52) = 52.0, if doesnot match, can not do repalcement
            adjusted_value = max(0, current_value - global_xmin)
            # print("adjusted_value",adjusted_value)
            textgrid_lines[i] = line.replace(current_value_str, str(adjusted_value))

    return textgrid_lines

def process_textgrid_files(input_directory, output_directory):
    """Process all TextGrid files in the given directory."""
    ensure_directory_exists(output_directory)

    for file_name in os.listdir(input_directory):
        if file_name.endswith('.TextGrid'):
            file_path = os.path.join(input_directory, file_name)

            with open(file_path, 'r') as file:
                textgrid_content = file.readlines()

            adjusted_content = adjust_timestamps_in_textgrid(textgrid_content)

            adjusted_file_path = os.path.join(output_directory, file_name)
            with open(adjusted_file_path, 'w') as file:
                file.writelines(adjusted_content)

def process_textgrid(textgrid_path, children_type, band_id, participant_id, audio_id, split_tier_name="phonetic"):
    # Step 1: Crop the original TextGrid based on the phonetic tier
    original_tg_path = textgrid_path
    output_directory = f'/mnt/data/ying/SMAAT_1st_iterative_learning/{children_type}/{band_id}/new_TG/{participant_id}/individual_TG/'
    tg = load_textgrid_file(original_tg_path)

    # Crop the TextGrid and save to the output directory
    cropped_textgrid_dir = crop_textgrid(tg, split_tier_name, output_directory, participant_id, audio_id)

    # Step 2: Adjust timestamps in the cropped TextGrid files
    rebase_output_directory = f'/mnt/data/ying/SMAAT_1st_iterative_learning/{children_type}/{band_id}/new_TG/{participant_id}/rebase_to_zero_TG'
    process_textgrid_files(cropped_textgrid_dir, rebase_output_directory)

    print("Processing completed.")


def main():
    # Set up the argument parser
    parser = argparse.ArgumentParser(description="Process TextGrid files and crop them based on phonetic tier.")
    parser.add_argument('textgrid_path', type=str, help="Path to the textgrid file.")
    parser.add_argument('children_type', type=str, default="TD", help="Type of children ('TD' or 'SSD').")
    parser.add_argument('band_id', type=str, default="Band_3", help="Band ID ('Band_1', 'Band_2', 'Band_3', or 'Band_4').")
    parser.add_argument('participant_id', type=str, help="Participant ID (e.g., '302_Bonnie').")
    parser.add_argument('audio_id', type=str, help="Audio ID (e.g., 'A006_03201225_C028').")

    # Parse the arguments
    args = parser.parse_args()

    # Process the participant folder based on the parsed arguments
    process_textgrid(
        textgrid_path=args.textgrid_path,
        children_type=args.children_type,
        band_id=args.band_id,
        participant_id=args.participant_id,
        audio_id=args.audio_id
    ) 
    
if __name__ == '__main__':
    main()
