#!/usr/bin/env python
# encoding: utf-8


import sys
import logging
import re
import time
import util
from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary
from alignment.sequencealigner import SimpleScoring, GlobalSequenceAligner
smt_log = logging.getLogger("norm.module.smt")

class SMT(object):
    '''
    This class contains functions that are useful for the SMT in general. 
    The functions are used by the different SMT approaches like cascaded, token etc. 
    '''

    def __init__(self):
        super(SMT,self).__init__()
        
    def run_moses(self,sentence,type):
	'''
	Sent a request to the running Moses server dependent on the type of SMT you wish.
	
	**parameters**, **types**,**return**,**return types**::
		:param sentence: flooding corrected original message
		:type sentence: unicode string 
		:param type: one out of the values "token", "bigram" or "unigram"
		:type type: string
		:return: holds the alignment, translation etc returned by the Moses server. access text via translation["text"]
		:rtype: dictionary

	
	'''
        if type == "token":
            params = {"text":sentence, "align":"true", "report-all-factors":"true"}
            translation = self.normalizer.s_token.translate(params)
            time.sleep(0.05)
        elif type == "bigram":
            params = {"text":sentence, "align":"true", "report-all-factors":"true"}
            translation = self.normalizer.s_bigram.translate(params)
            time.sleep(0.05)
        elif type == "unigram":
            params = {"text":sentence, "align":"true", "report-all-factors":"true"}
            translation = self.normalizer.s_unigram.translate(params)
            time.sleep(0.05)
        return translation
    
    #this aligns the results of the moses translation to the original tokens
    #this is necessary to keep track of which word was transformed into which string
    def combine_trans(self,trans,original):
	'''
	use dynamic alignment to align original tokens to translation tokens
	
	**parameters**, **types**,**return**,**return types**::
		:param trans: translation for the input strubg
		:type trans: unicode string 
		:param original: the orignial string
		:type type: unicode string
		:return: original tokens aligned with the suggestion of the form [[ori,[sug]],[ori2,[sug2]]]
		:rtype: list of lists

	'''

        #transList = trans['align']
        #wordsOri = original
        wordsTrans0 = re.sub("(\|UNK[BQk]{,1})+","",trans)
        result = util.align(original,wordsTrans0)

        return result
    
    def convert_string_to_ngrams(self,s, ngram):
	'''
	convert string into a string split into ngrams with # as replacement for whitespace characters.

	**parameters**, **types**,**return**,**return types**::
		:param s: token string
		:type s: unicode string 
		:param ngram: n in ngram
		:type ngram: integer
		:return: string in ngram format
		:rtype: unicode string
	
	'''
        # Lowercase string, replace spaces with #, add # for sentence start and end
        s = u"#" + s.replace(" ", "#") + u"#"
        # Pad all characters with spaces
        return " ".join(s[i:i+ngram] for i in range(len(s)-ngram+1))
    
    def convert_ngrams_to_string(self,s, ngram):
	'''
	convert ngram string into a token string.

	**parameters**, **types**,**return**,**return types**::
		:param s: ngram string
		:type s: unicode string 
		:param ngram: n in ngram
		:type ngram: integer
		:return: string in token format
		:rtype: unicode string
	'''
        s = s+"#"
        s = s.replace("  "," ").strip()
        s = s.split(" ")
        strings = []
        for num,el in enumerate(s):
          if len(el) < ngram:
              s.pop(num)
        for n in range(ngram):
            string = s[0][:n] + "".join([x[n] for x in s]) + s[-1][n+1:]
            strings.append(string.replace("#", " "))

        return strings[0]

