#!/usr/bin/env python
# encoding: utf-8

import hunspell
import logging
spellcheck_log = logging.getLogger("norm.module.spellcheck")
class Hunspell(object):
    '''
    This class contains functions that check a word with the hunspell spell checker.
    In case it is recognized as incorrectly spelled, alternative spelling options are suggested
    '''

    def __init__(self,normalizer):
	"""
	**parameters**, **types**::
    		:param normalizer: an object of the class Normalizer
    		:type word: Normalizer object

	A hunspell object is initialized.
	"""
        self.normalizer = normalizer
        super(Hunspell,self).__init__()
        if self.normalizer.language == "en":
            self.hobj = hunspell.HunSpell('/usr/share/myspell/dicts/en_US.dic', '/usr/share/myspell/dicts/en_US.aff')
        elif self.normalizer.language == "nl":
            self.hobj = hunspell.HunSpell('/usr/share/myspell/dicts/nl.dic', '/usr/share/myspell/dicts/nl.aff')
    #check and suggest alternatives if word is wrongly spelled


    def find_suggestions(self,word):
        '''	
	use the hunspell spell checker for correct suggestions. take the first suggestion (levenshtein distance smallest).	
	**parameters**, **types**,**return**,**return types**::
		:param word: a token
		:type sentence: unicode string 
		:return: hunspell corrected suggestion
		:rtype: unicode string
	'''
        if self.hobj.spell(word.encode("utf-8")) == False:                   
            suggestion = self.hobj.suggest(word.encode("utf-8"))
            if suggestion !=[]:
                suggestion = suggestion[0]
        else:
            suggestion=""
        return suggestion

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
	
   	 '''
        spellcheck_log.info("start spell checker")
        original = sentence.split()
        words = sentence.split()
        results =[]
        for i in range(0,len(words)):
            #ignore the replacement characters
            options=""
            if words[i] not in [u"•",u"±",u"∞",u"™"] and words[i].isalpha():
                options = self.find_suggestions(words[i])
    
            if options != "" and options !=[]  and i in corr_list:
                results.append([original[i],[unicode(options,"utf-8").strip()]])
            else:
                results.append([original[i],[original[i]]])
                
         
        spellcheck_log.debug(results)
        spellcheck_log.info("finished spell checker")
        return results
            
