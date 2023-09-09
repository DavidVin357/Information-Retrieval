#!/usr/bin/python3
from nltk import word_tokenize, sent_tokenize
from nltk.stem.porter import PorterStemmer
import pickle
import sys
import getopt


def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


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


class Node:
    def __init__(self, val=None, next=None):
        self.val = val
        self.next = next
        self.skip = None


class LinkedList:
    def __init__(self, head=None):
        self.head = head

    def __str__(self):
        if self is None:
            return ''
        result_str = ''
        node = self.head
        while node:
            result_str += str(node.val)
            if node.next:
                result_str += ' '
            node = node.next
        return result_str


def process_words(text):
    sentences = sent_tokenize(text)
    words = []
    for s in sentences:
        words.extend(word.lower() for word in word_tokenize(s) if word.isalnum())
    stemmer = PorterStemmer()
    return map(stemmer.stem, words)


operators = {'AND', 'OR', 'NOT'}


def is_operator(token):
    return token in operators


def is_word(token):
    return not is_operator(token) and token != '(' and token != ')'


# Parse query with Shunting-yard algorithm
def parse_query(query):
    tokens = word_tokenize(query)
    stemmer = PorterStemmer()

    precedence = {
        'OR': 0,
        'AND': 1,
        'NOT': 2
    }
    operator_stack = []
    output = []

    for token in tokens:
        if is_word(token):
            processed_token = stemmer.stem(token.lower())
            output.append(processed_token)

        elif token == '(':
            operator_stack.append(token)

        elif token == ')':
            while len(operator_stack) > 0 and operator_stack[-1] != '(':
                operator = operator_stack.pop()
                output.append(operator)

            if len(operator_stack) == 0:
                raise Exception('Invalid brackets closure')

            # remove ( bracket
            operator_stack.pop()

        elif is_operator(token):
            while (
                    len(operator_stack) > 0 and
                    operator_stack[-1] != '(' and
                    precedence[operator_stack[-1]] >= precedence[token]):
                    output.append(operator_stack.pop())

            operator_stack.append(token)

    operator_stack.reverse()
    output.extend(operator_stack)
    return output


with open('docIds.pickle', 'rb') as handle:
    all_docIds = sorted(pickle.load(handle))

all_docIds_length = len(all_docIds)


# LINKED LISTS OPERATIONS

# Find difference between 2 linked lists - used in AND NOT optimization
def linked_list_differece(l1, l2):
    res = LinkedList()
    last = None
    node1 = l1.head
    node2 = l2.head
    size = 0
    while node1 and node2:
        if node1.val == node2.val:
            node1 = node1.next
            node2 = node2.next
        elif node1.val < node2.val:
            if last is None:
                res.head = Node(node1.val)
                last = res.head
            else:
                last.next = Node(node1.val)
                last = last.next
            node1 = node1.next
            size += 1
        else:
            node2 = node2.next
    if node2 is None:
        last.next = node1
    return res, size


# Find difference between postings linked list and all docIds - used in general NOT operation
def not_difference(linked_list):
    res = LinkedList()
    last = None
    node = linked_list.head
    index = 0
    while node and index < all_docIds_length:
        if all_docIds[index] == node.val:
            index += 1
            node = node.next
        elif index < all_docIds_length and all_docIds[index] > node.val:
            node = node.next
        elif index < all_docIds_length and all_docIds[index] < node.val:
            if last is None:
                res.head = Node(all_docIds[index])
                last = res.head
            else:
                last.next = Node(all_docIds[index])
                last = last.next
            index += 1
    if node is None:
        for el in all_docIds[index:]:
            last.next = Node(el)
            last = last.next
    return res


# Merge 2 postings linked lists with handling duplicates on the flow
def two_merge(l1, l2):
    if l1 is None or l2 is None:
        return None
    res = LinkedList()
    last = res.head
    minNode = None

    node1 = l1.head
    node2 = l2.head
    while node1 and node2:
        if node1.val == node2.val:
            minNode = Node(node1.val)
            node1 = node1.next
            node2 = node2.next

        elif node1.val < node2.val:
            minNode = Node(node1.val)
            node1 = node1.next

        elif node2.val < node1.val:
            minNode = Node(node2.val)
            node2 = node2.next

        if last is None:
            res.head = minNode
            last = res.head
        else:
            last.next = minNode
            last = last.next
    if node1 is None:
        last.next = node2
    else:
        last.next = node1
    return res


# Intersect 2 linked lists - used in AND operation (specifically, intersect_ands)
def intersect(l1, l2):
    res = LinkedList()
    size = 0
    last = None
    if l1 is None or l2 is None:
        return None
    node1 = l1.head
    node2 = l2.head
    while node1 and node2:
        if node1.val == node2.val:
            new_node = Node(node1.val)
            if last is None:
                res.head = new_node
                last = res.head
            else:
                last.next = new_node
                last = last.next
            size += 1
            node1 = node1.next
            node2 = node2.next
        elif node1.val < node2.val:
            if node1.skip and node1.skip.val < node2.val:
                while node1.skip and node1.skip.val < node2.val:
                    node1 = node1.skip
            else:
                node1 = node1.next
        else:
            if node2.skip and node2.skip.val < node1.val:
                while node2.skip and node2.skip.val < node1.val:
                    node2 = node2.skip
            else:
                node2 = node2.next
    return res, size