class SMT_Token(SMT):
    '''
    This class contains functions with which the SMT on the token level can be performed. 
    '''    
    def __init__(self,normalizer):
	"""
	**parameters**, **types**::
    		:param normalizer: an object of the class Normalizer
    		:type word: Normalizer object

	"""
        self.normalizer = normalizer
        SMT.__init__(self)

        
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
        smt_log.info("run token module")
	#replace characters Moses cannot handle
        sentence_in = sentence.replace("[",u"ʘ")
        sentence_in = sentence_in.replace("]",u"ʨ")
        time.sleep(0.05)
        sentences=[]
	#make sure the sentences is not longer than 50 words (Moses out of memory -> search trees too big)
	#if so process 50 token long parts of the sentence separately	
        if len(sentence_in.split()) > 50:
	        while len(sentence_in.split())> 50:
        	    sentence_split=sentence_in.split()
       		    sentences.append(" ".join(sentence_split[:50]).strip())
       		    sentence_in = " ".join(sentence_split[50:])
       		if len(sentence_in.strip()) != 0:
	       	        sentences.append(sentence_in.strip())
        else:
            sentences.append(sentence_in)
        output_sentences=[]

        resultList=[]
	log_sent=""
	#align each of the subsentence translations back to its input and combine the resulting lists of lists
        for sentence in sentences:

            trans = SMT.run_moses(self,sentence,"token")
	    log_sent+=" "+ trans["text"].replace(u"ʘ","[").replace(u"ʨ","]")

            resultList += SMT.combine_trans(self,trans["text"].replace(u"ʘ","[").replace(u"ʨ","]"),sentence.replace(u"ʘ","[").replace(u"ʨ","]"))

	for num,elem in enumerate(resultList):
            if num not in corr_list:
                resultList[num]=[elem[0],[elem[0]]]
                
        smt_log.debug(resultList)
         
        smt_log.info("token module finished")
        return resultList

    
        

class SMT_Unigram(SMT):
    '''
    This class contains functions with which the SMT on the unigram level can be performed. 
    ''' 
    def __init__(self,normalizer):
	"""
	**parameters**, **types**,**return types**::
    		:param normalizer: an object of the class Normalizer
    		:type word: Normalizer object

	"""	
        self.normalizer = normalizer
        SMT.__init__(self)   
     

        
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
        smt_log.info("run unigram module")
        ori_sent = sentence
        sentence = sentence.replace("[",u"ʘ")
        sentence = sentence.replace("]",u"ʨ")
        sentence = sentence.replace(u"#",u"␄")
        sentences=[]
	#make sure the sentences is not longer than 50 characters (Moses out of memory -> search trees too big)
	#if so process 50 token long parts of the sentence separately	
        if len(sentence.split()) > 50:
	        while len(sentence.split())>50:
        	    sentence_split=sentence.split()
       		    sentences.append(" ".join(sentence_split[:50]).strip())
       		    sentence = " ".join(sentence_split[50:])
       		if len(sentence.strip()) != 0:
	       	        sentences.append(sentence.strip())
        else:
            sentences.append(sentence)
        output_sentences=[]
        returnList=[]
        sent_char=""
	#combine alignments and sentences back to one output list
        for sentence in sentences:
            
            sent_char_part = SMT.convert_string_to_ngrams(self,sentence, 1)
            time.sleep(0.05)
            trans = SMT.run_moses(self,sent_char_part,"unigram")
                       

            sent_char +=" "+sent_char_part
	    trans = unicode(trans["text"]).replace(" ","").replace("#"," ").strip().replace(u"ʘ","[").replace(u"␄",u"#").replace(u"ʨ","]")
	    trans = re.sub("(\|UNK[BQk]{,1})+","",trans)
            returnList += util.align(sentence.replace(u"ʘ","[").replace(u"ʨ","]").replace(u"␄",u"#"),trans)

	for num,elem in enumerate(returnList):
            if num not in corr_list:
                returnList[num]=[elem[0],[elem[0]]]

        return returnList

        smt_log.debug(returnList)

        smt_log.info("unigram module finished")
        
        
