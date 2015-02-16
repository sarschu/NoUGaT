#!/usr/bin/env python
# encoding: utf-8

import os
import json
import re
import codecs
import random
import sys
import subprocess
import util
import logging
import socket
v = False
#logfiles
rewrite_log = logging.getLogger("norm.rewrite")
logfile = util.logfile

###all the substitution 
pretok1 = re.compile("([^ !\?\.,;:A-Z]+)([.!;,?:]+)([^ !\?,\.;:]+)")
pretok2 = re.compile("([^ !\?\.,;:]+)([.!;,?:]+)([^ !\?,\.;:A-Z]+)")
pretok3 = re.compile("([^ !\?\.,;:A-Z]+)([.!;,?:]+)")
pretok4 = re.compile("( ')([A-Za-z0-9]{2,}) ")
smi1 =re.compile(r"B-?(\)\)?)")
smi2 =re.compile(r"<+/*3+")
smi3 =re.compile(r"\^[_]?\^")
smi4 =re.compile(r"\([a-zA-Z]{,2}\)")
smi5 =re.compile(r"[O>C}\]\[)(]+[-~]?[;:x8=][)(]?")
smi6 =re.compile(r"[;:=][',]?[-~]?(['3s/xSdDpPcCoO#@*$|\[\]\)]+|\)|\(\(?)=?")
smi7 =re.compile(r"[;:8=][',]?[-~]?([sxSdDpPcCoO#@*$|\[\]\)]+|\)|\(\(?)=?")
smi8 =re.compile(r"x[',]?[-~]?([3sSdDPcCO#@*$|\[\]\)]+|\)|\(\(?)=?")
smi9= re.compile(r"\[[^\[ \]]+\]")
smi10=re.compile(r"[-~]+'")
smi11=re.compile(r"[oO0n][.,][n0oO]")
smil12=re.compile(r" xp ")
p = re.compile(r"\[[a-z=]+\]")  
rep1 = re.compile(r"\[[^\[ \]]*\]")
rep2 = re.compile("#ERROR!:parse") 
low=re.compile(r'([A-Z]{2,})')
email=re.compile(r'[^ ]+\@[^ ]+\.[^ \n]+')
pipe=re.compile(r"\|")     
hyp1=re.compile(r"http:/\S+")
hyp2=re.compile(r"www\.\S+") 
tok1=re.compile("[!,;.'?] [!.,;?]") 
hasht =re.compile(r"#([\w\d]+)")
spaces=re.compile(" +")
at = re.compile("@ ")
placehol1=re.compile(ur"([^ ])([•±∞™])")
placehol2 = re.compile(ur"([•±∞™])([^ ])")


