#!/usr/bin/env python
# encoding: utf-8
import hunspell
import json
import re
import util

class Flooding(object):
    '''
    this class corrects the flooding of characters and punctionation,
    it reduces flooding to one and two characters and checks whether a correct word emerges
    with the help of spell checking. In case it does it returns the whole sentence
    It also corrects punctuation flooding. It does that in any case.
    '''


    def __init__(self,normalizer):
	"""
	**parameters**, **types**,**return**,**return types**::
    		:param normalizer: an object of the class Normalizer
    		:type word: Normalizer object

	A hunspell object is initialized.

	An abbreviation dictionary is loaded.
	"""
        self.normalizer = normalizer
        super(Flooding, self).__init__()
        
        if self.normalizer.language =="en":
            self.hobj = hunspell.HunSpell('/usr/share/myspell/dicts/en_US.dic', '/usr/share/myspell/dicts/en_US.aff')
        elif self.normalizer.language =="nl":
            self.hobj = hunspell.HunSpell('/usr/share/myspell/dicts/new_nl_dict.dic', '/usr/share/myspell/dicts/nl.aff')
        json_data = open(util.STATIC_DIR + "/flooding/abbrev_dict")
        self.abbrev_dict = json.load(json_data)
    
    def flooding_correct(self,t):
	'''
   	Correct flooding characters and character combinations in t.

	**parameters**, **types**,**return**,**return types**::
		:param t:  original message
		:type t: unicode string 
		:return: flooding corrected original message
		:rtype: unicode string
	
	Two versions of the corrected string are compiled: correction to one or two repetitions. In case
	the correction to one character produces a valid word, take this one, otherwise correct to two characters.
	
	The sentence is corrected word by word and joined in the end.
        '''
        sent_list=[]
        ori = t.split()
        for word in ori:
            w_corrected = self.correct_punctuation_flooding(word)
            two,corr_two = self.correct_flooding_to_two(w_corrected)
            one,corr_one = self.correct_flooding_to_one(w_corrected)
            if one and two:
                sent_list.append(unicode(corr_two))
            elif one and not two:
                sent_list.append(unicode(corr_one))
            else:

                sent_list.append(unicode(corr_two))
        output_sent = " ".join(sent_list)
        return output_sent
    
        
    def correct_punctuation_flooding(self,t):
	'''
   	Correct flooding punctuations using regex matches.

	**parameters**, **types**,**return**,**return types**::
		:param t:  original token
		:type t: unicode string 
		:return: punctuation flooding corrected token
		:rtype: unicode string
	
	Reduce all punctuation flooding to two subsequent characters, just dots are 
	corrected to three.
   	 '''
        # Lowercase the string, to find flooding with case alternation
        # Reduce character repetitions to max 2, except for numbers
        corrected_t = re.sub(r"([.?!:;,])(\1{2,})", r"\1\1", t)
        
        # Replace 2 dots by 3 dots
        corrected_t = corrected_t.replace("..", "...")
        
        # If correction was necessary, return the lowercased corrected string.
        # Else, return the original string with capitalization
        return corrected_t
        
    def correct_flooding_to_two(self,t):
	'''
   	Correct flooding characters using regex matches to two repetitions.

	**parameters**, **types**,**return**,**return types**::
		:param t:  original token
		:type t: unicode string 
		:return: tuple: first part gives information if the suggested token is marked as correct by hunspell, corrected token
		:rtype: tuple(boolean, string)
	
	Reduce all character flooding to two subsequent characters. For Dutch the e is 
	corrected to 3 repetitions first to check if an existing word emerges.
	
   	 '''
        # split the string into tokens. So, each token can be check for its correctness
        if re.findall("e{3,}",t):
            if self.normalizer.language=="nl":
                corrected_t = re.sub(ur"([^e0-9±ਊ•\.])(?i)(\1{2,})", r"\1\1", t,10)
                corrected_t_e_2 = re.sub("e{3,}","ee",corrected_t)
                if self.check_for_correctness(corrected_t_e_2):
                    corrected_t = corrected_t_e_2
                else: corrected_t = re.sub("e{3,}",u"eee",corrected_t)
            else: 
                corrected_t = re.sub(ur"([^0-9±ਊ•\.])(?i)(\1{2,})", r"\1\1", t,10)

        # Reduce character repetitions to max 2, except for numbers
        else:
            corrected_t = re.sub(ur"([^0-9±ਊ•\.])(?i)(\1{2,})", r"\1\1", t,10)
        
        # Reduce repetitions of substrings to max 2

        for i in range(1,10):
            if re.findall(ur"([^0-9±ਊ•\.]{2})(?i)(\1{2,})",corrected_t)==[]:
                break
            corrected_t = re.sub(ur"([^0-9±ਊ•\.]{2})(?i)(\1{2,})", r"\1\1", corrected_t,10)
        for i in range(1,10):
            if re.findall(ur"([^0-9±ਊ•\.]{3})(?i)(\1{2,})",corrected_t)==[]:
                break
            corrected_t = re.sub(ur"([^0-9±ਊ•\.]{2})(?i)(\1{2,})", r"\1\1", corrected_t,10)
        #check whether word exists
        if self.check_for_correctness(corrected_t) or self.check_for_correctness(re.sub("e{3,}",u"eeë",corrected_t)):
                return  True,corrected_t

        else:   return False,corrected_t
      
        # If correction was necessary, return the lowercased corrected string.
        # Else, return the original string with capitalization
    def correct_flooding_to_one(self,t):
	'''
   	Correct flooding characters using regex matches to one repetitions.

	**parameters**, **types**,**return**,**return types**::
		:param t:  original token
		:type t: unicode string 
		:return: tuple: first part gives information if the suggested token is marked as correct by hunspell, corrected token
		:rtype: tuple(boolean, string)
	
	Reduce all character flooding to one subsequent characters.
	
   	 '''
        tokens = t.split()
        flood_corr = []
        for el in tokens:
            flood_corr.append(el)
        for ind,tok in enumerate(flood_corr):
        # Reduce character repetitions to max 2, except for numbers
            corrected_t = re.sub(ur"([^0-9±™•\.!\?,])(?i)(\1{2,})", r"\1", tok,10)
            # if v: print repr(corrected_s)
            
            # Reduce repetitions of substrings to max 2
            for i in range(1,10):
                if re.findall(ur"([^0-9±ਊ•\.]{2})(?i)(\1{2,})",corrected_t)==[]:
                    break
                corrected_t = re.sub(ur"([^0-9±ਊ•\.!\?!,]{2})(?i)(\1{2,})", r"\1", corrected_t,10)
            for i in range(1,10):
                if re.findall(ur"([^0-9±ਊ•\.]{3})(?i)(\1{2,})",corrected_t)==[]:
                    break
                corrected_t = re.sub(ur"([^0-9±ਊ•\.!\?!,]{3})(?i)(\1{2,})", r"\1", corrected_t,10)
            
            # Replace 2 dots by 3 dots
            if self.check_for_correctness(corrected_t):
                return True,corrected_t

            else:    return False,t
                    
                

    def check_for_correctness(self,token):
 	'''
   	Check if token is marked as correct by hunspell or is found in the abbreviation dictionary.

	**parameters**, **types**,**return**,**return types**::
		:param t:  original token
		:type t: unicode string 
		:return: word is correct word or not
		:rtype: boolean
	
   	 '''
 
        if self.hunspell_check(token) or token.lower() in self.abbrev_dict:
            return True
        
        
    def hunspell_check(self,word):
	"""
	check word for spelling

	**parameters**, **types**,**return**,**return types**::
		:param word: a word
		:type word: unicode string
		:return: return True or False dependent on word being in dict or not
		:rtype: boolean	
	"""
        language = self.normalizer.language
        return self.hobj.spell(word.lower().encode("utf8"))
       
        
