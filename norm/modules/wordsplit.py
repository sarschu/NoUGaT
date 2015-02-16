#!/usr/bin/env python
# encoding: utf-8

import logging
import util
split_log = logging.getLogger("norm.module.wordsplit")
import subprocess

class Word_Split(object):
    '''
    This class contains functions with which subsequent words can be checked for "compoundness".
    It uses word frequencies from the cgn corpus to decide if a word should be split or not.
    It makes use of the decompounder perl script that comes together with Moses.
    '''

    def __init__(self,normalizer):
	"""
	**parameters**, **types**::
    		:param normalizer: an object of the class Normalizer
    		:type word: Normalizer object

	"""
        self.normalizer = normalizer
        super(Word_Split,self).__init__()
              
        
    
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
        split_log.info("start split checker")
        split_sent = sentence.split()
        result = []
	
	#call the word split script from python (included in the static directory)
        for w in range(0,len(split_sent)):
            if len(split_sent[w]) >1 and w in corr_list:
                
                if self.normalizer.language =="nl":
                    decomp = subprocess.Popen(["perl",util.STATIC_DIR+"/decompounder/compound-splitter.perl","-min-size", "2", "-model", util.STATIC_DIR+"/decompounder/decompound-nl-cgn"],stdout=subprocess.PIPE,stdin=subprocess.PIPE,shell=False)
                elif self.normalizer.language =="en":
                    decomp = subprocess.Popen(["perl",util.STATIC_DIR+"/decompounder/compound-splitter.perl","-min-size", "2", "-model", util.STATIC_DIR+"/decompounder/decompound-en-opensub"],stdout=subprocess.PIPE,stdin=subprocess.PIPE,shell=False)
                

                stdout,stderror=decomp.communicate(split_sent[w].encode("utf8")+" ")

                
                result.append([split_sent[w],[unicode(stdout.strip(), 'utf-8')]])
    

            else:
                result.append([split_sent[w],[split_sent[w]]])
               
        split_log.debug(result)
        split_log.info("finished split checker")

        return result
