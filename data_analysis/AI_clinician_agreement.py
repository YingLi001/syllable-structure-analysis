'''
@Project   : SMAAT Project
@File      : AI_clinician_agreement.py
@Author    : Ying Li
@Student ID: 20909226
@School    : EECMS
@University: Curtin University
'''

'''This file aims to calculate the agreement between AI clinician and human clinician in phoneme transcription.
Future improvement:
    Handle diacritics in IPA transcription more effectively.
'''

from jiwer import wer
from praatio import textgrid
import os
import re
import unicodedata
import pandas as pd

def character_error_rate(pred_str, label_str):
    # pred_str/label_str: list
    print("***************** WER ***********************")
    print(pred_str)
    print(label_str)
    print("*****************  ***********************")
    error = wer(label_str, pred_str)
    return error

def get_prediction_label(file_path):
    
    tg = textgrid.openTextgrid(file_path, includeEmptyIntervals=False)
    # prediction
    prediction_tier = tg.getTier("phoneme_ipa")
    prediction_tier_cv = tg.getTier("structure")
    # label
    label_tier = tg.getTier("phonetic")

    predictions = []
    predictions_cv = []
    for start, end, text in prediction_tier.entries:
        if text == "ɪ/ɪə":
            text = "ɪ"
        predictions.append(text)
    print("predictions", predictions)
    for start, end, text in prediction_tier_cv.entries:
        predictions_cv.append(text)
    print("predictions_cv", predictions_cv)

    for start, end, text in label_tier.entries:
       
        # for item in text:
        #     print("item",item)
        #     labels.append(item.strip())    
        # print(labels)
        print("text", text)
        # broad = narrow_to_broad(text)
        broad = text
        print(f"Narrow: {text} → Broad: {broad}")
        labels = []
        labels_cv = []
        labels = [phoneme.strip() for phoneme in broad.split(',')]
        print("labels", labels)
        for item in labels:
            item_cv = mapping_ipa2cv(item)
            labels_cv.append(item_cv)
        # print("labels",labels)
    return predictions, labels, predictions_cv, labels_cv


def mapping_ipa2cv(item):
    vowels = {'u', 'j', 'ɯ', 'ʊ', 'a', 'ɘ', 'ɐ', 'i', 'ʌ', 'æ', 'ɒ', 'o', 'e', 'ɛ', 'ɜ', 'ɑ', 'ɨ', 'ɔ', 'ɵ', 'ɛ','ə','ɪ', 'ʉ', "aɪ","eɪ","oʊ","aʊ","ɔɪ","ɪə","eə","ai"}
    consonants = {'m', 't', 'b', 'f', 'x', 'ɱ', 'ɹ', 'v', 'c', 'w', 'β', 'n', 'h', 'r', 'ʧ', 'd', 's', 'p', 'q', 'ɤ', 'ŋ', 'ʔ', 'ɾ', 'k', 'g', 'l', 'ʤ', 'ɡ','ʦ','ʃ'}
    if item in vowels:
        return "V"
    elif item in consonants:
        return "C"
    else:
        return "U"

# def remove_diacritics(text):
#     """Removes diacritics from narrow IPA transcription."""
#     return ''.join([char for char in unicodedata.normalize('NFD', text) if unicodedata.category(char) != 'Mn'])
# 1: Remove all diacritics
def remove_diacritics(ipa_text):
    """Removes all diacritics from narrow IPA transcription while preserving base phonemes."""
    return ''.join(
        char for char in unicodedata.normalize('NFD', ipa_text) 
        if unicodedata.category(char) not in ['Mn', 'Sk','Lm','Po'] or char == ','
    )

