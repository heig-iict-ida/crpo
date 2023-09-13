from calendar import c
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from string import punctuation
from transformers import pipeline
import numpy as np
import re
from datetime import datetime
import random
import utils.config as conf
import os

from backend.correct_with_dictionary import postprocessing

def load_models (models, path):
    """
    Loads and builds the trained language models, their vocab and indices, given path and models' names.
    """
    built_models = []
    model_path = path + '/' + models[0] # using Huggingface name instead of the local: os.path.join(path, models[0])
	
    model = GPT2LMHeadModel.from_pretrained(model_path)
    tokenizer = GPT2Tokenizer.from_pretrained(model_path)
    pipe = pipeline('text-generation', model=model, tokenizer=tokenizer, device = conf.DEVICE, pad_token_id=tokenizer.eos_token_id)
	
    built_models.append(pipe)
    built_models.append(model)
    built_models.append(tokenizer) # references to all three will be needed

    return [built_models]


def random_form ():
    """
    Generates a random poem structure.
    """

    structure = []
    num_strophes = 1 #random.choice(range(2, 5)) #single stroph

    for s in range(num_strophes):

        strophe = []
        num_verses = random.choice(range(3, 6))

        for v in range(num_verses):

            verse_length = random.choice(range(8*5, 13*5)) #32 to 52 chars, approx 8 to 13 syllabs
            strophe += [verse_length]

        structure += [strophe]

    return structure


def flatten(L):
    """
    Flattens a list.
    """

    return [L] if not isinstance(L, list) else [x for X in L for x in flatten(X)]


def get_alignment_indices (vocabs): #DEPRECATED
    """
    Gets the correct indices relations to align the different vocabs and predictions.
    """

    alignments = []

    for idx in range(len(vocabs)):
        vocab = vocabs[idx]
        new_idx = []
        new_idx += [0]
        for key in vocabs[0]:
            new_idx += [vocab[key]]

        alignments += [new_idx]

    return alignments


def align_predictions (predictions, alignments): #DEPRECATED
    """
    Aligns prediction vectors based on get_alignment_indices' alignments.
    """

    new_predictions = np.zeros((predictions.shape))

    for i in range(len(predictions)):
        pred = predictions[i]
        alignment = np.asarray(alignments[i])

        new_pred = pred[alignment]
        new_predictions[i] = new_pred

    return new_predictions


def sample(preds, temperature, forbidden, interactive=False, top_n=3): #DEPRECATED
    """
    Samples predicted probabilities of the next character to allow
    for the network to show "creativity".

    forbidden: list of idxs for characters we don't want to choose.
    """

    preds = np.asarray(preds).astype('float64')

    if temperature is None or temperature == 0.0:
        return np.argmax(preds)

    preds = np.log(preds + 1e-07) / temperature # APB: replaced keras.epsilon() with 1e-7 to avoid installing Keras only for this
    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    probas = np.random.multinomial(1, preds, 1)

    index = np.argmax(probas)

    # If selected char is forbidden, gets next one

    good_ones = []
    if index in forbidden:
        sorted_inv = np.argsort(preds)
        good_one = False
        for el in list(reversed(sorted_inv)):
            if el not in forbidden:
                good_ones += [el]
        index = good_ones[0]

    return index


def predict (text_to_encode, #DEPRECATED
             models, vocabs, indices_chars,
             mixing_percentages,
             alignments,
             temperature=0.5,
             maxlen=40):
    """
    Predicts an index weighting the different models with given mixing percentages.
    """

    total_mixing_percentages = mixing_percentages.sum()
    random_choice = random.random() # random in the range [0, 1)

    model_index = 0
    current_interval_max = mixing_percentages[model_index] / total_mixing_percentages

