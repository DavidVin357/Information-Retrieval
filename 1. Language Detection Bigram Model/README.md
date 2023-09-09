## Language Detection Bigram Model
Language Model for Information Retrieval course at NUS to distinguish text in Indonesian, Malaysian and Tamil languages.

### Building Model

- The build_LM function consists of 2 sub-functions being called in the end:
  the construct_gram_model and calculate_probabilities.

- The construct_gram_model algorithm:

  1. Create initial scaffold of Language Model with the following structure:
     {
     language1: {total_frequency: x, chunks: {chunk1 : c1_freq, chunk2: c2_freq, ...}},
     language2: {...},
     ...
     }
  2. Go through each line of the file and extract language and text components
  3. Iterate over the text and get every 4-letter chunk of it
  4. If chunk is new in the current model's language, set its frequency as 2 (first occurrence + add-1 smoothing combined),
     and add 2 to total frequency
  5. Otherwise, add each existing chunk occurrence as 1 to its own frequency and total frequency
  6. Add the chunks' frequencies to other languages which don't have them as 1 (zero occurrence but add-1 smoothing applied)

  - Note: By testing two variants in the end, I decided not to add START and END paddings ("SSS" & "EEE") to each line,
    as they only decreased the final accuracy from 95% to 90%

- The calculate_probabilities algorithm:

  1. For every language, calculate probabilities through dividing chunk frequency by total frequency
  2. We get the following probability-based Language Model as the final result of build_LM:
     {
     language1: {chunk1: c1_prob, chunk2: c2_prob ...},
     language2: {...},
     ...
     }

  - Note: The Decimal number is used for chunks frequency & total frequency,
    as it gives much better precision than float in the division and later multiplication

- Return Value:
  build_LM ends with calling the construct_gram_model and calculate_probabilities functions
  and returning probability-based Language Model

### Testing Model

- The algorithm of test_LM is as following:
  1. For each line of input file, create the following initial "prediction" dictionary:
     {
     lang1: 1,
     lang2: 1,
     ...
     }
  2. Iterate through each 4-letter chunk of the line
  3. Go through each language in computed LM and check for a chunk existence.
     If the chunk is there, multiply the prediction language probability by the chunk's probability
  4. Remove from a prediction dictionary languages with probability 1:
     it means that no chunk from these languages in the computed LM was found for a current line
  5. If filtered prediction dictionary is empty, it means no given language fits the line, thus output "other"
  6. Otherwise, get the language with maximum probability in a filtered_prediction and output it in the prediction file
  7. Go to the next line and repeat the procedure

### Evaluation

- After running build_test_LM.py and eval.py, the resulting accuracy was 95%
  with 11th line not being identified as "other"