# 2: Define phoneme mappings for broad IPA transcription
def narrow_to_broad(narrow_ipa):
    # Step 2: Define phoneme mappings for broad transcription
    phoneme_mapping = {
        'ʈ': 't',   # Retroflex "ʈ" → Alveolar "t"
        'ʋ': 'v',   # Labiodental approximant "ʋ" → "v"
        'ɦ': 'h',   # Voiced glottal fricative "ɦ" → "h"
        'ɸ': 'f',   # Bilabial fricative "ɸ" → "f"
        'ɣ': 'ɡ',   # Voiced velar fricative "ɣ" → "ɡ"
        'ɭ': 'l',   # Retroflex lateral "ɭ" → "l"
        'ʂ': 'ʃ',   # Retroflex fricative "ʂ" → "ʃ"
        'ǃ': 'ʔ',   # Click "ǃ" → Glottal stop "ʔ"
        'ǂ': 'ʔ',   # Alveolar click "ǂ" → Glottal stop "ʔ"
        'ʘ': 'p',   # Bilabial click "ʘ" → Bilabial stop "p"
        'ɶ': 'a',   # Open front rounded vowel "ɶ" → "a"
        'ɞ': 'ɜ',   # Close-mid central rounded vowel "ɞ" → Open-mid central unrounded vowel "ɜ"
        'œ': 'ɛ',   # Open-mid front rounded vowel "œ" → Open-mid front unrounded vowel "ɛ"
        'θ': 'ɘ',   # Voiceless dental fricative "θ" → Close-mid central unrounded vowel "ɘ"
        'ʙ':'b',
    }

    # Apply regex replacement for each diacritic
    # for pattern in diacritic_patterns:
    #     broad_ipa = re.sub(pattern, '', narrow_ipa)

    # return narrow_ipa
    # Remove diacritics
    broad_ipa = remove_diacritics(narrow_ipa)
    print("broad_ipa", broad_ipa)
    # Apply phoneme mapping
    for narrow, broad in phoneme_mapping.items():
        broad_ipa = broad_ipa.replace(narrow, broad)
    print("ipa_text", broad_ipa)
    return broad_ipa

def process_stage(files, stage_name, df):
    phonemes = set()
    results = []
    
    for file in files:
        prediction, label, prediction_cv, label_cv = get_prediction_label(file)
        for i in label:
            phonemes.add(i)
        
        error_rate_basic = character_error_rate(prediction, label)
        error_rate_cv = character_error_rate(prediction_cv, label_cv)
        filename = os.path.basename(file)
        
        text_part = os.path.splitext(filename)[0].split("_", maxsplit=6)[-1]  # Extract the sentence
        text_part = [text_part]
        
        gt = df[df["Word"].isin(text_part)]["IPA Transcription"].apply(lambda x: x.split(",")).tolist()
        gt = [item for sublist in gt for item in sublist]
        
        gt_cv = df[df["Word"].isin(text_part)]["Syllable Structure"].apply(lambda x: list(x)).tolist()
        gt_cv = [item for sublist in gt_cv for item in sublist]
        
        error_rate_gt = character_error_rate(prediction, gt)
        error_rate_gt_cv = character_error_rate(prediction_cv, gt_cv)
        error_rate_label_gt = character_error_rate(label, gt)
        error_rate_label_gt_cv = character_error_rate(label_cv, gt_cv)

        
        results.append([filename, stage_name, prediction,label, error_rate_basic, prediction_cv, label_cv, error_rate_cv, prediction, gt, error_rate_gt, prediction_cv, gt_cv, error_rate_gt_cv, label, gt, error_rate_label_gt, label_cv, gt_cv, error_rate_label_gt_cv])
    
    return results, phonemes

