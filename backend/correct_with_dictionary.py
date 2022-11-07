import difflib
import numpy as np
from nltk import word_tokenize
import re
import random


'''
Code by Àlex
'''

def postprocessing (text, punctuation):
    """
    Does a bit of aesthetic postprocessing on the text. Each part is separate and ad hoc quick patch atm, so
    things could be improved, added, or deleted - there's lots of redundancies (should be cleaned up).
    """

    # Don't start with punctuation or ' '.
    while text[0] in punctuation:
        text = text[1:]

    # Punctuation immediately follows alphabetical characters (no ' ' in between).
    idxs_punctuation = []
    for i in range(len(text) - 1):
        if text[i] in punctuation[:-1]:
            if text[i-1] == ' ':
                idxs_punctuation += [i - 1]
    text = [text[i] for i in range(len(text)) if i not in idxs_punctuation]

    # Don't have two punctuation signs next to each other.
    idxs_punctuation = []
    for i in range(len(text) - 1):
        if text[i] in punctuation:
            if text[i+1] in punctuation:
                idxs_punctuation += [i + 1]
    text = [text[i] for i in range(len(text)) if i not in idxs_punctuation]

    # Add ' ' after punctuation.
    new_text = []
    for i in range(len(text) - 1):
        if text[i] not in punctuation:
            new_text += [text[i]]
        elif text[i] == ' ':
            new_text += [text[i]]
        elif text[i] in punctuation[:-1]:
            new_text += [text[i], ' ']
    text = new_text

    # No ' ' after ' ', '↵' into '\n', no verse start with ' ', write '...' correctly.
    text_joined = ''.join(text)
    text_joined = re.sub(r" +", ' ', text_joined)
    text_joined = re.sub(r"↵", '\n', text_joined)
    text_joined = re.sub(r'\n ','\n', text_joined)
    text_joined = re.sub('\.\.+', '...', text_joined)

    # Correct uppercase and lowercase #The new gpt-2 model doesn't generally makes casing mistakes 
    #text = [i for i in text_joined]
    #text[0] = text[0].upper()
    #for i in range(len(text)):
        #if text[i-1] in ['.', '!', '?']:
            #if text[i] == ' ' and i+1 < len(text):
                #text[i+1] = text[i+1].upper()
            #else:
                #text[i] = text[i].upper()
        #elif text[i-1] in [',', ':', ';']:
            #text[i] = text[i].lower()

    # Delete some t percent of ending soft punctuation to make it look a bit more natural.
    t = 0.25
    idxs_to_delete = []
    for i in range(len(text)):
        if text[i] == '\n':
            if text[i-1] != '\n':
                end = text[i-2]
                if end in [',', ':', ';']:
                    if random.random() < t:
                        idxs_to_delete += [i-2]
    text = [text[i] for i in range(len(text)) if i not in idxs_to_delete]

    # Add ' ' before certain punctuation signs.  
    #new_text = []
    #for i in range(len(text) - 1):
        #if text[i+1] not in [':', ';', '!', '?']:
            #new_text += [text[i]]
        #else:
            #new_text +=[text[i], ' ']
    #new_text += text[-1]
    #text = new_text

    # No ' ' before '\n' and end strophes with punctuation
    re_sub = re.sub(r' \n', '\n', ''.join(text))
    text = [i for i in re_sub]
    new_text = []
    for i in range(len(text) - 2):
        if text[i+1] == '\n' and text[i+2] == '\n':
            if text[i] in ['!', '?', '.']: #While I don't like the idea of random hard punctuation, I think it's better than nothing.
                new_text += [text[i]]
            elif text[i] in [';', ',', ':']: 
                new_text += [text[i]] #But not better than soft punctuation.
            else:
                new_text += [text[i], random.choice(['!', '?', '.'])]
        else:
            new_text += [text[i]]
    new_text += text[-2:]
    text = new_text

    # End with hard punctuation.
    if  text[-2] in punctuation and text[-2] not in ['!', '?', '.']:
        text[-2] = random.choice(['!', '?', '.'])
        text[-1] = ""
    elif text[-2] in ['!', '?', '.']:
        text[-1] = ""
    else:
        text[-1] = random.choice(['!', '?', '.'])

    return ''.join(text)



def check_dictionary_poem (text, dictionary): # not used in english version as gpt-2 generally doesn't makes these mistakes

    punctuation = ['.', ',', ',', ':', ';', '!', '?', ' ']

    all_poem = []
    all_replacements = []

    strophes = text.split('\n\n')
    for s in strophes:
        correct_strophe = []
        verses = s.split('\n')

        for v in verses:

            new_verse = []
            tok_verse = word_tokenize(v, language='french')
            final_verse = []
            replacements = {}
            apostrophes_idxs = []

            for t in range(len(tok_verse)):
                if "'" in tok_verse[t]:
                    splits = tok_verse[t].split("'")
                    for e in range(len(splits)):
                        final_verse += [splits[e]]
                    apo_corr_idx = t + len(apostrophes_idxs)
                    apostrophes_idxs += [apo_corr_idx]

                else:
                    final_verse += [tok_verse[t]]

            for word in final_verse:

                word_lower = word.lower()
                word_in_array = np.where(dictionary[:,0] == word_lower)

                #
                if (np.asarray(word_in_array)).shape[1] == 0:
                    possibles = difflib.get_close_matches(word_lower, dictionary[:,0])

                    if len(possibles) != 0:
                        word_in_array = np.where(dictionary[:,0] == possibles[0].lower())
                        new_word = dictionary[word_in_array][0][0]
                    else:
                        new_word = word_lower

                    if word and word[0] and word[0] != word[0].lower():
                        new_word = new_word[0].upper() + new_word[1:]

                    replacements[word] = new_word

            final_replacements = {}

            for i in replacements:
                if i not in punctuation:
                    if replacements[i] != i:
                        final_replacements[i] = replacements[i]
            all_replacements += [final_replacements]

            correct_verse = [final_replacements.get(item,item)  for item in final_verse]

            apos_verse = []
            for i in range(len(correct_verse)):
                if i in apostrophes_idxs:
                    apos_verse += [correct_verse[i] + "'"]
                else:
                    apos_verse += [correct_verse[i]]

            raw_verse = ' '.join(apos_verse)
            raw_verse = re.sub("' ", "'", raw_verse)
#             raw_verse + '\n'


            correct_strophe += [raw_verse]

        final_strophe = ['\n'.join(correct_strophe)]

        all_poem += [final_strophe]

    new_poem = ''
    for ns in all_poem:
        new_poem += ns[0]
        new_poem += '\n\n'


    raw_final_poem = postprocessing(new_poem, punctuation)

    print('REPLACED WORDS IN VERSES:', all_replacements, '\n')

    return (raw_final_poem, all_replacements)