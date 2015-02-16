import json
import util
import hunspell
import logging
abb_log = logging.getLogger("norm.module.named_entity")


class Abbreviation(object):
    '''
    This module resolves the most frequent abbreviations
    in social media content
    '''


    def __init__(self,normalizer):
	"""
	**parameters**, **types**::
    		:param normalizer: an object of the class Normalizer
    		:type normalizer: Normalizer object

	A hunspell object is initialized.
	"""
        self.normalizer = normalizer
        super(Abbreviation, self).__init__()
        if self.normalizer.language =="nl":
            json_data = open(util.STATIC_DIR + "/abbreviation/dutch_ab.dict")
            self.hobj = hunspell.HunSpell('/usr/share/myspell/dicts/new_nl_dict.dic', '/usr/share/myspell/dicts/nl.aff')
        elif self.normalizer.language =="en":
            json_data = open(util.STATIC_DIR + "/abbreviation/english_ab.dict")
            self.hobj = hunspell.HunSpell('/usr/share/myspell/dicts/en_US.dic', '/usr/share/myspell/dicts/en_US.aff')

        self.abbr = json.load(json_data)
       
        


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
	
	Looks up a token in an abbreviation lexicon and returns the long version in case the token is found.
   	 '''
        abb_log.info("start abbreviation module")

        result =[]
        words = sentence.split()
        
        for word_ind,word in enumerate(words):  
            if not self.check_hunspell(word) and word.lower() in self.abbr and word_ind in corr_list:
                result.append([unicode(word),[unicode(self.abbr[word.lower()])]])
            else:
                result.append([unicode(word),[unicode(word)]])
        abb_log.debug(result)
        abb_log.info("finished abbreviation module")

        return result
            
                
        
    def check_hunspell(self,word):
	"""
	check word for spelling

	**parameters**, **types**,**return**,**return types**::
		:param word: a word
		:type word: unicode string
		:return: return True or False dependent on word being in dict or not
		:rtype: boolean	
	"""
        
	return self.hobj.spell(word.encode("utf8"))
            
