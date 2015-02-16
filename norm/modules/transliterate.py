#!/usr/bin/env python
# encoding: utf-8

import sys
from sklearn import svm, cross_validation
from sklearn.metrics import classification_report, accuracy_score
import sys, codecs, getopt
from sklearn.externals import joblib
import numpy as np
import util
import logging
translit_log = logging.getLogger("norm.module.transliterate")

class Transliterate(object):
    '''
    use a transliterate approach on character level. Used classifier is SVM.
    The class has been implemented by Guy DePauw.
    '''


    def __init__(self,normalizer):
	"""
	**parameters**, **types**::
    		:param normalizer: an object of the class Normalizer
    		:type word: Normalizer object

		"""
        super(Transliterate, self).__init__()
	if normalizer.language == "nl":
	    self.language = "dutch"
	elif normalizer.language == "en":
	    self.language = "english"
	self.set = normalizer.SETTING
	

    def vectorize(self,string):
	'''
	prepare the data for the learner
	
	**parameters**, **types**::
		:param string: flooding corrected original message
		:type string: unicode string 
	
	the string is prepared and appended to 'data' which is a global list	
	
	'''
	nL = 5
	nR = 5
	global data
	data = []
	string = list(string)

	for i in range(len(string)):
		instance = []
		j = 1
		while j <= nL:
			if i - j < 0:
				instance.insert(0,'@')
			else: 
				instance.insert(0,string[i-j])
			j += 1

		instance.append(string[i])	
		j = 1
		while j <= nR:
			if i + j >= len(string):
				instance.append('@')
			else :
				instance.append(string[i+j])
			j += 1

		features = instance
		v = {}
		for i in range(len(features)-1):
			key = str(i)+'-'+instance[i]
			v[key] = 1
		instance = []
		for feature in defaultFeatures:
			if feature in v.keys():
				instance.append(1)
			else:
				instance.append(0)
		data.append(instance)

    def run_transliterate(self,sentence):
	'''
	run the model on the data

	**parameters**, **types**,**return**,**return types**::
		:param sentence: flooding corrected original message
		:type sentence: unicode string 
		:return: transliterated sentence
		:rtype: unicode string
	
	the setting determines which data has been used for training

	the model and all the belonging files are stored in the static directory
	
	'''
	
	setting = self.set

	

	modelName = util.STATIC_DIR+"/transliterate/"+self.language+"/"+setting+".model.pkl"
	featuresName = util.STATIC_DIR+"/transliterate/"+self.language+"/"+setting+".feat.pkl"
	global defaultFeatures, nL, nR, data
	nL = 5
	nR = 5				
	clf = joblib.load(modelName)

	defaultFeatures = joblib.load(featuresName)
		
	line = sentence.replace(' ',u'£')
	self.vectorize(line)
	y_pred = clf.predict(data)
	translation =[]
	
	for character in y_pred:

		translation.append(unicode(character.replace(u'£',' ').replace(u'§','')))
	return "".join(translation)
	

  
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
        translit_log.info("start transliterate module")
        ori_sent = sentence
        sentences=[]
	# in order to avoid problems with alignment, sentences longer than 50 words are split
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
	trans_log=""
	#the transliteration is performed and the original and transliterated sentences are aligned
        for sentence in sentences:
	        translation = self.run_transliterate(sentence)
		trans_log+=" "+translation
                returnList += util.align(sentence,translation)

	
	#since the alignment method sometimes has problems due to a bad transliteration: in case it fails, 
	#align the tokens one by one and the reminder all to the last token (a little desperate, i know...)
        if returnList ==[] and out !="":
                sentence_split=sentence.split()
        	out_split=out.split()
        	if len(sentence_split)>len(out_split):
        	    for ind,el in enumerate(out_split):
        	        if ind == len(out_split)-1:
        	            returnList.append([unicode(sentence_split[ind:]),[unicode(el)]])
        	        else:
        	            returnList.append([unicode(sentence_split[ind]),[unicode(el)]])
        	elif len(out_split)>len(sentence_split):
        	    for ind,el in enumerate(sentence_split):
        	        if ind == len(sentence_split)-1:
        	            returnList.append([unicode(el),[unicode(out_split[ind:])]]) 
        	        else:
        	            returnList.append([unicode(el),[unicode(out_split[ind])]]) 
        	else:
        	    for ind,el in enumerate(out_split):
        		returnList.append([unicode(sentence_split[ind]),[unicode(el)]])
        for num,elem in enumerate(returnList):
            if num not in corr_list:
                returnList[num]=[elem[0],[elem[0]]]
                
        translit_log.debug(returnList)
        translit_log.info("finished transliterate module")        
        return returnList
 
