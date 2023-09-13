# from keras.preprocessing.text import Tokenizer # inutile
# from keras import backend as K # inutile
import numpy as np
import re
from pathlib import Path
import random
from transformers import pipeline
import os

from backend.generer_poesie import predict, get_alignment_indices, sample
import utils.config as conf

#debug allows printing of detailed debug info in TERMINAL
def adapt_poem_with_models(poem,
                           models, #For the english version we only use the roBERTa models, the textgenrnn models are not loaded, thus trying to use them will not work
                           associations_file_path,
                           word_list_path,
                           mixing_numbers,
                           temperature,
                           debug=False,
                           textgen_select=False, #This should stay false, as we are not using the textgenrnn models for word selection
                           roberta_replace=True, #This should stay true, as we are using the roBERTa models for word replacement
                           roberta_models=[]):

    ASSOCIATIONS_PATH = Path(associations_file_path)
    WORD_LIST_PATH = Path(word_list_path)

    mixing_numbers = np.asarray(eval(mixing_numbers))
    mixing_percentages = mixing_numbers / 100.
    emotion_association_model = load_word_associations(ASSOCIATIONS_PATH)

    # Load corresponding emotion word list.
    wordlist = load_word_list(WORD_LIST_PATH)

    # Get candidate word locations.
    if textgen_select: #DEPRECATED
        candidate_slices = select_candidate_words_with_textGenRnn(
            poem,
            models,
            list(mixing_numbers),
            temperature,
            debug=debug,
        )
    else:
        candidate_slices = select_candidate_words(
            poem,
            mixing_numbers,
            emotion_association_model,
            wordlist,
        )

    if debug:
        # Display text with brackets around candidate words...
        to_modify_text = poem
        for candidate_slice in reversed(sorted(candidate_slices)):
            to_modify_text = (
                to_modify_text[:candidate_slice.start]
                + "["
                + to_modify_text[candidate_slice.start:candidate_slice.stop]
                + "]"
                + to_modify_text[candidate_slice.stop:]
            )
        print('TEXT TO MODIFY\n', to_modify_text, '\n')

    
    if roberta_replace:
        modified_text, context = replace_with_roberta(poem, 
                                                        roberta_models, 
                                                        mixing_numbers, 
                                                        candidate_slices,
                                                        debug=debug
                                                       )
        if debug:
            print('MODIFIED TEXT', modified_text, '\n')
        return(modified_text,context)
        
    else : #DEPRECATED
        reference_text = poem
        context = ''
        prev_slice = slice(0, 0)
        candidate_prediction_tuples = []

        ##############


        # for each word we've selected to change (starting from the beginning), 
        # 1st loop: we consider as context from the beginning of 
        # poem till the beginning of the first word we want to change.
        # 2nd loop: prev_slice = previous candidate slice, 
        # and added prediction to context, add to context what there is between 1st generated
        # word until new word to change, and so one.
        # for each word to change, save the generated words and locations (slices)

        # Build the predictions while maintaining the context updated
        for candidate_slice in sorted(candidate_slices):
            context += reference_text[prev_slice.stop:candidate_slice.start]
            prev_slice = candidate_slice

            candidate = poem[candidate_slice.start:candidate_slice.stop] # word to change
            pred = predict_next_word(context,
                                candidate,
                                models,
                                mixing_percentages,
                                temperature)
            pred = pred.strip()
            context += pred

            candidate_prediction_tuples.append((
                candidate_slice,
                pred
            ))

        # add final generated word
        context += reference_text[prev_slice.stop:]

        # string similarity with a (fairly small) dictionary
        # Returns (raw_final_poem, all_replacements) 
        corrections = check_dictionary_poem(context, get_rhyming_array())

        # context = poem = dictionary_corrected poem
        context = corrections[0]

        # I'm not sure I understand what this does, have we not added already the new words to context and corrected it?
        # check better what check_dictionary_poem() does
        updated_tuples = []
        for (cand, pred) in candidate_prediction_tuples:
            is_updated = False
            for corr in corrections[1]:
                for (old_value, new_value) in corr.items():
                    if pred in old_value:
                        if debug: print('Correction: ' + str(pred) + ' -> ' + str(new_value))
                        updated_tuples.append((cand, new_value))
                        is_updated = True
            if not is_updated:
                updated_tuples.append((cand, pred))

        # Apply corrections
        candidate_prediction_tuples = updated_tuples

        # Build the text with metadata for kivy
        modified_text = reference_text
        for candidate_prediction in reversed(candidate_prediction_tuples):
            modified_text = (
                modified_text[:candidate_prediction[0].start]
                + "[u]"
                + candidate_prediction[1]
                + "[/u]"
                + modified_text[candidate_prediction[0].stop:]
            )

        if debug:
            print('MODIFIED TEXT', modified_text, '\n')
            #print('CONTEXT', context, '\n')

        return (modified_text, context)