# Intersect accumulated list of AND operands in one flow
def intersect_ands(ands):
    r = ands[0][0]
    size = 0
    for i in range(1, len(ands)):
        if ands[i][1] == 'NOT':
            r, length = linked_list_differece(r, ands[i][0])
        else:
            r, length = intersect(r, ands[i][0])
        size += length
    return r, size


def process_intermediate_query_element(element):
    p, op, size = element
    if op == 'AND':
        postings, size = intersect_ands(p)
    elif op == 'NOT':
        postings = not_difference(p)
        size = all_docIds_length - size
    else:
        postings = p
    payload = (postings, None, size)
    return payload


def search(query, dictionary_path, postings_path):
    if not query:
        return []
    result = []

    parsed_query = parse_query(query)
    with open(dictionary_path, 'rb') as handle:
        dictionary = pickle.load(handle)
    postings_file = open(postings_path, 'rb')

    # term_data format for result stack: (postings_linked_list, operation, size)
    for idx, el in enumerate(parsed_query):
        if el == 'AND':
            term_data1 = result.pop()
            term_data2 = result.pop()
            # Handling non-existing terms
            if term_data1 is None or term_data2 is None:
                result.append(None)

            # Existing terms logic
            else:
                ands = []
                postings1, op1, size1 = term_data1
                postings2, op2, size2 = term_data2

                # If operand is 'AND' - extend new ands by previous operands
                if op1 == 'AND':
                    ands.extend(postings1)
                # Otherwise, add operand to ands
                else:
                    ands.append(term_data1)
                if op2 == 'AND':
                    ands.extend(postings2)
                else:
                    ands.append(term_data2)

                # sort AND operands according to their sizes
                ands = sorted(ands, key=lambda x: x[2])

                # For last AND - compute intersection
                if idx == len(parsed_query) - 1:
                    postings, size = intersect_ands(ands)
                    payload = (postings, None, size)
                    result.append(payload)
                else:
                    size = ands[0][2]  # smallest length among all operands
                    payload = (ands, 'AND', size)
                    result.append(payload)

        if el == 'OR':
            term_data1 = result.pop()
            term_data2 = result.pop()
            # Handling non-existing terms
            if term_data1 is None and term_data2 is None:
                result.append(None)

            elif term_data1 is None:
                postings, op, size = process_intermediate_query_element(term_data2)
                payload = (postings, 'OR', size)
                result.append(payload)

            elif term_data2 is None:
                postings, op, size = process_intermediate_query_element(term_data1)
                payload = (postings, 'OR', size)
                result.append(payload)

            # Existing terms logic
            else:
                postings1, op1, size1 = process_intermediate_query_element(term_data1)
                postings2, op2, size2 = process_intermediate_query_element(term_data2)
                postings = two_merge(postings1, postings2)
                # approximate OR size by adding operands lengths
                payload = (postings, 'OR', size1 + size2)
                result.append(payload)

        if el == 'NOT':
            term_data = result.pop()
            if term_data is None:
                postings = LinkedList()
                last = None
                for docId in all_docIds:
                    if last is None:
                        postings.head = Node(docId)
                        last = postings.head
                    else:
                        last.next = Node(docId)
                        last = last.next
                result.append((postings, None, all_docIds_length))
            else:
                postings, op, size = process_intermediate_query_element(term_data)
                # For last NOT - compute difference
                if idx == len(parsed_query) - 1:
                    postings = not_difference(postings)
                    size = all_docIds_length - size
                    payload = (postings, None, size)
                    result.append(payload)
                else:
                    not_postings_length = all_docIds_length - size
                    payload = (postings, 'NOT', not_postings_length)
                    result.append(payload)

        if is_word(el):
            term_data = dictionary.get(el)
            if term_data is None:
                result.append(None)
            else:
                position, postings_length = term_data
                postings_file.seek(position)
                data = postings_file.read()
                postings = pickle.loads(data)
                payload = (postings, None, postings_length)
                result.append(payload)
    return result[0][0] if result[0] is not None else None


def search_and_write(output_path, queries_path, dictionary_path, postings_path):
    input_queries_file = open(queries_path, 'r')
    output_file = open(output_path, 'w')

    queries = input_queries_file.read().splitlines()
    result = []

    for q in queries:
        postings_linked_list = search(q, dictionary_path, postings_path)
        result_str = ''
        if postings_linked_list is not None:
            result_str = str(postings_linked_list)

        result.append(result_str + '\n')
    output_file.writelines(result)

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
