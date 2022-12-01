import torch
import numpy as np
import re
from datetime import datetime
import random
import utils.config as conf
import nltk
#nltk.download('punkt') # must run it *once* to download resource
from nltk.tokenize import word_tokenize
import pickle
import difflib
import random

from backend.correct_with_dictionary import postprocessing
from backend.generer_poesie import flatten


def get_rhyming_dictionaries(path=conf.RIME_PICKLE_FILE):
    """Dictionaries of {word: [perfect_rhyme, assonant_rhyme]},
    and {perfect_rhyme : [words..]} and {assonant_rhyme : [words]}
    """
    pickle_in = open(path,"rb")
    word2rhymes, perfect_rhyme2words, assonant_rhyme2words = pickle.load(pickle_in)
    return word2rhymes, perfect_rhyme2words, assonant_rhyme2words


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

    punctuation = ['.', ',', ',', ':', ';', '!', '?', ' ', '-']

    tok_verse = word_tokenize(verse, language='english')
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


def get_candidate_rhymes(word_to_replace, word, rhyming_dicts):
    """
    Given a word and three dictionaries (word->rhymes, perfect_rhymes->words,
    assonant_rhymes->words), checks if word is in first one, and if not finds
    the most similar word which is in the first one.
    Returns its perfect rhymes (if available) or assonant or empty list.
    """
    word2rhymes, perfect_rhyme2words, assonant_rhyme2words = rhyming_dicts
    
    word = word.lower()
    if word not in word2rhymes:  # find similar words
        try:
            word = difflib.get_close_matches(word, list(word2rhymes.keys()))[0]
        except:
            try:
                word = difflib.get_close_matches(word, list(word2rhymes.keys()), cutoff=0.25)[0]
            except:
                word = random.sample(word2rhymes.keys(), 1)[0]

    perfect_rhyme = word2rhymes[word][0]
    perfect_rhyme_candidates = [w for w in perfect_rhyme2words[perfect_rhyme] if w != word]
    # check if there are words that have perfect rhyme
    if len(perfect_rhyme_candidates) != 0:
        rhyme = perfect_rhyme
        candidates = perfect_rhyme_candidates
    # if not, check if there are words that have assonant rhyme
    else:
        assonant_rhyme = word2rhymes[word][1]
        assonant_rhyme_candidates = [w for w in assonant_rhyme2words[assonant_rhyme] if w != word]
        if len(assonant_rhyme_candidates) != 0:
            rhyme = assonant_rhyme
            candidates = assonant_rhyme_candidates
        # if not, return original word
        else:
            rhyme = ""
            candidates = []
    
    return rhyme, candidates


def seq_prob(verse_idx, strophe, old_verse, candidate, models):
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


def apply_rhyming_scheme(poem,
                          models,
                          rhyming_scheme,
                          outfile_directory=conf.OUTPUT_DIRECTORY_FILE,
                          print_into_file=False,
                          d=False,
                          n_candidates=30):
    """
    Gets the poem from the previous stage, and according to the rhyming scheme
    (e.g., ABBA ABBA CCD EDE, etc.), changes sends of lines to make them rhyme.
    n_candidates : how many candidate words to rank with the language model
    print_into_file : used to debug only (saves to disk before & after rhyme)
    d=True : print of detailed debug info in terminal
    """
    punctuation = ['.', ',', ',', ':', ';', '!', '?', ' ', '-']
    tok_poem = tokenize_poem(poem) # segment poem into stanzas and verses

    new_poem = []
    new_poem_markup = []
    used_candidates = []
    strophes_scheme = rhyming_scheme.split(' ')
    
    rhyming_dicts = get_rhyming_dictionaries() # loads 3 dictionaries
    
    all_rhymes = dict([(c, '') for c in set(rhyming_scheme) if not c == ' '])

    for strophe_idx in range(len(tok_poem)):
        strophe = tok_poem[strophe_idx]
        new_strophe = []
        new_strophe_markup =[]

        for verse_idx in range(len(strophe)):
            full_old_verse = strophe[verse_idx]
            all_probs = []
            punct, word, old_verse = process_verse(full_old_verse)
            verse_scheme = strophes_scheme[strophe_idx][verse_idx]
            if d: 
                print('\tStanza: {} Verse: {} Rhyme: {}'.format(strophe_idx+1, verse_idx+1, verse_scheme))
                print(all_rhymes[verse_scheme])

            if all_rhymes[verse_scheme] == '':  # if it is a new rhyme leave it as is
                all_rhymes[verse_scheme] = word
                final_word = word
                final_word_markup = word
                rime = 'nochange'
            else: # if it is not a new rhyme
                rime, candidates = get_candidate_rhymes(word, all_rhymes[verse_scheme], rhyming_dicts)
                if d: print("#1a", candidates)
                candidates = [i for i in candidates if i not in used_candidates and len(i) > 1]
                if d: print("#1b", candidates)

                if len(candidates) == 0:
                    candidates = [word]

                if len(candidates) < n_candidates:
                    n_candidates = len(candidates)

                random.shuffle(candidates)
                random_candidates = random.sample(candidates, n_candidates)

                if d: 
                    print('\t\tALL CANDIDATES:', len(candidates), '\n')
                    if len(candidates) < 100:
                        print('\t\t', word, rime, candidates, '\n')

                for candidate in random_candidates:
                    prob = seq_prob(verse_idx, strophe, old_verse, candidate, models)
                    all_probs += [prob]

                best = np.argmax(all_probs) # np.argsort(all_probs)[::-1] # why sort if we only use max?
                best_prob = all_probs[best]
                final_word = random_candidates[best]
                final_word_markup = "[u]" + final_word + "[/u]"

            if len(punct) != 0:
                best_riming_verse = old_verse + ' ' + ''.join(final_word) + punct[0]
                best_riming_verse_markup = old_verse + ' ' + ''.join(final_word_markup) + punct[0]
            else:
                best_riming_verse = old_verse + ' ' + ''.join(final_word)
                best_riming_verse_markup = old_verse + ' ' + ''.join(final_word_markup)

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

    if d: 
        print('NEW POEM\n\n' + new_poem + '\n' + '~'*50 + '\n' + 'OLD POEM\n\n' + poem)
    if print_into_file:
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_RHYME") #Windows compatible
        with open(outfile_directory + now + '.txt', 'w') as f:
            f.write('NEW POEM\n\n' + new_poem + '\n' + '~'*50 + '\n' + 'OLD POEM\n\n' + poem)

    return (new_poem_markup, new_poem)


def make_it_rhyme(poem,
                     models,
                     rhyming_scheme,
                     outfile_directory=conf.OUTPUT_DIRECTORY_FILE,
                     n_candidates=30,
                     rime_syllables=2):
    """
    Calls apply_rhyming_scheme() with correct scheme and model mixing %s parameters.
    models: list of list of built models, their vocabs, and their indices_chars.
    In reality, all arguments of make_it_rhyme are passed identically, except the model (pass only pipeline). 
    """
    return apply_rhyming_scheme(poem,
                               models[0],  # called from 'stage_4_rhyme.py' with only the general model (GPT-2)
                                           # 'models' has [pipeline, model, tokenizer] so we keep only the pipeline (?)
                               rhyming_scheme,
                               outfile_directory,
                               n_candidates=n_candidates)
