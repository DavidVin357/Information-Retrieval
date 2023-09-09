#!/usr/bin/python3

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import nltk
import sys
import getopt

from decimal import Decimal


def build_LM(in_file):
    """
    build language models for each label
    each line in in_file contains a label and a string separated by a space
    """
    print("building language models...")
    languages = ["indonesian", "malaysian", "tamil"]

    gram_len = 4

    def construct_gram_model(gram_len, languages):
        LM = dict()
        # Model scaffold: for every language, record chunks frequency and total frequency
        for lang in languages:
            LM[lang] = {
                "total_frequency": 0,
                "chunks": {}
            }

        input_lines = open(in_file).readlines()

        for line in input_lines:
            # Extract language & text from the given line
            split_line = line.split(' ', 1)
            language = split_line[0]
            text = ''.join(split_line[1::gram_len]).replace("\n", "")

            # For a given language, record chunks frequency
            language_instance = LM[language]
            for i in range(len(text)):
                # extract a 4-letter chunk
                chunk = text[i: i + gram_len]
                # don't record chunks with less than gram length (4 in this case)
                if len(chunk) < gram_len:
                    continue
                # if chunk already exists, add 1 to its frequency
                if language_instance["chunks"].get(chunk):
                    language_instance["chunks"][chunk] += 1
                    language_instance["total_frequency"] += 1

                # if chunk is new, set the frequency to 2: one occurrence + add-1 smoothing
                else:
                    language_instance["chunks"][chunk] = 2
                    language_instance["total_frequency"] += 2

        # Set chunks that don't exist in other languages as 1 (zero frequency + add-1 smoothing)
        for current_lang in languages:
            other_languages = [l for l in languages if l != current_lang]
            for key in LM[current_lang]["chunks"]:
                for ol in other_languages:
                    if LM[ol]["chunks"].get(key) is None:
                        # zero frequency, but apply add-1 smoothing
                        LM[ol]["chunks"][key] = 1
                        LM[ol]["total_frequency"] += 1

        return LM

    def calculate_probabilities(LM):
        for lang in LM:
            total_frequency = LM[lang]["total_frequency"]
            # Replace gram_model with prob_model through dividing each chunk_frequency by total_frequency
            # Use Decimal for better precision
            # Resulting model structure: {lang1: { chunk1: frequency1, chunk2: frequency2 }, lang2: {...}, ... }
            LM[lang] = {chunk_name: Decimal(chunk_frequency) / Decimal(total_frequency)
                        for chunk_name, chunk_frequency in LM[lang]["chunks"].items()}

        return LM

    gram_model = construct_gram_model(gram_len, languages)
    prob_model = calculate_probabilities(gram_model)
    return prob_model


def test_LM(in_file, out_file, LM):
    languages = ["indonesian", "malaysian", "tamil"]

    gram_len = 4

    # Clear the output file from previous content
    open(out_file, "w").close()

    input_lines = open(in_file).readlines()

    for line in input_lines:
        # Create prediction dictionary for a line with the following structure:
        # {lang1: prob1, lang2: prob2, ...}
        # Set 1 as the starting probability for each language
        prediction = dict()
        for lang in languages:
            prediction[lang] = Decimal(1)

        text = line.replace("\n", "")

        for i in range(len(text)):
            # extract chunk
            chunk = text[i: i + gram_len]
            # omit <4 letter chunks
            if len(chunk) < gram_len:
                continue
            for lang in languages:
                #  If a chunk exists in language model, multiply by its probability
                chunk_probability = LM[lang].get(chunk)
                if chunk_probability:
                    prediction[lang] *= chunk_probability

        # Remove languages that have probability 1 (no chunk fitted so didn't multiply)
        filtered_prediction = {lang: lang_prob for lang, lang_prob in prediction.items() if lang_prob != 1}

        f = open(out_file, "a")

        # Empty filtered_prediction => no chunk from existing languages fits, thus output 'other'
        if not filtered_prediction:
            f.write(f'other {line}')

        # Otherwise, output the language with maximum probability
        else:
            language_guess = max(filtered_prediction, key=prediction.get)
            f.write(f'{language_guess} {line}')
            f.close()


def usage():
    print(
        "usage: "
        + sys.argv[0]
        + " -b input-file-for-building-LM -t input-file-for-testing-LM -o output-file"
    )


input_file_b = input_file_t = output_file = None
try:
    opts, args = getopt.getopt(sys.argv[1:], "b:t:o:")
except getopt.GetoptError:
    usage()
    sys.exit(2)
for o, a in opts:
    if o == "-b":
        input_file_b = a
    elif o == "-t":
        input_file_t = a
    elif o == "-o":
        output_file = a
    else:
        assert False, "unhandled option"
if input_file_b == None or input_file_t == None or output_file == None:
    usage()
    sys.exit(2)

LM = build_LM(input_file_b)
test_LM(input_file_t, output_file, LM)
