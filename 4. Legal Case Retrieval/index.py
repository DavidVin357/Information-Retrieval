#!/usr/bin/python3

import multiprocessing as mp
from nltk import word_tokenize, sent_tokenize
from nltk.stem.porter import PorterStemmer
import pickle
from lib import pandas as pd
import sys
import getopt

sys.setrecursionlimit(20000)


def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")


def process_words(text):
    sentences = sent_tokenize(text)
    words = []
    for s in sentences:
        words.extend(word.lower() for word in word_tokenize(s))
    stemmer = PorterStemmer()
    return map(stemmer.stem, words)


dataset_file = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i':  # input directory
        dataset_file = a
    elif o == '-d':  # dictionary file
        output_file_dictionary = a
    elif o == '-p':  # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if dataset_file == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

df = pd.read_csv(dataset_file)

# Record docIds
docIds = sorted(df['document_id'].tolist())

with open('docIds.txt', 'wb') as docIds_handle:
    pickle.dump(docIds, docIds_handle, protocol=pickle.HIGHEST_PROTOCOL)

docIds_handle.close()

additional_data = {}


def mapper(docId):
    other_data = {}

    # Split zones data
    content = process_words(df[df['document_id'] == docId]['content'].values[0])
    title = process_words(df[df['document_id'] == docId]['title'].values[0])
    date = process_words(df[df['document_id'] == docId]['date_posted'].values[0])
    court_name = df[df['document_id'] == docId]['court'].values[0]
    court = process_words(court_name)
    values = [content, title, date, court]

    # content, title, date, court - record term frequencies by zone
    # [0, 0, 0, 0, 0]
    term_frequencies = {}
    # result = {term: [docId, zone_frequencies]}
    result = {}
    for i, v in enumerate(values):
        for word in v:
            if word in term_frequencies:
                term_frequencies[word][i] += 1
            else:
                term_frequencies[word] = [0, 0, 0, 0]
                term_frequencies[word][i] += 1

    for term, frequencies in term_frequencies.items():
        result[term] = [[docId, term_frequencies[term]]]

    other_data[docId] = court_name

    return {
        'index': result,
        'other_data': other_data
    }


def combine(data_list):
    index_result = {}
    count = 0
    while len(data_list):
        data = data_list.pop()
        index = data['index']
        other_data = data['other_data']
        additional_data.update(other_data)
        for key in index:
            if key in index_result:
                index_result[key].extend(index[key])
            else:
                index_result[key] = index[key]
        count += 1

    return index_result


def create_index(postings_path, dictionary_path):
    # Concurrent MapReduce
    with mp.Pool(mp.cpu_count()) as pool:
        # MapReduce for all docIds
        indexes = pool.map(mapper, docIds)

    # Final reduce
    inverted_index = combine(indexes)

    dictionary = {}
    postings_file = open(postings_path, 'ab')

    for key in inverted_index:
        payload = inverted_index[key]
        position = postings_file.tell()

        postings_file.write(pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL))
        dictionary[key] = position

    postings_file.close()

    print('Dumping dictionary and additionals...')
    with open(dictionary_path, 'wb') as dictionary_handle:
        pickle.dump(dictionary, dictionary_handle, protocol=pickle.HIGHEST_PROTOCOL)

    dictionary_handle.close()

    with open('additional.txt', 'wb') as additional_data_handle:
        pickle.dump(additional_data, additional_data_handle, protocol=pickle.HIGHEST_PROTOCOL)

    additional_data_handle.close()


def build_index(out_dict, out_postings):
    print('indexing...')
    create_index(dictionary_path=out_dict, postings_path=out_postings)
    print('DONE!')


build_index(output_file_dictionary, output_file_postings)
