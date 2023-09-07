# Rhyme counter

**Àlex R. Atrio and Andrei Popescu-Belis, HEIG-VD/HES-SO and EPFL, 2023**

This folder provides a notebook called `rhyme-counter.ipynb` which defines functions that verify if two verses rhyme.  They are validated in the notebook on three poems.

This rhyming measure is presented in Section 2 of our paper "[GPoeT: a Language Model Trained for Rhyme Generation on Synthetic Data](https://aclanthology.org/2023.latechclfl-1.2/)" 
by Popescu-Belis A., Atrio A.R. et al., presented at the [LaTeCH-CLfL 2023 workshop](https://aclanthology.org/volumes/2023.latechclfl-1/).  The paper also presents the validation
of the measure on the [Chicago Rhyming Poetry Corpus](https://github.com/sravanareddy/rhymedata)

The main function is `test_rhyme()`, which relies on a dictionary of rhymes provided within `rhyming_dictionaries.pickle` (4.3 MB).
This file was built from a phonetic dictionary of English provided by [CMU Sphinx](http://svn.code.sf.net/p/cmusphinx/code/trunk/cmudict/sphinxdict/) 
using the code provided here in the notebook `create_rhyming_dictionary_from_sphinx.ipynb`.