def load_roberta_models(model_names):
    loads = []
    for model_name in model_names:
        loads.append(pipeline("fill-mask", model = conf.MODELS_ROB_PATH + '/' + model_name, # os.path.join(conf.MODELS_ROB_PATH, model_name), 
                                           tokenizer = conf.MODELS_ROB_PATH + '/' + model_name, # os.path.join(conf.MODELS_ROB_PATH, model_name), 
                                           top_k=5))
    return loads

def replace_with_roberta(poem, models, mixing_numbers, candidate_slices, debug=False):
        
    #get the models that will replace each word
    replacement_models = random.choices(models, weights = mixing_numbers, k = len(candidate_slices))
    context = poem #poem without [u] & [/u]
    
    #for each word : (start from last to add [u] easily)
    # 1. Create a mask and get the 5 most likely words
    # 2. Choose this word randomly based on score
    # 3. replace the word in the poem and keep going
    for i,candidate_slice in enumerate(reversed(sorted(candidate_slices))):
        word = ""
        j = 0
        old_word = context[candidate_slice.start:candidate_slice.stop]
        pred = replacement_models[i]('<mask>'.join([context[:candidate_slice.start],context[candidate_slice.stop:]]))
        weights = [word['score'] for word in pred]
        while len(word) <= 1 or word == old_word: #avoid punctuations and same word
            chosen_index = random.choices(range(len(pred)), weights = weights)[0]
            word = pred[chosen_index]['token_str']

            word = word.replace(" ","") #rare case where there is a blank space in the word
            
            #check if want to replace with same word, then disallow it
            if word == old_word:
                weights[chosen_index] = 0
                
            #if we went 5 times without finding a word that's not a punctuation, 
            #just take the same word (very rare, avoid rare crash)
            if j > 5:
                word = old_word
                break
            j += 1 #avoid deadlock if very unlucky
        
        #update poem and context
        if context[candidate_slice.start-1:candidate_slice.start] == "\n" : #capitalize first letter of new line
            word = word.capitalize()
        context = word.join([context[:candidate_slice.start],context[candidate_slice.stop:]])
        poem = (f'[u]{word}[/u]').join([poem[:candidate_slice.start],poem[candidate_slice.stop:]])
        
    return (poem,context)
    
def letter_probabilities(text, models, mixing_percentages, temperature): #DEPRECATED
    
    model = models[0] # actual model
    vocabs = models[1] # char2idx
    indices_chars = models[2] # idx2char
    
    text_encoding = ['<s>']
    letter_probabilities = []

    for c in text:

        #probabilities for each letter in current context
        pred = predict(text_encoding, model, vocabs, indices_chars, 
                       np.array(mixing_percentages) / 100,
                       alignments = get_alignment_indices(vocabs), 
                       temperature = temperature)
        #get the probability of current letter
        vocab_pos = mixing_percentages.index(max(mixing_percentages))
        current_probability = pred[vocabs[0][c]] #taking the heighest represented vocab
                                                         #does not work with a combinaison of models
        
        letter_probabilities.append((c, current_probability))
        text_encoding += c   
        
    return letter_probabilities

def word_probabilities(text, models, mixing_percentages, temperature, get_word_slices=False, perplexity=False): #DEPRECATED
    
    letter_probs = letter_probabilities(text,models,mixing_percentages, temperature)
    counter = 0
    current_pos = 0
    current_sum = 0
    current_word = ""
    word_start = True
    current_word_start = 0
    word_list = list()
    punctuation = ['.', ',', ':', ';', '!', '?', ' ', '\n','\'']
    
    for letter in letter_probs:
        
        if letter[0] not in punctuation:
            if word_start:
                word_start = False
                current_word_start = current_pos
            if perplexity:
                current_sum += -(math.log(letter[1]))
            else:
                current_sum += letter[1]
            current_word += letter[0]
            counter += 1
        elif counter != 0:
            if get_word_slices:
                word_list.append(((current_word, '{:.10f}'.format(current_sum/counter)), slice(current_word_start,current_pos)))
            else:
                word_list.append((current_word, '{:.10f}'.format(current_sum/counter)))
            current_sum = 0
            current_word = ""
            counter = 0
            word_start = True
        
        current_pos += 1
        
    return word_list

