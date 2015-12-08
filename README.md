# NoUGaT
system for normalization of user-generated content. This is the underlying code. The static files containing all models cannot be made available here. Therefore, the code cannot be executed. However, if one includes their own models (language models, translation models), this code can be used as the base architecture.

Tutorial
========

Contributors: Sarah Schulz, Bart Desmet, Orphee De Clercq, Arda Tezcan, Guy De Pauw

Version 1.0

Date 15th November 2014

contact: Sarschu@gmail.com

The Normalizer converts User Generated Contents into a normalized version that can be further processed with NLP tools. 
It has been trained on three different genres of UGC namely Twitter data, SMS and Netlog. It works for Dutch as well as for English. 


System architecture
===================

The normalization pipeline consists of different more or less independent modules.

 * the preprocessing module
 * the suggestion-generation modules
 * the decision module

Preprocessing
-------------

The first step that is performed is the preprocessing of the input files. 

The program works on the sentence level. That means that the input is split into sentences first. 

The following replacements of  characters talk place:
* smilies
* tags
* hyperlink 



Suggestion generation
---------------------

There are 8 different modules that generate possible normalization option for each word in a sentence. Some modules 
generate exactly one output for each word, others do not deliver an option for every word but can deliver more than one
possible option per word. 

The modules cover different levels of mistakes that can appear in UGC such as spelling errors or phonetic expressions.

Abbreviation
************

Language used in UGC often shares certain abbreviations and uniform ways of reference like hash tags in Twitter posts. Therefore, lookup approaches can cover a reasonable number of issues.

The abbreviation module relies on a dictionary of about 350 frequent abbreviations appearing in social media texts like *lol* (laughing out loud) and *aub* for (alstublieft) (thank you).

Compound
********

It is often the case (and certainly more often for Dutch than for English) that compounds that should actually be written in one 
word are written in two words. 

To account for this compounding mistakes the compound module tests for all two words that are written next to each other if a 
spell checker (hunspell) recognizes them as correctly spelled word when they are written as one word. If that is the case, the 
compound version is returned as a possible option for the two words. 

The output of this module is a phrase (the two original words) along with a one word option. This is possible since we later one work
with phrase-based machine translation. If there is no compound correction in the input sentence the output is an empty list.


Empty
*****

A module which is not included by default. It returns the empty string for each token in order to give the possibility to delete tokens.

Named entity module
*******************

This is a module that differs from the other modules. It does not give options but returns information that can be used later as a feature. By default, this module is not included.


Named entities (NEs) should not be normalized and it is therefore important to recognize them as such in order to avoid overcorrection. Since NEs in UGC have different characteristics than in standard texts (NEs frequently lack capitalization or are introduced with specific characters as @ or #), we developed a dedicated named entity recognition (NER) tool. 

The NER tool is hybrid in the sense that it uses gazetteer lookup and classification. The gazetteers  contain a variety of named entities. Moreover, it includes a simple pattern-matching rule to find words with a capitalized first letter which does not appear at the beginning of a sentence. 

 Other than abbreviations, NEs are a highly productive group, so a lookup approach does not suffice.
For that reason, we added a conditional random field classifier trained on the training set of our corpus. It reaches a high performance (F-score of 0.9) and has been trained with features tailored to named entities in UGC.



Original
********

The original module returns the original word as an option for the word. This is important since some of the words are not 
erroneous and could get lost when no other module returns the original option. 

The output of this module is the original word along with exactly one option (which is the same word as the input word).


G2P2G
*****

UGC often contains mistakes that are due to the "spell like you pronounce it" style. Often words are a graphematic representation of 
how a word is pronounced. To be able to translate those words to the correct spelling we first have to find a phonetic representation
that is close to the graphematic representation and then use a lookup dictionary to find the correct orthographic representation of the
similar phonetic string.

The module performs the following steps:

1. The graphematic original word is with the help of a memory-based translation system translated into its phonetic representation
2. certain replacement strategies borrowed from spell checking approaches are used in order to generate similar phonetic strings (namely splits, deletes, transposes, replaces, inserts and of course also the phonetic representation of the original string)
3. all the phonetic alternatives are looked up in a dictionary containing phonetic strings along with its grapheme translations. 
4. all grapheme translations that can be found for the phonetic alternatives are returned as possible options of the original word

(implemented by Guy De Pauw)

SMT
***
Following preliminary experiments described in DeClercq (2013), the SMT models have been trained on token and character level using Moses. The language model used has been built from a combination of four corpora using KenLM.
 
There are four different modules that work with statistical machine translation.

* unigram module
* bigram module
* token module
* cascaded module

All those modules work with Moses models. Since the program works on the sentence level we included Moses sever mode in order 
to avoid loading the model files of Moses for each sentence.
	


Spell checker
*************

The spell checker module uses hunspell (and its python wrapper pyhunspell). Each word in the original sentence is spell checked.
In case hunspell classifies a word as wrongly-spelled, the correction suggestions given by hunspell are returned as alternatives.
The output of the spell checker module is a list of spell checker suggestions for each wrongly-spelled word.

Word split
**********
Theword split module is the opposite of the compound module and splits words that have been erroneously written together. In UGC words are often concatenated in order to save space. 

The word split module is based on the compound-splitter module of Moses  and has been trained on the Corpus Gesproken Netherlands (CGN). 
It often appears that words that are actually two words are written together. 





Decision module
---------------

Since we have no a-priori knowledge about the nature of a normalization problem, each sentence is sent to all modules of the suggestion  layer. In order to prevent an avalanche of suggestions, for each module of the suggestion layer, we restricted the number of suggestions per token to one.

It is the task of the decision module to choose the most probable combination of suggestions  to build a well-formed sentence, which poses a combinatorial problem. The decision module itself makes use of the Moses decoder, a powerful, highly efficient tool able to solve the combinatorial problem with the aid of a language model of standard languagein order to include probability information.

We include the normalization suggestions in form of a phrase table into the decoding process. The decoder weights have been manually tuned using development data. However, the weights might not be ideal for decoding the dynamically compiled phrase tables containing the normalization suggestions. We include weights for the different components of the decoding process like the language model. the translation model, word penalty and distortion. Distortion is made expensive since we want to avoid reordering. Moreover, the decoder uses features containing information about which module returned which suggestion. The feature weights are first set to 0.2 and later tuned on the development data

 
Example of usage
^^^^^^^^^^^^^^^^

The system requires 3 arguments and is run like this: 

run_norm.py <lang> <inputfile> <outputfile>

The two last arguments serve evaluation and can be ignored
Run it from the norm directory. The log files will be located in the log directory after the run. 
In case you have questions, ask me.


* <lang>:       can take value "nl" and "en"
* <inputfile>:  inputfile is a text file containing one messages per line. Those will be handeled as one to not lose context
* <outputfile>: the file to which the normalized messages will be written.

The system can also just be run in preprocessing mode:

run_prepro.py <lang> <inputfile> <outputfile>

System Requirements
===================

The system has been tested on a 64-bit Ubuntu machine. 
The following tools and packages have to be installed and the paths have to be adjusted in order to run the normalizer.

* Moses (compiled with server mode and SRILM setting)
* xmlrpc-c 1.25.23 (Moses has to be compiled with the --with-xmlrpc-c in order to include it)
* hunspell
* pyhunspell 0.1
* pytest
* scikit-learn
* nltk

