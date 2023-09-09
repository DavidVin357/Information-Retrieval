#!/usr/bin/python3
import math
import os
import pickle
import sys
import getopt

from nltk import word_tokenize, sent_tokenize
from nltk.stem.porter import PorterStemmer

sys.setrecursionlimit(20000)


def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")


class Node:
    def __init__(self, docId=None, next=None, termFrequency=1):
        self.docId = docId
        self.termFrequency = termFrequency
        self.next = next


class LinkedList:
    def __init__(self, head=None):
        self.head = head


def process_words(text):
    sentences = sent_tokenize(text)
    words = []
    for s in sentences:
        words.extend(word.lower() for word in word_tokenize(s))
    stemmer = PorterStemmer()
    return map(stemmer.stem, words)


def create_index(documents_directory_path, postings_path, dictionary_path):
    inverted_index = dict()
    docIds = sorted([int(name) for name in os.listdir(documents_directory_path)], reverse=True)

    with open('docIds.pickle', 'wb') as handle:
        pickle.dump(docIds, handle, protocol=pickle.HIGHEST_PROTOCOL)

    terms = set()
    doc_lengths = dict()
    for docId in docIds:
        f = open(documents_directory_path + '/' + str(docId))
        text = f.read()
        words = process_words(text)

        term_frequencies = dict()
        for word in words:
            if word in term_frequencies:
                term_frequencies[word] += 1
            else:
                term_frequencies[word] = 1

            terms.add(word)
            node = Node(docId=docId, termFrequency=1)

            if word in inverted_index:
                # Get postings list for the existing term in the index
                postings_list = inverted_index[word][1]
                # New term for the current document
                if postings_list.head.docId != docId:
                    # new document, so increment docFrequency
                    inverted_index[word][0] += 1
                    # add new node to postings_list
                    node.next = inverted_index[word][1].head
                    inverted_index[word][1].head = node
                # Repeating term for this document (increment termFrequency)
                else:
                    inverted_index[word][1].head.termFrequency += 1

            # New term for the index: docFrequency=1
            else:
                inverted_index[word] = [1, LinkedList(head=node)]

        doc_length = 0
        for term, frequency in term_frequencies.items():
            tf = 1 + math.log10(frequency)
            doc_length += math.pow(tf, 2)

        doc_lengths[docId] = math.sqrt(doc_length)

    # clear existing postings file
    open(postings_path, 'w').close()

    # Write postings, dictionary, doc_lengths
    postings_file = open(postings_path, 'ab')
    dictionary = {}
    for term in terms:
        payload = inverted_index[term]
        position = postings_file.tell()

        postings_file.write(pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL))
        dictionary[term] = position

    with open(dictionary_path, 'wb') as dictionary_handle:
        pickle.dump(dictionary, dictionary_handle, protocol=pickle.HIGHEST_PROTOCOL)

    with open('docLengths.pickle', 'wb') as doc_lengths_handle:
        pickle.dump(doc_lengths, doc_lengths_handle, protocol=pickle.HIGHEST_PROTOCOL)


def build_index(in_dir, out_dict, out_postings):
    print('indexing...')
    create_index(documents_directory_path=in_dir, dictionary_path=out_dict, postings_path=out_postings)
    print('DONE!')


input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i':  # input directory
        input_directory = a
    elif o == '-d':  # dictionary file
        output_file_dictionary = a
    elif o == '-p':  # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_directory == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary, output_file_postings)
