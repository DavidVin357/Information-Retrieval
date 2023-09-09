#!/usr/bin/python3
import math
import pickle
import sys
import getopt
import heapq

from nltk import word_tokenize, sent_tokenize
from nltk.stem.porter import PorterStemmer


def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


class Node:
    def __init__(self, docId=None, next=None, termFrequency=1):
        self.docId = docId
        self.termFrequency = termFrequency
        self.next = next


class LinkedList:
    def __init__(self, head=None):
        self.head = head


with open('docIds.pickle', 'rb') as handle:
    all_docIds_length = len(pickle.load(handle))


def process_words(text):
    sentences = sent_tokenize(text)
    words = []
    for s in sentences:
        words.extend(word.lower() for word in word_tokenize(s))
    stemmer = PorterStemmer()
    return map(stemmer.stem, words)


def cosine_similarity(query, dictionary_path, postings_path):
    scores = dict()

    query_terms = process_words(query)
    postings_file = open(postings_path, 'rb')

    with open(dictionary_path, 'rb') as dictionary_file:
        dictionary = pickle.load(dictionary_file)

    query_frequencies = dict()
    query_length = 0

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
        doc_frequency, postings_list = pickle.loads(data)

        # calculate w(t, q)
        wq = math.log10(all_docIds_length / doc_frequency) * (1 + math.log10(query_term_frequency))

        query_length += pow(wq, 2)

        node = postings_list.head

        # get w(t, d) and add the product to final score the product of weights
        while node is not None:
            tfd = node.termFrequency
            docId = node.docId
            if docId in scores:
                scores[docId] += (1 + math.log10(tfd)) * wq
            else:
                scores[docId] = (1 + math.log10(tfd)) * wq
            node = node.next

    with open('docLengths.pickle', 'rb') as doc_lengths_handle:
        doc_lengths = pickle.load(doc_lengths_handle)

    heap = []
    query_length = math.sqrt(query_length)

    for docId in scores:
        # Limit heap to 100 entries
        heap_capacity = len(heap)
        if heap_capacity < 100:
            heapq.heappush(heap, (scores[docId] / doc_lengths[docId] / query_length, docId))
        else:
            heapq.heapreplace(heap, (scores[docId] / doc_lengths[docId] / query_length, docId))

    k = len(heap) if len(heap) < 10 else 10
    #  return ranked documents sorted by increasing docId
    return sorted(heapq.nlargest(k, heap), key=lambda x: (-x[0], x[1]))


def search_and_write(queries_path, output_path, dictionary_path, postings_path):
    input_queries_file = open(queries_path, 'r')
    output_file = open(output_path, 'w')

    queries = input_queries_file.read().splitlines()
    lines = []
    for q in queries:
        result_str = ''
        result = cosine_similarity(query=q, dictionary_path=dictionary_path, postings_path=postings_path)
        if len(result) > 0:
            result_str = ' '.join([str(r[1]) for r in result][:10])

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
