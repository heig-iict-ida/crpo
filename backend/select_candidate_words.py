# -*- coding: utf-8 -*-
"""Module select_candidate_words.py

This module provides function select_candidate_words(), which selects optimal
word tokens to replace in a text given a model of word-emotion association
(stored in file emotions.npy) and a vector of emotion quantities (happiness,
sadness, aversion, in this order, in arbitrary units).

The module also provides function load_word_emotion_associations(), which opens
and deserializes the word-emotion association model as a numpy array, and
function load_emotion_word_list(), which opens the list of emotion words
(possible candidates for replacement, which are the row headers of the
word-emotion association model) and stores them in an array.
"""

import re
from pathlib import Path
import numpy as np

TEST_DATA = """— Enfant charmant à voir,
Et couronné de roses,
Je montre aux cœurs moroses
Ce qu'ils voudraient avoir,

Je cours, matin et soir,
Après les belles choses,
Papillons blancs et roses,
Je suis le jeune espoir !

— Vieillard à la voix tendre,
Que chacun aime entendre
Et cherche à retenir,

J'entre au seuil, et, doux hôte,
Je rends ce que l'âge ôte,
Je suis le souvenir !
"""

TEST_EMOTION_VECTOR = [0, 10, 10]      # happiness, sadness, aversion

WORD_EMOTION_ASSOCIATIONS_PATH = Path("./word_emotion_associations.npy")

EMOTION_WORD_LIST_PATH = Path("./emotion_word_list.txt")


def main():
    """Main program."""

    # Load word-emotion association model.
    model = load_word_emotion_associations()

    # Load corresponding emotion word list.
    wordlist = load_emotion_word_list()

    # Get candidate word locations.
    candidate_slices = select_candidate_words(
        TEST_DATA,
        TEST_EMOTION_VECTOR,
        model,
        wordlist,
    )

    # Display text with brackets around candidate words...
    modified_text = TEST_DATA
    for candidate_slice in reversed(sorted(candidate_slices)):
        modified_text = (
            modified_text[:candidate_slice.start]
          + "["
          + modified_text[candidate_slice.start:candidate_slice.stop]
          + "]"
          + modified_text[candidate_slice.stop:]
        )
    print(modified_text)

def select_candidate_words(
    input_text,
    emotion_vector,
    word_emotion_associations,
    emotion_word_list,
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
        word_emotion_associations,
        np.array(emotion_vector),
    )

    # Get list of emotion words in increasing order of conservability...
    sorted_indices = np.argsort(conservability_scores)
    replaceable_words = list(emotion_word_list[sorted_indices])

    # Exclude when conservability > emotion vector sum / conservativeness...
    to_exclude = emotion_word_list[
        conservability_scores >= sum(emotion_vector) / conservativeness
    ]
    replaceable_words = [w for w in replaceable_words if w not in to_exclude]

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



def load_word_emotion_associations(path=WORD_EMOTION_ASSOCIATIONS_PATH):
    """Given the path to a word-emotion association model, opens and
    deserializes it as a numpy array."""
    try:
        with open(path, mode="rb") as input_file:
            return np.load(path)
    except IOError:
        print("Couldn't open file", path)
        exit()

def load_emotion_word_list(path=EMOTION_WORD_LIST_PATH):
    """Given the path to a list of emotion words (row headers of the
    word-emotion association model), opens it and stores them in an array."""
    try:
        with open(path, mode="r") as input_file:
            return np.array(input_file.read().split("\n"))
    except IOError:
        print("Couldn't open file", path)
        exit()


if __name__ == "__main__":
    main()