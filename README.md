# Computer Assisted Poem Creation (CRPO)

This system generates poems in English based on neural language models (GPT-2 and RoBERTa).  The interface allows users to select the form of the poem, the topics and emotions, and the rhyming patterns.

## Installation instructions

Create a conda environment: `conda create --name crpo python=3.8` and then activate it: `conda activate crpo`

Install *torch*, *pytorch_transformers*, *transformers*, *kivy*, and *nltk*, either individually with `pip install` or by running: `conda env create -f crpo.yml`

Clone or download this repo in a folder named `crpo` at the root of your home folder: the paths in `utils/config.py` assume this location, but they can also be adjusted for a different location.

Download language models from [Switch Drive](https://drive.switch.ch/index.php/s/ICq06PM0od7cjrD), and unpack them into the `models` folder.  You should see subfolders named 'gpt2-poetry-model-crpo', 'anger', 'art', 'happiness', 'life', 'love', 'nature', 'religion', and 'sadness' (4.2 GB).

From a command line interface, run `python main.py` -- this should open a GUI for the system with explicit instructions.

## Content of system folders
  - `backend`: code for generating poems according to a selected form (number of stanzas and lines, length of lines) or modifying them according to a selected topic, emotion, or rhyming pattern
  - `frontend`: code for displaying the screens using the Kivy framework (currently, the application opens in a window, but it can also be configured to run full screen, e.g. covering an entire touchscreen)
  - `logs`: each generated poem is written in a timestampted JSON file, with all intermediary stages, for further analysis
  - `models`: folder to store the GPT-2 and RoBERTa models (downloaded from https://drive.switch.ch/index.php/s/ICq06PM0od7cjrD and unzipped there) 
  - `utils`: auxiliary functions and data

## Credits

The system is described in the following article:

Andrei Popescu-Belis, Àlex R. Atrio, Valentin Minder, Aris Xanthos, Gabriel Luthier, Simon Mattei, and Antonio Rodriguez. 2022. [Constrained Language Models for Interactive Poem Generation](https://aclanthology.org/2022.lrec-1.377). *Proceedings of the 13th Language Resources and Evaluation Conference (LREC)*, pages 3519–3529, Marseille, France. European Language Resources Association.

The models for the English version were replaced with Transformer-based ones by [Teo Ferrari](https://www.linkedin.com/in/teo-ferrari-0a4009176/) as part of his Bachelor thesis at HEIG-VD, supervised by [Andrei Popescu-Belis](http://iict-space.heig-vd.ch/apu/).

CRPO was originally designed for the [Digital Lyric exhibition](https://lyricalvalley.org/digital-lyric-exposition/) held in Morges, Switzerland, in spring 2020.  The exhibition was curated by [Antonio Rodriguez](https://www.unil.ch/fra/antoniorodriguez) (University of Lausanne) and [Sarah Kenderdine](https://people.epfl.ch/sarah.kenderdine) (EPFL), and showcased art works and devices demonstrating novel relations between poetry and technology.