class Rewrite(object):
    '''
	This class preprocesses the text including tokenization, special character replacement, 
	deletion of more than one whitespace.



	INPUT: line (@janthans @SvenOrnelis BBQ? Wie, wat , waar? :-D #aanwezig) 

	OUTPUT: tokenized sentence with replacements (@janthans @SvenOrnelis BBQ? Wie, wat , waar? • aanwezig)

	Placeholders list sign "•" 

    '''


    def __init__(self,normalizer):
	"""
	**parameters**, **types**::
    		:param normalizer: an object of the class Normalizer
    		:type word: Normalizer object

	"""
	super(Rewrite,self).__init__()
	
	

    def replace_smileys(self,t):
	'''
	replace all smiley characters with a special character	

	**parameters**, **types**,**return**,**return types**::
    		:param t: input text
    		:type t: Unicode string	
		:return: the string with replacement characters for smileys
		:rtype: Unicode string	
	'''

	t = smi1.sub(u"•", t)
	t = smi2.sub(u"•", t)
	t = smi3.sub(u"•", t)
	t = smi4.sub(u"•", t)
	t = smi5.sub(u"•",t)
	t = smi6.sub(u"•", t)
	t = smi7.sub(u"•", t)
	t = smi8.sub(u"•", t)
	t = smi10.sub(u"•", t)
	t = smi11.sub(u"•", t)
	t = smil12.sub(u"•", t)
	#    t = re.sub(r"([^ ])±", r"\1 •", t)
	if v: print repr(t)
	    
	return t

    def tolower(self,t):
	'''
	lowercase string

	**parameters**, **types**,**return**,**return types**::
    		:param t: input text
    		:type t: Unicode string	
		:return: the string in lowercase
		:rtype: Unicode string	
	'''

	return t.group(0).lower()

    def reduce_allcaps(self,t):
	'''
	lowercase sequences of more than 1 uppercased letter

	**parameters**, **types**,**return**,**return types**::
    		:param t: input text
    		:type t: Unicode string	
		:return: the string with replacement characters for smileys
		:rtype: Unicode string	
	'''

	t = low.sub(tolower, t)
	return t

	
    def replace_tags(self,t):
	'''
	replace [*] with replacement character 

	**parameters**, **types**,**return**,**return types**::
    		:param t: input text
    		:type t: Unicode string	
		:return: the string with replacement characters for tags
		:rtype: Unicode string	
	'''

	t = rep1.sub(u"•", t)
	t = rep2.sub(u"•", t )
	if v: print repr(t)
	    
	return t

    def replace_pipe(self,t):
	'''
	replace | wirht " "

	**parameters**, **types**,**return**,**return types**::
    		:param t: input text
    		:type t: Unicode string	
		:return: the string with replacement of |
		:rtype: Unicode string	
	'''

	t = pipe.sub(" ",t)
	return t



    def replace_hyperlinks(self,t):
	'''
	replace hyperlink with replacement character

	**parameters**, **types**,**return**,**return types**::
    		:param t: input text
    		:type t: Unicode string	
		:return: the string with replacement characters for hyperlinks
		:rtype: Unicode string	
	'''

	t = hyp1.sub(u"•", t)
	t = hyp2.sub(u"•", t)
	t = email.sub(u"•", t)
	if v: print repr(t)
	    
	return t


    def tokenize(self,t,norm):#post tokenize '?
	'''
	tokenize the text with a special pretokenizer and a perl script from TreeTagger

	**parameters**, **types**,**return**,**return types**::
    		:param t: input text
    		:type t: Unicode string	
		:param norm: a normalizer for language information
		:type norm: Normalizer object		
		:return: the tokenized string
		:rtype: Unicode string	
	'''


	#pretokenize
	#doesnt split uppercasE.Uppercase (protect N.V.A)
        #splits cases like word.Word -> word . Word
	#splits cases like word!word -> word ! word
	t = pretok1.sub("\g<1> \g<2> \g<3>",t)
	#splits cases like worD.word worD . word
	t = pretok2.sub("\g<1> \g<2> \g<3>",t)
	#splits cases like word. -> word .
	t = pretok3.sub("\g<1> \g<2>",t)
	   
	t = t.strip()

	#run the TreeTagger tokenizer
	echo = subprocess.Popen(["echo",t.encode("utf8")],stdout=subprocess.PIPE)
	if norm.language == "nl":
	    proc = subprocess.Popen(["perl",util.STATIC_DIR+"/tokenizer/utf8-tokenize.perl","-a",util.STATIC_DIR+"/tokenizer/dutch-abbreviations"],stdin=echo.stdout,stdout=subprocess.PIPE,shell=False)
	    out = proc.communicate()[0]
	elif norm.language == "en":
            proc = subprocess.Popen(["perl",util.STATIC_DIR+"/tokenizer/utf8-tokenize.perl", "-e"],stdin=echo.stdout,stdout=subprocess.PIPE,shell=False)
	    out = proc.communicate()[0]    
	t =unicode(out.replace("\n"," "),'utf-8')

	found = tok1.findall(t)
	while found !=[]:
            for element in found:
		replacement = element.replace(" ","")
		t = t.replace(element,replacement)
            found = tok1.findall(t)

	return t    


    def replace_hashtags(self,t):
	'''
	replace #tags like #workisboring with a special character

	**parameters**, **types**,**return**,**return types**::
    		:param t: input text
    		:type t: Unicode string	
		:return: the string with replacement characters for hash tags
		:rtype: Unicode string	
	'''

	t = hasht.sub(u"•", t)
	    
	return t

    def replace_spaces(self,t):
	'''
	replace all spaces with just one space

	**parameters**, **types**,**return**,**return types**::
    		:param t: input text
    		:type t: Unicode string	
		:return: the string with max one whitespace in a row
		:rtype: Unicode string	
	'''

	t = spaces.sub(" ",t)
	return t


    def replace_linebreaks(self,t):
	'''
	delete the string <LINEBREAK>

	**parameters**, **types**,**return**,**return types**::
    		:param t: input text
    		:type t: Unicode string	
		:return: the string without <LINEBREAK>
		:rtype: Unicode string	
	'''

	return t.replace("<LINEBREAK>", u"")
	    

	
    def rewrite_text(self,t, norm):
	'''
	call all the replacement and preprocesing methods on the input

	**parameters**, **types**,**return**,**return types**::
    		:param t: input text
    		:type t: Unicode string	
		:param norm: a normalizer for language information
		:type norm: Normalizer object	
		:return: the preprocessed string
		:rtype: Unicode string	
	'''

	rewrite_log.debug("rewrite text")
	t = t.strip() # Strip leading and trailing whitespace
	t = " "+t
	t = self.replace_linebreaks(t) # Replace <LINEBREAK> by special character
	t = self.replace_hashtags(t)
	t = self.replace_hyperlinks(t)
	t = self.replace_tags(t)
	t = self.replace_smileys(t)
	t = self.replace_pipe(t) # For Moses
	t = self.tokenize(t,norm) # Pretokenise and run Texsis
	t = self.correct_at_tok(t) # Corrects tokenized at-replies (remove space after @)
	t = self.tokenize_placeholders(t)
	t = self.replace_spaces(t) # Correct space flooding to 1 space
	t = t.strip()
	rewrite_log.debug("text rewritten")

        return t


    def correct_at_tok(self,t):
	'''
	correct missed tokenization with @

	**parameters**, **types**,**return**,**return types**::
    	    :param t: input text
    	    :type t: Unicode string	
	    :return: the string with whitespace deleted after @
	    :rtype: Unicode string	
	'''
	t = at.sub("@",t)
	return t
	    
	    
    def tokenize_placeholders(self,t):
	'''
	correct the tokenization of the special characters

	**parameters**, **types**,**return**,**return types**::
    	    :param t: input text
    	    :type t: Unicode string	
	    :return: string with special characters being tokenized
	    :rtype: Unicode string	
	'''
	before_t = placehol1.sub(ur"\1 \2", t)
	after_t  = placehol2.sub(ur"\1 \2", before_t)
        return after_t

	
