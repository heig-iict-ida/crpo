# From Etape 1
import torch
import numpy as np
import re
from datetime import datetime
import random
import utils.config as conf


# New for Etape 3

import nltk # It is necessary to install it in the environment.
#nltk.download('punkt') # It is necessary to run it once to download it.
from nltk.tokenize import word_tokenize
import pickle
import difflib

from backend.correct_with_dictionary import postprocessing
from backend.generer_poesie import flatten


def get_rhyming_array (path=conf.RIME_PICKLE_FILE):

    pickle_in = open(path,"rb")
    warr = pickle.load(pickle_in)
    warr = np.array(warr, dtype=object)
    return warr


def tokenize_poem (text):
    """
    Tokenize poem into strophes and verses.
    """
    structured = []

    strophes = text.split('\n\n')
    for s in strophes:
        strophe = []
        verses = s.split('\n')
        for v in verses:
            strophe += [v]
        structured += [strophe]

    return structured


def process_verse (verse):
    """
    Given a verse, returns its final punctuation (if any), last word, and remainder
    of verse without either of the two.
    """

    punctuation = ['.', ',', ',', ':', ';', '!', '?', ' ']

    tok_verse = word_tokenize(verse, language='english') #changed to english -Teo
    # Remember punctuation
    if tok_verse[-1] in punctuation:
        original_punctuation = [tok_verse[-1]]
    else:
        original_punctuation = ''

    # Get last word
    if tok_verse[-1] in punctuation:
        if len(tok_verse) > 1:
            last_word = tok_verse [-2]
        else:
            last_word = ''
    else:
        last_word = tok_verse [-1]
    if "'" in last_word:
        last_word = last_word.split("'")[1]

    # Get new verse
    try:
        while tok_verse[-1] in punctuation:
            tok_verse = tok_verse[:-1]
    except IndexError:
        pass

    new_verse = ' '.join(tok_verse[:-1])
    new_verse = re.sub (r" ’ ",r'’', new_verse)
    new_verse = re.sub (r" \.", '.', new_verse)

    return original_punctuation, last_word, new_verse


def get_candidates_rime (word_to_replace, word, arr, all_phonemes, same_pos=True, n_syllable=2):
    """
    Given a word and an array, returns its pronunciation according to the array
    and a list of candidate words that have the same pronunciation.

    same_pos = whether we check for candidates with exclusively the same POS.

    n_syllable = how many of the syllables we count; n=1 means we just look at the last
    vowel in the pronunciation.
    """

#     uppercase = False
#     if word[0] != word[0].lower():
#         uppercase = True

    word = word.lower()

    word_in_array = np.where(arr[:,0] == word.lower())

    if (np.asarray(word_in_array)).shape[1] == 0:
        possibles = difflib.get_close_matches(word, arr[:,0])
        word_in_array = np.where(arr[:,0] == possibles[0].lower())
#         print('found similar word:', word, possibles[0])

    original = np.asarray(word_in_array)[0][0]
    word, rime, pos = arr[original]

    if n_syllable != 'all':
        rime = rime[-n_syllable:] #TODO syllables to phonemes

#     print('WORD:', word, '|', 'RIME:', rime, '|','POS:', pos)

    if  len(rime) < n_syllable :

        all_phonemes = get_rhyming_array()[:,1]

        nb_phonems = min(n_syllable,len(rime))
        for i in range(len(all_phonemes)):
            all_phonemes[i] = all_phonemes[i][-nb_phonems:]

        for i in range(len(all_phonemes)):
            all_phonemes[i] = "".join(all_phonemes[i])

    joined_rime = "".join(rime)

    if same_pos == True:
#         print('Same POS')
        word_to_replace = word_to_replace.lower()

        word_in_array = np.where(arr[:,0] == word_to_replace.lower())

        if (np.asarray(word_in_array)).shape[1] == 0:
            possibles = difflib.get_close_matches(word_to_replace, arr[:,0])
            word_in_array = np.where(arr[:,0] == possibles[0].lower())
    #         print('found similar word:', word, possibles[0])

        original = np.asarray(word_in_array)[0][0]
        word_to_replace, rime_to_replace, pos_to_replace = arr[original]

        idxs = np.asarray(np.where((all_phonemes == joined_rime) & (arr[:,2] == pos_to_replace)))
    else:
#         print('Any POS')
        idxs = np.asarray(np.where((all_phonemes == joined_rime)))
        

    candidates = (arr[idxs][0][:,0]).tolist()

#     if uppercase:
#         candidates = [i[0].upper() + i[1:] for i in candidates]

    candidates = [c for c in candidates if c.lower() != word.lower()]

    return rime, candidates

def seq_prob (verse_idx, strophe, old_verse, candidate,
             models):
    """
    Calculates probability of a sequence of old_verse + ending (candidate) word.
    """
   
    candidate_in_context = []
    for i in range(len(strophe)):
        candidate_in_context.append("<start>" + strophe[i])
    candidate_in_context[verse_idx] = "<start>" + old_verse + " " + candidate
    candidate_in_context = "\n".join(candidate_in_context) 
    tokenize_input = models[2].tokenize(candidate_in_context)
    tensor_input = torch.tensor([models[2].convert_tokens_to_ids(tokenize_input)])
    loss = models[1](tensor_input, labels=tensor_input)
    return -loss[0].item()

