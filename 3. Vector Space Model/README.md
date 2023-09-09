## Vector Space Model Retrieval

### Indexing Phase

The index construction happens in the `create_index` function of the index.py file.

1. For each document traversed within a loop, the `term_frequencies` dictionary is created that is later used for document vector length calculation. The frequency is incremented each time the same term is met.

2. The inverted index is filled with the data in format of `[docFrequency, postings_list]` for each term. The postings list is a linked list with each node having docId and termFrequency for the given term.

3. The inverted index construction algorithm is as following:

   1. If new term for the index is found, add it to the index with a docFrequency=1 and linked list having one element (head)
   2. If already existing term for the index is being met, and it **_was_** already seen in the current document, increment
      the termFrequency for this document node (with `docIds` being sorted in descending order for traversal, it happens to be the first node of the linked list).
   3. If already existing term for the index is met, but it **_was not_** yet met for the current document, add the node
      to the postings list and increment docFrequency for the current term.

4. Finally, we calculate the vector length for each document using `term_frequencies` dictionary where the length equals to a `sqrt(sum(tfs))` with `tf = (1 + log10(term_frequency))`.

5. The `dictionary`, `postings`, and `doc_lengths` dictionary are pickled to the corresponding files

### Search Phase

The main search logic happens in the `cosine_similarity` function where we calculate cosine similarity between
query and each document using `lnc.ltc` scheme.

The `cosine_similarity` algorithm is as follows:

1. Create `scores` dictionary which will hold normalized similarity score for each `docId` and given query.

2. Record raw term frequencies for each word inside the query (for later query weight calculation).

3. For each term in the query, we calculate its weight using `tf-idf` scheme by using `query_frequency` and `doc_frequency` for the current term. We then find postings list of documents for this term and calculate the weights for each `docId` using the recorded term frequencies from the indexing stage.

4. We add the squared `tf-idf` to the `query_length` which is used for cosine normalization for queries.

5. For each term `t` that belongs to query `q` and doc `d`, add `w(q, t) \* w(d, t)` to corresponding `scores[docId]`
   which gradually constructs the whole dot product for the given query vector and doc vector.

6. Finally, the normalization is applied to the dot product of each query-doc similarity score through dividing the
   score by a `doc_length` of the current doc vector (recorded in the docLengths.pickle file during indexing phase). It is also normalized with the query vector length as asked in the requirements, even though the same query length doesn't affect comparison between scores for the ranked retrieval.

7. The normalized scores are added to a heap with capacity of 100 entries and top 10 or less documents with the greatest scores are popped from it and returned in the end.

After getting the most similar <=10 documents for the given query, `search_and_write` function records them to the given output file.
