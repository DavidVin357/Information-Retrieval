import multiprocessing as mp
from nltk import word_tokenize, sent_tokenize
from nltk.stem.porter import PorterStemmer
import pickle
import pandas as pd
import math
import sys

sys.setrecursionlimit(20000)


def process_words(text):
    sentences = sent_tokenize(text)
    words = []
    for s in sentences:
        words.extend(word.lower() for word in word_tokenize(s))
    stemmer = PorterStemmer()
    return map(stemmer.stem, words)


df = pd.read_csv('dataset.csv')

# Record docIds
docIds = sorted(df['document_id'].tolist())

with open('docIds.txt', 'wb') as docIds_handle:
    pickle.dump(docIds, docIds_handle, protocol=pickle.HIGHEST_PROTOCOL)

docIds_handle.close()

# additional_data:
# {docId: (doc_length_n, doc_length_l, doc_length_a, doc_length_ave, max-tf, ave-tf, court_name)}
additional_data = {}


def mapper(docId):
    other_data = {}

    content = process_words(df[df['document_id'] == docId]['content'].values[0])
    title = process_words(df[df['document_id'] == docId]['title'].values[0])
    date = process_words(df[df['document_id'] == docId]['date_posted'].values[0])
    court_name = df[df['document_id'] == docId]['court'].values[0]
    court = process_words(court_name)
    values = [content, title, date, court]
    # content, title, date, court
    # [0, 0, 0, 0]
    term_frequencies = {}
    # result = [{terms}, max_tf, ave_tf]
    result = {}
    for i, v in enumerate(values):
        for word in v:
            if word in term_frequencies:
                term_frequencies[word][i] += 1
            else:
                term_frequencies[word] = [0, 0, 0, 0]
                term_frequencies[word][i] += 1

    doc_length_n = 0
    doc_length_l = 0
    doc_length_ave = 0
    doc_length_a = 0
    ave_tf = 0
    max_tf = 0

    # Compute ave_tf
    for term, frequencies in term_frequencies.items():
        fsum = sum(frequencies)
        if fsum > max_tf:
            max_tf = fsum
        ave_tf += fsum
    ave_tf = ave_tf / len(term_frequencies.keys())

    for term, frequencies in term_frequencies.items():
        tf = sum(frequencies)
        # Natural
        tfd_n = tf
        #
        # Logarithmic
        tfd_l = 1 + math.log10(tf)
        #
        # Log Ave
        tfd_ave = (1 + math.log10(tf)) / (1 + math.log10(ave_tf))

        # Augmented
        tfd_a = (tf * 0.5 / max_tf) + 0.5

        doc_length_n += math.pow(tfd_n, 2)
        doc_length_l += math.pow(tfd_l, 2)
        doc_length_a += math.pow(tfd_a, 2)
        doc_length_ave += math.pow(tfd_ave, 2)
        result[term] = [[docId, term_frequencies[term]]]

    other_data[docId] = (
        math.sqrt(doc_length_n),
        math.sqrt(doc_length_l),
        math.sqrt(doc_length_a),
        math.sqrt(doc_length_ave),
        max_tf,
        ave_tf,
        court_name
    )

    return {
        'index': result,
        'other_data': other_data
    }


# MapReduce final reduce function - results in inverted_index and additional_data dicitionaries
def combine(data_list):
    index_result = {}
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

    return index_result


# Multiprocessing MapReduce
with mp.Pool(mp.cpu_count()) as pool:
    indexes = pool.map(mapper, docIds)

inverted_index = combine(indexes)

dictionary = {}
postings_file = open('postings.txt', 'ab')
dictionary_path = 'dictionary.txt'

print('Recording inverted index')
for key in inverted_index:
    payload = inverted_index[key]
    position = postings_file.tell()

    postings_file.write(pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL))
    dictionary[key] = position

postings_file.close()

print('Dumping dictionary...')
with open(dictionary_path, 'wb') as dictionary_handle:
    pickle.dump(dictionary, dictionary_handle, protocol=pickle.HIGHEST_PROTOCOL)

dictionary_handle.close()

print('Dumping additional data...')
with open('additional.txt', 'wb') as additional_data_handle:
    pickle.dump(additional_data, additional_data_handle, protocol=pickle.HIGHEST_PROTOCOL)

additional_data_handle.close()

print('Done!')
