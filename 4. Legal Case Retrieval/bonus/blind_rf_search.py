import math
import pickle

from nltk import sent_tokenize
from nltk import word_tokenize
from nltk.stem.porter import PorterStemmer
import sys
import getopt


# Alternative search with blind RF feedback

def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


def process_words(text):
    stemmer = PorterStemmer()
    processed_words = []
    for word in word_tokenize(text):
        if word != 'AND' and word.isalnum():
            processed_words.append(stemmer.stem(word))
    return processed_words


query_vector = {}
docs_vector = {}


def cosine_similarity(query_terms, dictionary, postings_file):
    with open('docIds.txt', 'rb') as handle:
        all_docIds_length = len(pickle.load(handle))

    scores = dict()

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
        wq = max(0, math.log10((all_docIds_length - docFrequency) / docFrequency)) * (
                    1 + math.log10(query_term_frequency))

        query_vector[query_term] = wq

        for node in postings_list:
            frequencies = node[1]
            weight = 1
            # term is in title
            if frequencies[1] > 0:
                weight = 1.4

            docId = node[0]

            # l_tf
            tf = sum(frequencies)
            tfd = 1 + math.log10(tf)
            if docId in docs_vector:
                docs_vector[docId].update({
                    query_term: tfd
                })
            else:
                docs_vector[docId] = {
                    query_term: tfd
                }
            if docId in scores:
                scores[docId] += tfd * wq * weight
            else:
                scores[docId] = tfd * wq * weight

    result = []
    for docId in scores:
        result.append((docId, scores[docId]))

    return sorted(result, key=lambda x: -x[1])


def search_and_write(queries_path, output_path, dictionary_path, postings_path):
    input_queries_file = open(queries_path, 'r')
    output_file = open(output_path, 'w')
    queries = input_queries_file.read().splitlines()
    lines = []

    with open(dictionary_path, 'rb') as dictionary_file:
        dictionary = pickle.load(dictionary_file)
    postings_file = open(postings_path, 'rb')

    for q in queries:
        result_str = ''
        query_terms = process_words(q)
        # Initial result
        result = cosine_similarity(query_terms=query_terms, dictionary=dictionary, postings_file=postings_file)

        # blind rf: get top 10 docs and 10 worst docs
        top_docs = result[:10]
        low_docs = result[-10:]
        new_query = query_vector

        for term in query_vector:
            position = dictionary.get(term)
            if position is None:
                continue
            postings_file.seek(position)
            data = postings_file.read()
            postings_list = pickle.loads(data)

            # find a centroid of top docs and add its value to a corresponding term of new query vector
            for doc in top_docs:
                docId = doc[0]
                doc_values = [(1 + math.log10(sum(t[1]))) for t in postings_list if t[0] == docId]
                new_query[term] += 0.75 * sum(doc_values) / 10

            # find a centroid of low docs and substract its value from a corresponding term of a new query vector
            for doc in low_docs:
                docId = doc[0]
                doc_values = [(1 + math.log10(sum(t[1]))) for t in postings_list if t[0] == docId]
                new_query[term] -= 0.15 * sum(doc_values) / 10

        # Calculate scores for a new query vector
        new_scores = {}
        for term in query_vector:
            for docId in docs_vector:
                new_scores[docId] = docs_vector[docId][term] * new_query[term] if term in docs_vector[docId] else \
                new_query[term]
        result = []
        for docId in new_scores:
            result.append((docId, new_scores[docId]))

        result = sorted(result, key=lambda x: -x[1])

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
