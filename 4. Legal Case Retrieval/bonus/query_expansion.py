import nltk

from nltk import word_tokenize
from nltk.corpus import wordnet as wn

from nltk.corpus import stopwords as sw

from nltk.stem.porter import PorterStemmer


def download_nltk_packages():
    nltk.download('wordnet')
    nltk.download('stopwords')


def process_words(text):
    stopwords = sw.words('english')
    processed_words = []
    for word in word_tokenize(text):
        print(word)
        if word != 'AND' and word.isalpha() and word not in stopwords:
            processed_words.append(word.lower())
    return processed_words


def stem_words(words):
    stemmer = PorterStemmer()
    return map(stemmer.stem, words)


def get_derived(word):
    stemmer = PorterStemmer()
    lemmas = [lemma for s in wn.synsets(word) for lemma in s.lemmas()]
    derived_forms = [l.derivationally_related_forms() for l in lemmas]
    result = [stemmer.stem(d[0].name()) for d in derived_forms if len(d) > 0]
    return result


def expand_query(query):
    words = process_words(query)
    result = set(stem_words(words))

    for word in words:
        derived_words = get_derived(word)
        stemmed_words = set(stem_words(derived_words))
        result = result.union(stemmed_words)
    return result