def syllable_count (word) : # Found this algorythm on this website : https://eayd.in/?p=232. Counts the syllables of a word following some rules

    word = word.lower()
    exception_add = ['serious','crucial']
    exception_del = ['fortunately','unfortunately']

    co_one = ['cool','coach','coat','coal','count','coin','coarse','coup','coif','cook','coign','coiffe','coof','court']
    co_two = ['coapt','coed','coinci']

    pre_one = ['preach']

    syls = 0 #added syllable number
    disc = 0 #discarded syllable number

    #if letters < 3 : return 1
    if len(word) <= 3 :
        syls = 1
        return syls

    #if doesn't end with "ted" or "tes" or "ses" or "ied" or "ies", discard "es" and "ed" at the end.
    # if it has only 1 vowel or 1 set of consecutive vowels, discard. (like "speed", "fled" etc.)

    if word[-2:] == "es" or word[-2:] == "ed" :
        doubleAndtripple_1 = len(re.findall(r'[eaoui][eaoui]',word))
        if doubleAndtripple_1 > 1 or len(re.findall(r'[eaoui][^eaoui]',word)) > 1 :
            if word[-3:] == "ted" or word[-3:] == "tes" or word[-3:] == "ses" or word[-3:] == "ied" or word[-3:] == "ies" :
                pass
            else :
                disc+=1

    #discard trailing "e", except where ending is "le"  

    le_except = ['whole','mobile','pole','male','female','hale','pale','tale','sale','aisle','whale','while']

    if word[-1:] == "e" :
        if word[-2:] == "le" and word not in le_except :
            pass

        else :
            disc+=1

    #check if consecutive vowels exists, triplets or pairs, count them as one.

    doubleAndtripple = len(re.findall(r'[eaoui][eaoui]',word))
    tripple = len(re.findall(r'[eaoui][eaoui][eaoui]',word))
    disc+=doubleAndtripple + tripple

    #count remaining vowels in word.
    numVowels = len(re.findall(r'[eaoui]',word))

    #add one if starts with "mc"
    if word[:2] == "mc" :
        syls+=1

    #add one if ends with "y" but is not surrouned by vowel
    if word[-1:] == "y" and word[-2] not in "aeoui" :
        syls +=1

    #add one if "y" is surrounded by non-vowels and is not in the last word.

    for i,j in enumerate(word) :
        if j == "y" :
            if (i != 0) and (i != len(word)-1) :
                if word[i-1] not in "aeoui" and word[i+1] not in "aeoui" :
                    syls+=1

    #if starts with "tri-" or "bi-" and is followed by a vowel, add one.

    if word[:3] == "tri" and word[3] in "aeoui" :
        syls+=1

    if word[:2] == "bi" and word[2] in "aeoui" :
        syls+=1

    #10) if ends with "-ian", should be counted as two syllables, except for "-tian" and "-cian"

    if word[-3:] == "ian" : 
    #and (word[-4:] != "cian" or word[-4:] != "tian") :
        if word[-4:] == "cian" or word[-4:] == "tian" :
            pass
        else :
            syls+=1

    #if starts with "co-" and is followed by a vowel, check if exists in the double syllable dictionary, if not, check if in single dictionary and act accordingly.

    if word[:2] == "co" and word[2] in 'eaoui' :

        if word[:4] in co_two or word[:5] in co_two or word[:6] in co_two :
            syls+=1
        elif word[:4] in co_one or word[:5] in co_one or word[:6] in co_one :
            pass
        else :
            syls+=1

    #if starts with "pre-" and is followed by a vowel, check if exists in the double syllable dictionary, if not, check if in single dictionary and act accordingly.

    if word[:3] == "pre" and word[3] in 'eaoui' :
        if word[:6] in pre_one :
            pass
        else :
            syls+=1

    #check for "-n't" and cross match with dictionary to add syllable.

    negative = ["doesn't", "isn't", "shouldn't", "couldn't","wouldn't"]

    if word[-3:] == "n't" :
        if word in negative :
            syls+=1
        else :
            pass   

    #Handling the exceptional words.

    if word in exception_del :
        disc+=1

    if word in exception_add :
        syls+=1     

    # calculate the output
    return numVowels - disc + syls

def syllable_count_sentence(sent): # Counts the syllables of a sentence
    count = 0
    sent = sent.replace("\n", "")
    sent_tokens = sent.split(" ")
    for word in sent_tokens:
            word = word.strip(punctuation)
            if word != "":
                count += syllable_count(word)
    return count


