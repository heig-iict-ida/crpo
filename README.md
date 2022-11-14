# Computer Assisted Poem Creation (CRPO)

This system generates poems in English based on neural language models (GPT-2 and RoBERTa).  The interface allows users to select the form of the poem, the topics and emotions, and the rhyming patterns.

## Installation instructions

Clone or download this repo in a folder named `crpo` at the root of your home folder.  The paths in `utils/config.py` assume the files are at this location, but they can also be changed if the location is different: just change 'crpo' in `cpao_root = os.path.join(home, 'crpo')` to your path.

Either i) create a conda environment: `conda create --name crpo python=3.8`, activate it: `conda activate crpo`, and install *torch*, *transformers*, *kivy*, and *nltk*, individually with `pip install`, 
or ii) simply run `conda env create -f crpo.yml` to create the environment with the necessary packages and then `conda activate crpo`.

Download fine-tuned language models from [Switch Drive](https://drive.switch.ch/index.php/s/ICq06PM0od7cjrD), and unpack them into the `models` folder.  You should see 1 + 5 + 3 subfolders named 'gpt2-poetry-model-crpo' / 'art', 'life', 'love', 'nature', 'religion' / 'anger', 'happiness', 'sadness' (4.2 GB).

From the command line, run `python main.py`, which opens the CRPO GUI, which should then be self-explanatory.

## Content of folders
  - `backend`: code to generate poems according to a selected form (number of stanzas and lines, length of lines) or to modify them according to a selected topic (among 5), emotion (among 3), or rhyming pattern
  - `frontend`: code to display the GUI using the Kivy framework (note: the application can be configured to run full screen, e.g. on a touchscreen)
  - `logs`: each poem is written in a timestampted JSON file, with all intermediary stages
  - `models`: fine-tuned GPT-2 and RoBERTa models (downloaded from [Switch Drive](https://drive.switch.ch/index.php/s/ICq06PM0od7cjrD)) 
  - `utils`: auxiliary functions and linguistic data

## Credits

The system is described in the following article:

Andrei Popescu-Belis, Àlex R. Atrio, Valentin Minder, Aris Xanthos, Gabriel Luthier, Simon Mattei, and Antonio Rodriguez. 2022. [Constrained Language Models for Interactive Poem Generation](https://aclanthology.org/2022.lrec-1.377). *Proceedings of the 13th Language Resources and Evaluation Conference (LREC)*, pages 3519–3529, Marseille, France. European Language Resources Association.

The models for the English version were replaced with Transformer-based ones by [Teo Ferrari](https://www.linkedin.com/in/teo-ferrari-0a4009176/) as part of his Bachelor thesis at HEIG-VD, supervised by [Andrei Popescu-Belis](http://iict-space.heig-vd.ch/apu/).

CRPO was originally designed for the [Digital Lyric exhibition](https://lyricalvalley.org/digital-lyric-exposition/) held in Morges, Switzerland, in spring 2020.  The exhibition was curated by [Antonio Rodriguez](https://www.unil.ch/fra/antoniorodriguez) (University of Lausanne) and [Sarah Kenderdine](https://people.epfl.ch/sarah.kenderdine) (EPFL), and showcased art works and devices demonstrating novel relations between poetry and technology.