#print_into_file may be used to DEBUG ONLY (save to disk before and after rhyme)
#d allows printing of detailed debug info in TERMINAL
def apply_rhyming_scheme (poem,
                          models,
                          rhyming_scheme,
                          outfile_directory=conf.OUTPUT_DIRECTORY_FILE,
                          print_into_file=False,
                          d=False,
                          n_candidates=30,
                          rime_syllables=2):
    """
    Gets a poem raw (as the first stage generates it), and according to the rhyming scheme
    (e.g., ABBA ABBA CCD EDE, etc. [which is now missing]), returns it rhyming.

    n_candidates = for how many candidate words are we going to calculate their probability.

    rime_syllables = number of syllables that should rhyme
    """

    punctuation = ['.', ',', ',', ':', ';', '!', '?', ' ']


    tok_poem = tokenize_poem(poem)

    new_poem = []
    new_poem_markup = []

    used_candidates = []

    strophes_scheme = rhyming_scheme.split(' ')

    all_phonemes = get_rhyming_array()[:,1]

    nb_phonems = rime_syllables
    for i in range(len(all_phonemes)):
        all_phonemes[i] = all_phonemes[i][-nb_phonems:]

    for i in range(len(all_phonemes)):
        all_phonemes[i] = "".join(all_phonemes[i])

    all_rhymes = {}
    for l in ''.join(strophes_scheme):
        all_rhymes[l] = ''

    for strophe_idx in range(len(tok_poem)):

        strophe = tok_poem[strophe_idx]
        new_strophe = []
        new_strophe_markup =[]
        if d: print('\nStrophe {}\n'.format(strophe_idx + 1))

        for verse_idx in range(len(strophe)):

            full_old_verse = strophe[verse_idx]
            all_probs = []

            punct, word, old_verse = process_verse(full_old_verse)
#             if d: print('\t', punct, '|', word, '|', old_verse)
            if d: print('V: {} {}'.format(strophe_idx, verse_idx))

            verse_scheme = strophes_scheme[strophe_idx][verse_idx]

            if d: print('\tVerse {}  {}'.format((verse_idx + 1), verse_scheme))


            # If it is a new rhyme leave it as is
            if all_rhymes[verse_scheme] == '':

                all_rhymes[verse_scheme] = word
                final_word = word
                final_word_markup = word
                rime = 'nochange'

            # Not a new rhyme
            else:

                rime, candidates = get_candidates_rime(word, all_rhymes[verse_scheme],
                                                       get_rhyming_array(), all_phonemes,
                                                       same_pos=False, # or True
                                                       n_syllable=rime_syllables)

                candidates = [i for i in candidates if i not in used_candidates]
                candidates = [i for i in candidates if len(i) > 1]

                if len(candidates) == 0:
                    rime, candidates = get_candidates_rime(word, all_rhymes[verse_scheme],
                                                       get_rhyming_array(), all_phonemes,
                                                       same_pos=False,
                                                       n_syllable=rime_syllables)
                    
                    candidates = [i for i in candidates if i not in used_candidates]
                    candidates = [i for i in candidates if len(i) > 1]

                    if len(candidates) == 0:
                        candidates = [word]                       

                if len(candidates) < n_candidates:
                    n_candidates = len(candidates)

                random.shuffle(candidates)
                random_candidates = random.sample(candidates, n_candidates)

                if d: print('\t\tALL CANDIDATES:', len(candidates), '\n')
                if len(candidates) < 100:
                    if d: print('\t\t', word, rime, candidates, '\n')

                for candidate in random_candidates:

                    prob = seq_prob (verse_idx, strophe, old_verse, candidate,
                             models)

                    all_probs += [prob]

                highest_to_lowest = np.argsort(all_probs)[::-1]
                best = highest_to_lowest[0]
                best_prob = all_probs[best]
                final_word = random_candidates[best]
                final_word_markup = "[u]" + final_word + "[/u]"

            if len(punct) != 0:
                best_riming_verse = old_verse + ' ' + ''.join(final_word) + punct[0]
                best_riming_verse_markup = old_verse + ' ' + ''.join(final_word_markup) + punct[0]
                # best_riming_verse += ' | ' + verse_scheme + ' (' + rime + ')'
            else:
                best_riming_verse = old_verse + ' ' + ''.join(final_word)
                best_riming_verse_markup = old_verse + ' ' + ''.join(final_word_markup)
                # best_riming_verse += ' | ' + verse_scheme + ' (' + rime + ')'

            used_candidates += [final_word]

            best_riming_verse += '\n'
            best_riming_verse_markup += '\n'

            new_strophe += [best_riming_verse]
            new_strophe_markup += [best_riming_verse_markup]

        new_strophe += ['\n']
        new_strophe_markup += ['\n']

        new_poem += [new_strophe]
        new_poem_markup += [new_strophe_markup]

    raw = ''.join((flatten(new_poem)))
    new_poem = postprocessing(raw, punctuation)

    raw_markup = ''.join((flatten(new_poem_markup)))
    new_poem_markup = postprocessing(raw_markup, punctuation)

    both_poems = 'NEW POEM\n\n' + new_poem + '\n' + '~'*50 + '\n' + 'OLD POEM\n\n' + poem
    if d: print(both_poems)

    if print_into_file:

        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_RHYME") #Windows compatible
        with open(outfile_directory + now + '.txt', 'w') as f:
            f.write(both_poems)


    return (new_poem_markup, new_poem)


def make_it_rhyme   (poem,
                     models,
                     rhyming_scheme,
                     outfile_directory=conf.OUTPUT_DIRECTORY_FILE,
                     n_candidates=30,
                     rime_syllables=2):
    """
    Calls apply_rhyming_scheme() with correct scheme and model mixing %s parameters.

    models: list of list of built models, their vocabs, and their indices_chars.
    """

    return apply_rhyming_scheme(poem,
                               models[0],  # called from 'stage_4_rhyme.py' with only the general model (GPT-2)
                               rhyming_scheme,
                               outfile_directory,
                               n_candidates=n_candidates,
                               rime_syllables=rime_syllables)


def get_poem (poem):

    with open(poem, 'r') as p:
        raw = p.read()

    return raw