#print_into_file may be used to DEBUG ONLY (save to DISK first stage generation results)
#d allows printing of detailed debug info in TERMINAL
def generate(form,
            models,
            outfile_directory,
            temperature= 1.0,
            print_into_file=False, 
            d=False,
            user_input=""):
   
    text = "<start>" + user_input
    number_of_strophes = len(form)
    punctuation = ['.', ',', ':', ';', '!', '?', ' ']
    verse_nb = 0
    first_verse = True
    input_length = syllable_count(user_input)

    if(d):
        special_gen_nb = 0

    # Start generation of poem
    for s in range(number_of_strophes): #Strophes

        number_of_verses = form[s]
    
        for v in range(len(number_of_verses)): #Verses
            verse_length = number_of_verses[v]
            verse_nb_syllables = round(verse_length / 5)
            verse_nb_tokens = round(verse_nb_syllables + ((verse_nb_syllables) / 2)) #Number of tokens in verse + one special token every two syllables
            verse = ""
            nb_generations = 0
            special_gen = False
            forbidden_tokens_special_gen = [[29],[9688],[27],[198],[220],[532],[60],[62],[26],[4210],[32],[960],[7],[27920], [685], [2361], [1391], [1782], [4808], [1279]] # tokens for \n<start> = 198, 27, 9688, 29,

            if not first_verse:
                input_length = 0

            max_lenght_verse = verse_nb_tokens + 2 + 4 - input_length
            min_lenght_verse = verse_nb_tokens - 2 + 4 + round(len(text) / 4)- input_length

            # Generate verse from the existing text
            generated = ""
            # Check if at least a full verse has been generated and if the verse has the correct number of syllables
            while generated.count('<start>') < verse_nb + 2 or syllable_count_sentence(generated.split("<start>")[verse_nb + 1]) != verse_nb_syllables:
                
                if nb_generations < 10: # Generate another verse up to 10 times
                    generated = models[0](text, temperature = temperature, max_new_tokens = max_lenght_verse, min_length = min_lenght_verse)[0]['generated_text']
                    nb_generations += 1
                
                else: # If the verse has not been generated after 10 tries, generate a new verse token by token
                    if(d):
                        print("special gen")
                        special_gen_nb += 1

                    special_gen = True 
                    s = input_length
                    if(s < verse_nb_syllables) : # This is necessary because with the user input the verse could already have the correct number of syllables
                        #This first generation take the original text as input
                        generated = models[0](text, temperature = temperature, max_new_tokens = 1, bad_words_ids = forbidden_tokens_special_gen )[0]['generated_text']
                    else:
                        generated = text
                    while s < verse_nb_syllables:
                        #the remaining generations take the original text plus the new tokens as an input
                        generated = models[0](generated, temperature = temperature, max_new_tokens = 1, bad_words_ids = forbidden_tokens_special_gen)[0]['generated_text']
                        s = syllable_count_sentence(generated.split("<start>")[verse_nb + 1])
                    generated += "\n<start>"
                    
                    
                        
            verse = generated.split("<start>")[verse_nb + 1] #With this we separate the new verse form the rest of the text
            
            if special_gen:
                verse = verse.replace("-","")
            if first_verse:
                verse = verse.replace(user_input,"")
                first_verse = False

            if (d):
                print("Nb gen :" , nb_generations)
                print(verse)
                

            if v == (len(number_of_verses) - 1):
                text = text + verse
            else:
                 text = text + verse  + "<start>"
            verse_nb += 1

        text = text + "\n<start>"
    
    text = text.replace("<start>", "")
    if(d):
        print("Temperature:" , temperature)
        print("Generated poem : \n" , text)
        print("Nb of special gen:" , special_gen_nb)
        print('\n')


    # Postprocessing.
    text = postprocessing(text, punctuation)


    # Print poem into file
    if print_into_file:

        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_GEN") #Windows compatible
        with open(outfile_directory + now + '.txt', 'w') as f:
            f.write(text)

    if d:
        print("Final poem: \n" , text)
        print('\n')

    return text

def generate_poetry (models,
                     form='quatrain',
                     outfile_directory=conf.OUTPUT_DIRECTORY_FILE,
                     debug=False,
                     temperature=1.0,
                     user_input=""):
    """
    Calls textgenrnn_generate() with correct form and model mixing %s parameters.

    models: list of list of built models, their vocabs, and their indices_chars.
    """

    # Character approximation to syllabic count.
    s = 4
    sonnet_l = 10 #should be 12, but let's speed up generation

	#haiku is 5-7-5 but we prefer longer texts (better quality)
    if form == 'haiku':
        structure = [[7*s, 9*s, 7*s], [8*s, 11*s, 8*s]]
    elif form == 'sonnet':
        structure = [[sonnet_l*s]*4, [sonnet_l*s]*4, [sonnet_l*s]*3, [sonnet_l*s]*3]
    elif form == 'limerick': #DEPRECATED
        structure = [[9*s]*5]
    elif form == 'quatrain':
        structure = [[10*s]*4]
    elif form == 'freeform':
        structure = random_form()

    return generate(structure,
                               models[0],
                               outfile_directory,
                               d=debug,
                               temperature=temperature,
                               user_input=user_input)
