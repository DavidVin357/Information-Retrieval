from query_expansion import expand_query
from search import cosine_similarity
from nltk import word_tokenize, sent_tokenize
from nltk.stem.porter import PorterStemmer

# The manual testing file for trying different experiments (SMART schemes, zone weighting, query expansion)
methods = ['tf_n', 'tf_l', 'tf_a', 'tf_ave']


def process_words(text):
    stemmer = PorterStemmer()
    processed_words = []
    for word in word_tokenize(text):
        if word != 'AND' and word.isalnum():
            processed_words.append(stemmer.stem(word))
    return processed_words


def search_and_write(with_expansion, tf_method, with_titles=False, with_courts=False):
    input_queries_file = open('queries.txt', 'r')
    output_file = open('results7.txt', 'a')
    queries = input_queries_file.read().splitlines()
    lines = []
    for q in queries:
        query_terms = expand_query(q) if with_expansion else process_words(q)
        result_str = ''
        result = cosine_similarity(query_terms=query_terms,
                                   dictionary_path='dictionary.txt',
                                   postings_path='postings.txt',
                                   tf_method=tf_method,
                                   with_titles=with_titles,
                                   with_courts=with_courts
                                   )
        if len(result) > 0:
            result_str = ' '.join([str(r[1]) for r in result[:10]])
        first_line = f"Query Expansion: {with_expansion}. TF method: {tf_method}. With titles: {with_titles}. With courts: {with_courts}"
        lines.append('\n' + first_line + '\n' + q + '\n')
        lines.append(result_str + '\n')

    output_file.writelines(lines)


def test():
    for method in methods:
        search_and_write(True, method)
        search_and_write(False, method)


test()
