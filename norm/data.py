#!/usr/bin/env python
# encoding: utf-8

import sys
from prepro.rewrite import Rewrite

#ACCEPTED_TEXT_TYPES = ("sms", "sns", "twe","cgn", "bnc")

class Text(object):
    """Represents a text, such as an SMS, a blogpost or a tweet"""
    def __init__(self, text, n, r):
	'''
	create a Text object which holds the different stages of the message: ori, prepro, output
	
	**parameters**, **types**,**return**,**return types**::
		:param n: a normalizer object
		:type n: Normalizer object
		:param r: object having functions to rewrite the text 
		:type r: Rewrite object
	
	'''

        self._norm = n
	self.r = r
        self._validate_input(text)
        self.text_orig = text
        self.text_prepro = self._preprocess()
    
    def _validate_input(self, t):
	'''
	validate that input string is unicode	

	**parameters**, **types**,**return**,**return types**::
		:param t: an input message
		:type t: unicode string
		:return: input is a unicode string or not
		:rtype: boolean	
	'''

        # Checks should return False in case of invalid input
        if not isinstance(t, unicode):
            sys.stderr.write("Invalid input: should be a unicode string, was %s" % type(t))
            return False
        return True
    
    def _preprocess(self):
	'''
	preprocess input text (tokenization, special character replacement)
	'''
        if self.text_orig.strip() != u'':
            prepro = self.r.rewrite_text(self.text_orig, self._norm)
        else:
            prepro = u"\n"
        return prepro



