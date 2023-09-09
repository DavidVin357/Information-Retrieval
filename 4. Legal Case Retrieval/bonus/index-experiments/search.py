import pickle
import math

with open('additional.txt', 'rb') as other_data_handle:
    otherData = pickle.load(other_data_handle)

courts = {
    ('SG Court of Appeal', 'SG Privy Council',
     'UK House of Lords', 'UK Supreme Court', 'High Court of Australia', 'CA Supreme Court'): 1.4,

    ('SG High Court', 'Singapore International Commercial Court', 'HK High Court',
     'HK Court of First Instance', 'UK Crown Court', 'UK Court of Appeal', 'UK High Court',
     'Federal Court of Australia', 'NSW Court of Appeal', 'NSW Court of Criminal Appeal',
     'NSW Supreme Court'
     ): 1.2
}


def court_importance(court):
    for key in courts:
        if court in key:
            return courts[key]
    return 1


def cosine_similarity(query_terms, dictionary_path, postings_path, tf_method, with_titles=False, with_courts=False):
    with open('docIds.txt', 'rb') as handle:
        all_docIds_length = len(pickle.load(handle))

    scores = dict()

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
        wq = math.log10(all_docIds_length / docFrequency) * (1 + math.log10(query_term_frequency))
        # wq = 1 + math.log10(query_term_frequency)

        for node in postings_list:
            # termFrequency = node[1]
            frequencies = node[1]
            weight = 1
            # term is in title
            if frequencies[1] > 0 and with_titles:
                weight = 1.4

            docId = node[0]

            max_tf = otherData[docId][4]
            ave_tf = otherData[docId][5]

            smart_map = {
                'tf_n': lambda tf: tf,
                'tf_l': lambda tf: 1 + math.log10(tf),
                'tf_a': lambda tf: (tf * 0.5 / max_tf) + 0.5,
                'tf_ave': lambda tf: (1 + math.log10(tf)) / (1 + math.log10(ave_tf)),
            }

            tf = sum(node[1])
            tfd = smart_map[tf_method](tf)

            if docId in scores:
                scores[docId] += tfd * wq * weight
            else:
                scores[docId] = tfd * wq * weight

    result = []
    for docId in scores:
        docLengths_map = {
            'tf_n': otherData[docId][0],
            'tf_l': otherData[docId][1],
            'tf_a': otherData[docId][2],
            'tf_ave': otherData[docId][3],
        }

        docLength = docLengths_map[tf_method]
        court = otherData[docId][3]
        court_weight = court_importance(court) if with_courts else 1

        result.append((court_weight * scores[docId], docId))

    return sorted(result, key=lambda x: -x[0])