def select_candidate_words_with_textGenRnn(text, models, mixing_percentages, temperature, debug=False): #DEPRECATED
    
    #get word probabilities for general and thematic/emotion models
    word_list_general = word_probabilities(text, model_general, [1], temperature)
    word_list_models = word_probabilities(text, models, mixing_percentages, temperature, get_word_slices=True)
    #word_list_general : [(word,proba)]
    #word_list_models : [((word,proba),slice)]
    
    #compute difference
    proba_diff = []
    #proba_diff : [(slice, diff)]
    for i in range(len(word_list_general)):
        proba_diff.append((word_list_models[i][1], float(word_list_models[i][0][1]) - float(word_list_general[i][1])))
    
    #sort
    proba_diff.sort(key=(lambda x: x[1]))
    candidate_slices = list()
    
    if(debug):
        print(proba_diff)
    
    #select a word for 12 words, and don't consider stop words (len <= 3) and first few word of sentence
    i = 0
    n = int(len(proba_diff)/12) + 0.8
    while len(candidate_slices) < n:
        curr_slice = proba_diff[i][0]
        if (curr_slice.stop - curr_slice.start > 3) and curr_slice.start != 0:
            candidate_slices.append(proba_diff[i][0])
        i += 1
        
    return candidate_slices


def predict_next_word(context, #DEPRECATED
                      candidate,
                      models,
                      mixing_percentages,
                      temperature):
    text = ['<s>']
    punctuation = ['.', ',', ':', ';', '!', '?', ' ']

    emotions = models[0]
    vocabs = models[1]
    indices_chars = models[2]

    # Define some characters we don't want the models to generate
    nums = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    chars_forbidden = ['\n', '↵', '(', ')', '"', '\t'] + nums
    idxs_forbidden = []

    for idx, char in list(indices_chars[0].items()):
        if char in chars_forbidden:
            idxs_forbidden += [idx]
    idxs_forbidden += [0]

    # Get correct vector alignments
    alignments = get_alignment_indices(vocabs)

    text += context
    new_word = []

    text_to_encode = text[:] + new_word
    next_char = " "
    while next_char not in punctuation:
        pred = predict(text_to_encode, emotions, vocabs, indices_chars,
                mixing_percentages, alignments, temperature)
        next_index = sample(pred, temperature, idxs_forbidden)
        next_char = indices_chars[0][next_index]

    new_word += [next_char]
    min_len = 4
    i = 0

    while i < min_len or (next_char not in punctuation and i >= min_len):
        i += 1
        text_to_encode = text[:] + new_word
        pred = predict(text_to_encode, emotions, vocabs, indices_chars,
                   mixing_percentages, alignments, temperature)
        next_index = sample(pred, temperature, idxs_forbidden)
        next_char = indices_chars[0][next_index]
        new_word += [next_char]

    pred = ''.join(new_word)

    # Trim leading and trailing punctuation
    pred = pred.strip(''.join(punctuation))

    return pred


# by Aris
def select_candidate_words(
    input_text,
    vector,
    word_associations,
    word_list,
    conservativeness=1,
    max_prop_candidates=0.1,
    ):
    """Given a text, an emotion vector, a word-emotion association array,
    the corresponding emotion word list, an optional minimum conservativeness
    ratio (default 1 is neutral, 2/1 is twice as conservative and 1/2 is
    half as conservative), an optional maximum proportion of candidate words
    (default 0.1), returns a list of slices indicating the location of optimal
    words to replace (i.e. those that are most atypical of the requested
    emotions.
    """

    # Get conservability score...
    conservability_scores = np.dot(
        word_associations,
        np.array(vector),
    )

    # Get list of emotion words in increasing order of conservability...
    sorted_indices = np.argsort(conservability_scores)
    replaceable_words = list(word_list[sorted_indices])

    # Exclude when conservability > emotion vector sum / conservativeness...
    to_exclude = word_list[
        conservability_scores >= sum(vector) / conservativeness
    ]
    replaceable_words = [w for w in replaceable_words if w not in to_exclude]
    random.shuffle(replaceable_words) # Added shuffle for more variety -Teo

    # Initialize list of candidate word locations and get text length.
    candidate_slices = list()
    text_length = len(re.findall(r"\w+", input_text))

    # While max proportion of candidates hasn't been reached...
    while len(candidate_slices) / text_length < max_prop_candidates:

        # Terminate loop if replaceable word list is empty...
        if not replaceable_words:
            break

        # Search for next most replaceable word...
        replaceable_word = replaceable_words.pop(0)
        matches = re.finditer(r"\b" + replaceable_word + r"\b(?i)", input_text)
        for match in matches:
            candidate_slices.append(slice(match.start(), match.end()))

    return candidate_slices


# by Aris
def load_word_associations(path):
    """Given the path to a word-emotion association model, opens and
    deserializes it as a numpy array."""
    try:
        with open(path, mode="rb") as input_file:
            return np.load(path)
    except IOError:
        print("Couldn't open file", path)
        exit()


# by Aris
def load_word_list(path):
    """Given the path to a list of emotion words (row headers of the
    word-emotion association model), opens it and stores them in an array."""
    try:
        with open(path, mode="r", encoding = "utf-8") as input_file:
            return np.array(input_file.read().split("\n"))
    except IOError:
        print("Couldn't open file", path)
        exit()
