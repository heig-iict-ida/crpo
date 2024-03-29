# Computer Assisted Poem Creation (CRPO)

This system generates poems in English based on neural language models (GPT-2 and RoBERTa).  The interface allows users to select the form of the poem, the topics and emotions, and the rhyming patterns.

The system was designed at the **School of Engineering and Management** in Yverdon, Switzerland ([HEIG-VD](https://www.heig-vd.ch/), part of [HES-SO](https://www.hes-so.ch/)), with contributions from the [University of Lausanne](https://www.unil.ch) and [EPFL](https://www.epfl.ch) (see credits below).

## Installation instructions

Clone or download this repo in a folder named `crpo` in your *home folder*.  The path in `utils/config.py` can be changed (modify the line with: `cpao_root = os.path.join(home, 'crpo')`) if you store it elsewhere.

Run `conda env create -f crpo.yml` to create the environment with the necessary packages, and activate the environment with `conda activate crpo`.  You can also create a conda environment with `conda create --name crpo python=3.8`, activate it, and then install manually with `pip install`: torch==1.13.0 transformers==4.24.0 kivy==2.1.0 nltk==3.7, with their dependencies.

The language models will be dowloaded automatically from [Huggingface](https://huggingface.co/models) upon the first use, thanks to the [Transformers](https://huggingface.co/docs/transformers/index) library.  This may take several minutes.  There is one general model used for generation ([gpt2-poetry-model-crpo](https://huggingface.co/andreipb/gpt2-poetry-model-crpo)), five topic-specific ones used for editing ([roberta-poetry-art-crpo](https://huggingface.co/andreipb/roberta-poetry-art-crpo), [-life-](https://huggingface.co/andreipb/roberta-poetry-life-crpo), [-love-](https://huggingface.co/andreipb/roberta-poetry-love-crpo), [-nature-](https://huggingface.co/andreipb/roberta-poetry-nature-crpo), and [-religion-](https://huggingface.co/andreipb/roberta-poetry-religion-crpo)), and three emotion-specific ones also for editing ([-happiness-](https://huggingface.co/andreipb/roberta-poetry-happiness-crpo), [-sadness-](https://huggingface.co/andreipb/roberta-poetry-sadness-crpo), and [-anger-](https://huggingface.co/andreipb/roberta-poetry-anger-crpo)), for a total of 4.2 GB.

From the command line, run `python ./main.py`, which opens the GUI of the generator.

## Content of folders
  - `backend`: code to generate poems according to a selected form (number of stanzas and lines, length of lines) or to modify them according to a selected topic (among 5), emotion (among 3), or rhyming pattern
  - `frontend`: code to display the GUI using the Kivy framework (the application can be configured to run full screen, for instance for a touchscreen)
  - `logs`: each poem is written in a timestamped JSON file, with all intermediary stages
  - `rhyming`: a function and a dictionary to measure whether two verses rhyme or not (see Section 2 of the [GPoeT paper](https://aclanthology.org/2023.latechclfl-1.2/) and the notebook in that folder)
  - `utils`: auxiliary functions and linguistic data

## Credits

The system is described in the following articles:

   - Andrei Popescu-Belis, Àlex R. Atrio, Valentin Minder, Aris Xanthos, Gabriel Luthier, Simon Mattei, and Antonio Rodriguez. 2022. [Constrained Language Models for Interactive Poem Generation](https://aclanthology.org/2022.lrec-1.377). *Proceedings of the 13th Language Resources and Evaluation Conference (LREC)*, pages 3519–3529, Marseille, France. European Language Resources Association.

The models for the English version were replaced with Transformer-based ones by [Teo Ferrari](https://www.linkedin.com/in/teo-ferrari-0a4009176/) as part of his [Bachelor thesis at HEIG-VD](https://gaps.heig-vd.ch/public/diplome/rapports.php?id=6763), supervised by [Andrei Popescu-Belis](http://iict-space.heig-vd.ch/apu/).  

Rhyming for English was updated by [Àlex R. Atrio](https://github.com/AlexRAtrio).  

Rhyming patterns can also be learned by the GPoeT model, as shown in the following article:

   - Popescu-Belis A., Atrio A.R., Bernath B., Boisson E., Ferrari T., Theimer-Lienhard X., & Vernikos G. 2023. [GPoeT: a Language Model Trained for Rhyme Generation on Synthetic Data](https://aclanthology.org/2023.latechclfl-1.2/). *Proceedings of the 6th Joint SIGHUM Workshop on Computational Linguistics for Cultural Heritage, Social Sciences, Humanities and Literature (LaTeCH-CLfL)*, EACL 2023, Dubrovnik, Croatia.

CRPO was originally designed for the [Digital Lyric exhibition](https://lyricalvalley.org/digital-lyric-exposition/) held in Morges, Switzerland, in spring 2020.  The exhibition was curated by Professors [Antonio Rodriguez](https://www.unil.ch/fra/antoniorodriguez) (University of Lausanne) and [Sarah Kenderdine](https://people.epfl.ch/sarah.kenderdine) (EPFL).  The event showcased artworks and devices demonstrating novel relations between poetry and technology.

## Examples

Here is a stanza generated by the system, with only 6 characters edited by a human:

*To Whom the ancient Snares obey<br/>
And give the gifts they best can give<br/>
If needful, I no more will pray<br/>
In peace with myself I forgive.<br/>*

Here are unedited lines generated by the GPoeT model trained to generate the AABB rhyming pattern (this model is not included in the current version):

*The prince of men in arms he heard<br/>
So bold, so bold the warrior plundered<br/>
That she herself in sorrow cried<br/>
My God! who made the earth so bide.<br/>*

*She sees no other sun above<br/>
Nor in that cloudless sky doth dove<br/>
My God! who made the earth so fair<br/>
And on this cloudless night hath mair.<br/>*
