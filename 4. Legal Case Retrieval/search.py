#!/usr/bin/python3

import math
import pickle

from nltk import word_tokenize
from nltk.stem.porter import PorterStemmer
import sys
import getopt


def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


# Experiment: impact ordering using custom weights for courts with different hierarchy
# courts = {
#     ('SG Court of Appeal', 'SG Privy Council',
#      'UK House of Lords', 'UK Supreme Court', 'High Court of Australia', 'CA Supreme Court'): 1.4,
#
#     ('SG High Court', 'Singapore International Commercial Court', 'HK High Court',
#      'HK Court of First Instance', 'UK Crown Court', 'UK Court of Appeal', 'UK High Court',
#      'Federal Court of Australia', 'NSW Court of Appeal', 'NSW Court of Criminal Appeal',
#      'NSW Supreme Court'
#      ): 1.2
# }
#
#
# def court_importance(court):
#     for key in courts:
#         if court in key:
#             return courts[key]
#     return 1

def process_words(text):
    stemmer = PorterStemmer()
    processed_words = []
    for word in word_tokenize(text):
        if word != 'AND' and word.isalnum():
            processed_words.append(stemmer.stem(word))
    return processed_words


with open('additional.txt', 'rb') as other_data_handle:
    otherData = pickle.load(other_data_handle)


def cosine_similarity(query, dictionary_path, postings_path):
    with open('docIds.txt', 'rb') as handle:
        all_docIds_length = len(pickle.load(handle))

    scores = dict()
    query_terms = process_words(query)
    postings_file = open(postings_path, 'rb')

    with open(dictionary_path, 'rb') as dictionary_file:
        dictionary = pickle.load(dictionary_file)

    query_frequencies = dict()

    # Fill query_terms dictionary
    for query_term in query_terms:
        if query_term in query_frequencies:
            query_frequencies[query_term] += 1
        else:
            query_frequencies[query_term] = 1

    # For each query term, compute a product with documents terms and add to the score
    for query_term, query_term_frequency in query_frequencies.items():
        position = dictionary.get(query_term)
        if position is None:
            continue
        postings_file.seek(position)
        data = postings_file.read()
        postings_list = pickle.loads(data)
        docFrequency = len(postings_list)
        # calculate w(t, q)
        # query scheme: lpn
        wq = max(0, math.log10((all_docIds_length - docFrequency) / docFrequency)) * (
                    1 + math.log10(query_term_frequency))

        for node in postings_list:
            frequencies = node[1]
            docId = node[0]

            # Experiment: additional weight if term is in the title
            # weight = 1
            # if frequencies[1] > 0:
            #     weight = 1.4

            # l_tf
            tf = sum(frequencies)
            tfd = (1 + math.log10(tf))
            if docId in scores:
                scores[docId] += tfd * wq
            else:
                scores[docId] = tfd * wq

    result = []
    for docId in scores:
        result.append((docId, scores[docId]))

    return sorted(result, key=lambda x: -x[1])


def search_and_write(queries_path, output_path, dictionary_path, postings_path):
    input_queries_file = open(queries_path, 'r')
    output_file = open(output_path, 'w')
    queries = input_queries_file.read().splitlines()
    lines = []
    for q in queries:
        result_str = ''
        result = cosine_similarity(query=q, dictionary_path=dictionary_path, postings_path=postings_path)
        if len(result) > 0:
            result_str = ' '.join([str(r[0]) for r in result])
        lines.append(result_str + '\n')

    output_file.writelines(lines)


dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None:
    usage()
    sys.exit(2)


def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')
    search_and_write(queries_path=queries_file, dictionary_path=dict_file, postings_path=postings_file,
                     output_path=results_file)
    print('DONE!')


run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