def main():
    stage = {
        'stage3': ['ba', 'eye', 'map', 'um', 'ham', 'papa', 'bob', 'pam', 'pup','pie'],
        'stage4': ['boy', 'b', 'peep', 'bush', 'moon', 'phone', 'feet', 'fish', 'wash', 'show'],
        'stage5': ['ten', 'dig', 'log', 'owl', 'cake', 'sun', 'snake', 'juice', 'clown', 'crib', 'grape'],
        'stage6': ['cupcake', 'icecream', 'toothbrush', 'robot', 'banana', 'marshmallow', 'umbrella', 'hamburger', 'watermelon', 'rhinoceros']
    }
    
    files_by_stage = {key: [] for key in stage}
    inpath = "/mnt/data/ying/SMAAT_1st_iterative_learning/SSD/Band_4"
    
    for _f in os.listdir(inpath):
        parent_f = os.path.join(inpath, _f)
        # if _f in ["336_Maddie", "343_Alice", "388_Archie", "409_Lotti", "465_Claire"]:
        #     continue
        
        input_directory = os.path.join(parent_f, 'ml_tg_no_max_before_using_smaat')
        for file_name in os.listdir(input_directory):
            file_path = os.path.join(input_directory, file_name)
            word = file_name.split('_')[-1].split('.')[0]
            
            for stage_name, words in stage.items():
                if word in words:
                    files_by_stage[stage_name].append(file_path)
                    break
    
    df = pd.read_csv("/home/ying/preprocess_SMAAT/stages_words.csv")
    all_results = []
    all_phonemes = set()
    
    for stage_name, files in files_by_stage.items():
        results, phonemes = process_stage(files, stage_name, df)
        all_results.extend(results)
        all_phonemes.update(phonemes)
    
    results_df = pd.DataFrame(all_results, columns=["Filename", "Stage", "Prediction", "Label", "Error_Rate_Basic", "Prediction_CV", "Label_CV", "Error_Rate_CV", "Prediction", "GT", "Error_Rate_GT", "Prediction_CV", "GT_CV", "Error_Rate_GT_CV", "label", "gt", "error_rate_label_gt", "label_cv", "gt_cv", "error_rate_label_gt_cv"])
    results_df.to_csv("error_rates_by_stage_with_diacritics.csv", index=False)
    phoneme_df = pd.DataFrame(all_phonemes, columns=["phoneme"])
    phoneme_df.to_csv("all_phonemes_filename_with_diacritics.csv", index=False)
    print("Error rates saved to error_rates_by_stage.csv")
    print(all_phonemes, len(all_phonemes))

import csv
from collections import defaultdict

def extract_phonemes(csv_file, output_file):
    phoneme_dict = defaultdict(set)  # Dictionary to store phonemes and their corresponding filenames
    # print()
    with open(csv_file, newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        headers = next(reader)  # Read the header row
        
        filename_index = 0  # First column (filename)
        label_index = headers.index("Label")  # Find index of 'Label' column
        
        for row in reader:
            filename = row[filename_index]
            phonemes = eval(row[label_index])  # Convert string representation of list to actual list
            
            for phoneme in phonemes:
                phoneme_dict[phoneme].add(filename)
    # Save results to a CSV file
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Phoneme", "Filenames"])
        for phoneme, filenames in phoneme_dict.items():
            writer.writerow([phoneme, ", ".join(filenames)])
    
    return phoneme_dict

if __name__ == "__main__":
    # main()
    # # Call the function with your input and output file names
    # input_file = '/home/ying/preprocess_SMAAT/error_rates_by_stage_with_diacritics.csv'  # Path to your generated phoneme files CSV
    # output_file = 'phoneme_files_with_diacritics.csv'  # Path to save the processed results

    # process_phoneme_files(input_file, output_file)
    
    # Example usage:
    csv_file = "/home/ying/preprocess_SMAAT/band_3_results/error_rates_band3_full_exclude_Julian.csv"  # Replace with your CSV filename
    output_file = "/home/ying/preprocess_SMAAT/band_3_results/phoneme_files_with_diacritics_band3_TD_exclude_Julian.csv"  # Replace with your output filename
    phoneme_data = extract_phonemes(csv_file, output_file)
    phonemes = set()
    # Print results
    for phoneme, filenames in phoneme_data.items():
        print(f"Phoneme: {phoneme}, Filenames: {list(filenames)}")
        phonemes.update(phoneme)
    print(phonemes, len(phoneme_data))

