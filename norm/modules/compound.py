#!/usr/bin/env python
# encoding: utf-8

import hunspell
import logging
compound_log = logging.getLogger("norm.module.compound")

class Compound(object):
    '''
    This class contains functions with which subsequent words can be checked for "compoundness".
    If the spellchecker (hunspell) doesn't complain about the combination of subsequent words,
    it is returned as an option.
    '''


    def __init__(self,normalizer):
	"""
	**parameters**, **types**::
    		:param normalizer: an object of the class Normalizer
    		:type word: Normalizer object

	A hunspell object is initialized.
	"""
        self.normalizer = normalizer
        if self.normalizer.language =="en":
            self.hobj = hunspell.HunSpell('/usr/share/myspell/dicts/en_US.dic', '/usr/share/myspell/dicts/en_US.aff')
        elif self.normalizer.language =="nl":
            self.hobj = hunspell.HunSpell('/usr/share/myspell/dicts/new_nl_dict.dic', '/usr/share/myspell/dicts/nl.aff')
        super(Compound,self).__init__()
        
    def check_hunspell(self,word):
	'''
 	return hunspell result

	**parameters**, **types**,**return**,**return types**::
		:param word: a word
		:type word: unicode string 
		:return: True or False dependent on whether a word is in hunspell dict or not
		:rtype: boolean
	
   	 '''
        return self.hobj.spell(word.encode("utf8"))
        
    #here i cant just do it for words that are wrongly spelled. Eg aan komen -> aankomen. Both correct
    def generate_alternatives(self,sentence,corr_list):
	'''
   	Generate suggestion

	**parameters**, **types**,**return**,**return types**::
		:param sentence: flooding corrected original message
		:type sentence: unicode string 
		:param corr_list: list containing all indices of the tokens that have to be normalized (hard filtering just some, otherwise all)
		:type corr_list: list of integers
		:return: original tokens aligned with the suggestion of the form [[ori,[sug]],[ori2,[sug2]]]
		:rtype: list of lists

	Compounds out of two subsequent tokens are built. Hunspell checks if the word is a correct word. 
	
   	 '''
        compound_log.info("start compound checker")
        original = sentence.split()
        words = sentence.split()
        results = []
        com =False
        for i in range(0,len(words)):
            if i != len(words)-1 and com ==False:
                #ignore the replacement characters and concatenate two subsequent tokens
                if words[i] not in [u"•",u"±",u"∞",u"ਊ"] and words[i+1][0] not in [u"•",u"±",u"∞",u"ਊ","?",".","!",'""']:
                    comp = unicode(words[i])+unicode(words[i+1])
                    #check whether the new "compound" is a existing word
                    regWord = self.check_hunspell(comp)
                    if regWord and i in corr_list:
                    #append all made up compound as an option. To use hunspell include the two lines above
                        results.append([unicode(original[i])+" "+unicode(original[i+1]),[comp.strip()]])
                        com = True
                    else:
                        results.append([unicode(original[i]),[unicode(original[i])]])
                else:
                        results.append([unicode(original[i]),[unicode(original[i])]])
            elif com ==False:
                results.append([unicode(original[i]),[unicode(original[i])]])
            elif com == True:
                com =False
                results.append(["",[""]])
        compound_log.debug(results)
        compound_log.info("compound checker finished")
        return results
