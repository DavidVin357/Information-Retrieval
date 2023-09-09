## Legal Case Information Retrieval

### Indexing Phase

The index construction happens in the `create_index` function of the index.py file.

To get the most optimal index structure both in terms of memory and performace, I firstly created a small self-made testing framework where a substantial index with data for different features was created, so that it could be used
for different kinds of IR improvements.
Specifically, the testing index included zones information and additional parameters for computing different SMART schemes.
[The code for test index construction and search testing can be found under bonus/index-experiments]

Interestingly, after testing and evaluating performances with different IR additions, I came to a simpler version of index which utilises `lnn-lpn` weighting scheme happening to be most performant both by my observations for the given sample queries and consistently improving scores in the leaderboard.

To optimize the indexing time, the python multiprocessing module was utilised together with an algortihm of the MapReduce type. This greatly improved indexing speed from 3-4 hours to approximately 40 minutes.

The indexing algorithm is thus as follows:

1. Read dataset.csv using pandas and retrieve all docIds from the resulting dataframe.
   Write the sorted docIds to a separate file to be used by search functionality.
2. The indexing part splits into two main functions which are the basis of MapReduce method: `mapper` and `combine`
3. The `mapper` function accepts docId and retrieves separately all zone components for it from dataframe, specifically content, title, date, and court name. It then creates a general `term_frequencies` dictionary which records zone frequencies for each term in the given document. After iterating over terms and recording all the frequencies, the data is aggregated in the result dictionary such that for each result[term] there is `[docId, termFrequencies]` mapping. There is no length computation for a document, as experimentally best SMART scheme for this dataset got to be `lnn-lpn`, so that no normalization is required by search.
4. The `combine` function receives the list of indexes for each docId and aggregates the `postings_list` for each term.
5. The actual indexing happens concurrently using python multiprocessing module. We create a pool with maximum available threads on the computer which calls the multiprocessing `map()` function that operates on docIds list concurrently, guaranteeing data integrity. After the concurrent `map()` phase is done, we simply call the final `combine()` method which returns the inverted_index with merged postings lists for each term.

### Experiments

1. To find the best weighting scheme, the initial testing index aggregated all the data for computing different weights, specifically it stored doc lengths for natural, logarithm, augmented and log ave term frequencies. Eventually, the iterative testing showed that the normalization part didn't play a positive role in the retrieval, and its removal improved search results, accelerated the index creation, and reduced its size. The final choice thus became `lnn-lpn` SMART scheme.

2. To represent zones, the frequencies were stored for each component in the list with frequencies corresponding to [content, title, date, court]. Unfortunately, the experiments with multiplying by additional weight when the word appeared in the title more than once didn't succeed. Nevertheless, the zoned frequency structure was left as it is, as the overhead was not too bad and the potential for results improvements with zones is still a possibility.
3. The final performance improvement experiment was to add impact ordering weight by evaluating the importance of court specified for each case according to the court hierarchy. However, it didn' add any additional value, so the decision was to go without it (the commented code section for that is still in search.py).

### Search Phase

As describe in the above "Experiments" section, the experimentally best search phase was simple
and efficient `lnn-lpn` weighting scheme. Indeed, by using it, the search not only got better scores in the leaderboard but also became faster.

I also experimented with two query refinement methods, which are Query Expansion and Pseudo-Relevant Feedback.
However, they didn't improve the relevance of results, so the decision was to go without any of them.
The code for both techniques is in the bonus directory.

To this end, the final implementation of search functionality came to be a simple cosine similarity function with following characteristics:

1. Logarithmic term frequency for both query and document
2. No normalisation for both query and document
3. Probability idf for the query and no idf for the document
4. The word processing does not treat boolean queries in any special way, just removing the "AND" operator if it's there and stripping phrasal queries into ordinary terms. It was done due to inefficiencies caused by bloated index when using n-words for phrasal queries.
5. The similarity-ranked result with all the documents is retrieved by `cosine_similarity` function and the results are written to a file inside the `search_write` function.