class SMT_Bigram(SMT):
    '''
    This class contains functions with which the SMT on the bigram level can be performed. 
    '''    
    def __init__(self,normalizer):
	"""
	**parameters**, **types**::
    		:param normalizer: an object of the class Normalizer
    		:type word: Normalizer object

	"""	
        self.normalizer = normalizer 
        SMT.__init__(self)
        

    

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
        smt_log.info("start bigram module")
        original = sentence
        sentence = sentence.replace("[",u"ʘ")
        sentence = sentence.replace("]",u"ʨ")
	sentence = sentence.replace(u"#",u"␄")
        sentences=[]
	#make sure the sentences is not longer than 50 character bigrams (Moses out of memory -> search trees too big)
	#if so process 50 token long parts of the sentence separately	
        if len(sentence.split()) > 50:
	        while len(sentence.split())> 50:
        	    sentence_split=sentence.split()
       		    sentences.append(" ".join(sentence_split[:50]).strip())
       		    sentence = " ".join(sentence_split[50:])
       		if len(sentence.strip()) != 0:
	       	        sentences.append(sentence.strip())
        else:
            sentences.append(sentence)
        output_sentences=[]
        returnList=[]
	#combine the alignemnts of each of the subparts back to one result list
        for sentence in sentences:

            sent_char = SMT.convert_string_to_ngrams(self,sentence,2)
            time.sleep(0.05)
            trans = SMT.run_moses(self,sent_char,"bigram")
            trans = unicode(trans["text"])
            trans = re.sub("(\|UNK[BQk]{,1})+","",trans)
            translation=SMT.convert_ngrams_to_string(self,trans,2)
            
            translation = translation.replace(u"ʘ","[").replace(u"ʨ","]").replace(u"␄",u"#")
            returnList += util.align(sentence.replace(u"ʘ","[").replace(u"ʨ","]").replace(u"␄",u"#"),translation)
       	
       	for num,elem in enumerate(returnList):
            if num not in corr_list:
                returnList[num]=[elem[0],[elem[0]]]     
            
        smt_log.debug(returnList)
        smt_log.info("bigram module finished")
        return returnList
    
class SMT_Cascaded(SMT):
    '''
    This class contains functions with which the SMT on first the token 
    and subsequently on the unigram level can be performed. 
    '''    
    def __init__(self,normalizer):
	"""
	**parameters**, **types**::
    		:param normalizer: an object of the class Normalizer
    		:type word: Normalizer object

	"""	
        self.normalizer = normalizer
        SMT.__init__(self)
        
    def generate_alternatives(self,sentence,corr_list):
	'''
   	Generate suggestion

	**parameters**, **types**,**return types**::
		:param sentence: flooding corrected original message
		:type sentence: unicode string 
		:param corr_list: list containing all indices of the tokens that have to be normalized (hard filtering just some, otherwise all)
		:type corr_list: list of integers
		:return: original tokens aligned with the suggestion of the form [[ori,[sug]],[ori2,[sug2]]]
		:rtype: list of lists
	
   	 '''
        smt_log.info("cascaded module started")
        token = SMT_Token(self.normalizer)
        #first call the token module
        original = sentence.split()
        token_list2 = token.generate_alternatives(sentence,corr_list)

        tokSent=""
        uniSent=""
	#combine the outout of token module to an input sentence for unigram module
        for i in range(0,len(token_list2)):
            tokSent = tokSent + token_list2[i][1][0]+" "
        tokSent = tokSent.strip()
	#run unigram module on output of token modle
        unigram = SMT_Unigram(self.normalizer)
        tok_ori=tokSent.split()
        returnList1 = unigram.generate_alternatives(tokSent,corr_list)
	#align the input back to the outout
        for i in range(0,len(returnList1)):
            uniSent = uniSent + returnList1[i][1][0]+" "

	results = util.align(sentence,uniSent)
        
        for num,elem in enumerate(results):
            if num not in corr_list:
                results[num]=[elem[0],[elem[0]]]
                  
        smt_log.debug(results)

        smt_log.info("cascaded module finished")
        return results
            
    
        
