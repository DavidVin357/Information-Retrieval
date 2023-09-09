## Boolean Retrieval Model

### Index Construction Phase

The index is implemented with SPIMI approach inside functions `create_index` and `merge_indexes`.
They are combined and run inside the build_index function.

#### I (`create_index`)

The `create_index` function goes through each of the terms in all documents and records corresponding docIds for every term.
Additionally, while building the in-memory mapping of terms and docIds, it also checks for
the dictionary being under `MEMORY_LIMIT` which emulates real RAM constraints in the SPIMI indexing. After `MEMORY_LIMIT`
is reached, the mapping is dumped to the intermediate file which is in the folder indexes.

The `create_index` function is thus implemented with the following algorithm:

1. Get all docIds in descending order (for the resulting ascending order when adding to linked lists)
2. Write all docIds to a separate pickled file (for a future use by search)
3. Add docId to its term inside the index - avoid duplicates of the same terms from the same document, as `n_merge` function doesn't handle that on its own
4. After `MEMORY_LIMIT` is reached, write the dictionary to a separate file in 'indexes' folder with `shelve` (used for an easier access to specific terms during merging phase)

#### II (`merge_indexes`)

The merge_indexes function reads buffers from all the intermediate files in the 'indexes' directory and merges term
postings into `postings.txt` file without loading all the intermediate parts into RAM. It utilizes `n_merge` function that
implements an algorithm for merging n different-sized sorted linked lists into one. It also implements skip pointers
after the final postings list was created for a current term.

The `merge_indexes` is thus implemented with the following algorithm:

1. For every unique term recorded in `create_index`, get its postings linked lists from all the intermediate files
   in 'indexes' folder using shelve.
2. Run `n_merge` on collected linked lists to get the final postings list for a term
3. Go through each node of a postings list and add the skip pointer to the nodes with offset of `sqrt(length)` -
   we get the length from the `n_merge` function.
4. Dump the postings linked list into postings.txt using pickle
5. Record each postings list position and length to the `dictionary` variable
6. After all terms were processed, dump the `dictionary` into the dictionary.txt file using pickle

### Search Phase

#### I (General outline)

The search functionality is divided into several parts with the following appropriate functions for each one:

- Parsing input query with Shunting yard algorithm: `parse_query`
- Linked Lists manipulations:
  - `two_merge` - merges two linked lists with handling duplicates in the process, used for OR operation
  - `intersect` - intersects two linked lists, used as a core algorithm for AND operation
  - `not_difference` - find a difference between all_docIds list and the given linked list - used for a general
    (non-optimized) NOT operation
  - `intersect_ands` - used as an optimization algorithm for AND operation, intersects the list of accumulated
    continuous AND operands according to their sizes (from smallest to biggest)
  - `linked_list_differece` - finds a difference between first and second linked lists, used for an optimization
    of (x AND NOT y) operation where we want to remove elements of y linked list
    from x linked list rather than computing general (NOT y). It is a separate algorithm, as combining it with
    `not_difference` would force us to convert all_docIds to the linked list which takes additional time during search.
- Search functionality: `search()` goes through each element of parsed query and executes above manipulations
  to get the final linked list which contains relevant result
- Write functionality: `search_write()` calls `search()` and writes the final result
  to the given output file in a correct format

#### II (Search Functionality)

A more detailed description of `search()` for each element of parsed query is as following:

0. Create the `result` list which will hold intermediate values and later the final search output (linked list)

1. Each element is stored in as `(postings, operation, size)` tuple which allows
   to distinguish and optimize NOT & AND operations on the flow
2. There are 4 types of elements in the parsed query - 'word', 'AND', 'NOT', and 'OR' which are handled as following:

- Element is word:

  - find the corresponding postings in the postings.txt by using its position from dictionary.txt and push them to the result stack with operation set as `None`

- Element is AND:

   1. Create `ands` list to accumulate operands for the later optimization (by intersecting them all
      at once according to their sizes)
   2. Pop two operands from the result stack
   3. If some of its operands are 'AND' operations themselves, extend current ands list with them
   4. If the operands are not 'AND', add them to the list in a format
      ([...operands_postings], 'AND', estimated_size) where estimated_size is the smallest
      postings size in the postings operands list
   5. Sort `ands` by the size of its operands
   6. If AND is the last operation, execute `intersect_ands` on `ands` list. Otherwise, push
      the accumulated ands to the stack (it will be intersected when AND chain will be ended)

- Element is OR:

  1.  Pop two operands from the result stack
  2.  Process intermediate operands (in case they are NOT or AND operations)
  3.  Run `two_merge` on the two postings lists of the operands and push it to the stack
      as (postings, 'OR', size)

- Element is NOT:

  1.  Pop one operand from the result stack
  2.  Process intermediate operands (in case they are NOT or AND operations)
  3.  If NOT is last operation, run it on all docIds with `not_difference` and add the result to the
      payload
  4.  Otherwise, add (postings, 'NOT', size) for the later execution and possible optimization
