#!/usr/bin/python3
import heapq
import math
import os
import pickle
import shelve
import shutil

import sys
import getopt

from nltk import word_tokenize, sent_tokenize
from nltk.stem.porter import PorterStemmer
import dbm.gnu as gdbm

sys.setrecursionlimit(20000)

# memory limit results in separate 11 index files
MEMORY_LIMIT = 250000

def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")


class Node:
    def __init__(self, val=None, next=None):
        self.val = val
        self.next = next
        self.skip = None


class LinkedList:
    def __init__(self, head=None):
        self.head = head


def process_words(text):
    sentences = sent_tokenize(text)
    words = []
    for s in sentences:
        words.extend(word.lower() for word in word_tokenize(s) if word.isalnum())
    stemmer = PorterStemmer()
    return map(stemmer.stem, words)


# All traversed terms
terms = set()


def create_index(documents_directory_path):
    count = 1
    inverted_index = dict()
    os.makedirs('indexes', exist_ok=True)
    docIds = sorted([int(name) for name in os.listdir(documents_directory_path)], reverse=True)
    with open('docIds.pickle', 'wb') as handle:
        pickle.dump(docIds, handle, protocol=pickle.HIGHEST_PROTOCOL)

    for docId in docIds:
        index_size = sys.getsizeof(inverted_index)
        # SPIMI: disk-based indexing
        if index_size > MEMORY_LIMIT:
            Shelf = shelve.Shelf(gdbm.open(f'indexes/{count}', 'c'))
            Shelf.update(inverted_index)
            Shelf.close()

            inverted_index.clear()
            count += 1

        f = open(documents_directory_path + '/' + str(docId))
        text = f.read()
        words = process_words(text)

        for word in words:
            terms.add(word)
            node = Node(val=docId)
            if word in inverted_index:
                # avoid duplicates by checking smallest value
                if inverted_index[word].head.val != docId:
                    node.next = inverted_index[word].head
                    inverted_index[word].head = node
            else:
                inverted_index[word] = LinkedList()
                inverted_index[word].head = node
        f.close()

    # Write last index
    Shelf = shelve.Shelf(gdbm.open(f'indexes/{count}', 'c'))
    Shelf.update(inverted_index)
    Shelf.close()


def n_merge(linked_lists):
    length = 0
    res = LinkedList()
    heap = []
    for l in linked_lists:
        heapq.heappush(heap, (l.head.val, l.head.next))

    last = None
    while heap:
        minVal, curr = heapq.heappop(heap)
        if last is None:
            res.head = Node(minVal)
            last = res.head
        else:
            last.next = Node(minVal)
            last = last.next
        length += 1
        if curr is not None:
            heapq.heappush(heap, (curr.val, curr.next))

    return res, length


def merge_indexes(postings_path, dictionary_path):
    postings_file = open(postings_path, 'ab')
    dictionary = {}

    indexes = sorted(os.listdir('indexes'), key=lambda s: int(s))
    shelves = [shelve.open(f'indexes/{i}') for i in indexes]
    for term in terms:
        postings, postings_length = n_merge([s.get(term) for s in shelves if (term in s)])

        pointers_offset = math.floor(math.sqrt(postings_length))
        node = postings.head
        count = 0
        skip_from = node

        while node:
            if count % pointers_offset == 0 and count < postings_length:
                if count > 0:
                    skip_from.skip = node
                    skip_from = node
            node = node.next
            count += 1

        position = postings_file.tell()

        postings_file.write(pickle.dumps(postings, protocol=pickle.HIGHEST_PROTOCOL))
        dictionary[term] = (position, postings_length)

    with open(dictionary_path, 'wb') as handle:
        pickle.dump(dictionary, handle, protocol=pickle.HIGHEST_PROTOCOL)

    handle.close()
    postings_file.close()
    for s in shelves:
        s.close()

    shutil.rmtree('indexes')


def build_index(in_dir, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print('indexing...')
    create_index(documents_directory_path=in_dir)

    merge_indexes(dictionary_path=out_dict, postings_path=out_postings)
    print('DONE!')
    # This is an empty method
    # Pls implement your code in below


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
