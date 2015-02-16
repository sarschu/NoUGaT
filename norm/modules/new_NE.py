#!/usr/bin/env python
# encoding: utf-8  

import os
import codecs
import util
import subprocess
import shutil
import re
import json
import logging
ne_log = logging.getLogger("norm.module.named_entity")

class New_NE(object):
    '''
    This module uses a crf model to predict whether a token is a 
    named entity or not. 

    This modules in not included by default.

    '''

    def __init__(self,normalizer):
	"""
	**parameters**, **types**::
    		:param normalizer: an object of the class Normalizer
    		:type word: Normalizer object

	The language, and the language-dependent gazetteer are initialized.
	"""
	
        super(New_NE, self).__init__()
        self.lang = normalizer.language
        self.texsis_dir =  util.get_random_tmp_path()
        if self.lang =="nl":
            gaz = open(util.STATIC_DIR+"/NE/gaz_dutch.json")
        elif self.lang == "en":
            gaz = open(util.STATIC_DIR+"/NE/gaz_english.json")
        self.gazjson = json.load(gaz)
    
    def generate_alternatives(self,sentence,corr_list):
	'''
   	Run a crf classifier to find out if a token is a NE or not.

	**parameters**, **types**,**return**,**return types**::
		:param sentence: flooding corrected original message
		:type sentence: unicode string 
		:param corr_list: list containing all indices of the tokens that have to be normalized (hard filtering just some, otherwise all, not used here)
		:type corr_list: list of integers
		:return: original tokens aligned with the ਊ token to hand over the information that a token is an NE of the form [[ori,[ori]],	[ori2,	[u'ਊ']]]
		:rtype: list of lists

	The information if a token is an NE or not is not included directly but can be used as a feature in the phrase table. 
	
   	 '''

        ne_log.info("start named entity module")

        self.write_file(sentence)
        self.run_texsis()
        self.make_feature_file()
        self.run_crf()
        results = self.get_labels(sentence)
        self.clean_up()
        ne_log.debug(results)
        ne_log.info("finished named entity module")
        return results
    
    def run_texsis(self):
	'''
	Texsis is used to pos tag the sentence. This information is used as a feature in the crf classification.
	'''
        if self.lang == "nl":    
        	tex = subprocess.Popen(["pos",self.texsis_dir,"nl"],shell=False)
        	tex.wait()
        elif self.lang =="en":
        	tex = subprocess.Popen(["pos",self.texsis_dir,"en"],shell=False)
        	tex.wait()
                
    def write_file(self,sent):
	'''
	The sentence is written to a file (one word per line) and stored in a directory. Texsis can be run on this directory to 
	generate pos tags for each word in the sentence. 

	**parameters**, **types**,**return types**::
		:param sentence: flooding corrected original message
		:type sentence: unicode string 
	'''
        os.system('mkdir '+self.texsis_dir)
        out_file = codecs.open(self.texsis_dir+"/texsis.tok","w","utf8")
        words = sent.split()
        for word in words:
            out_file.write(word+"\n")
        out_file.close()
    
    def make_feature_file(self):
	'''
	An external python script (language specific) is called to compile the feature files used for NE prediction.
	The script expects the following input:

	* language
	* texsis POS file
	* texsis tok file
	* gazetteer file
	* celex file
	* output file
	
	All these files can be found in the static directory.
	'''
        #os.system("python "+util.STATIC_DIR+"/NE/make_features.py nl "+self.texsis_dir+"/texsis.pos "+self.texsis_dir+"/texsis.tok "+util.STATIC_DIR+"/NE/gazetteer "+util.STATIC_DIR+"/NE/celex /tmp/featurefile")
        if self.lang == "nl":
            ff = subprocess.Popen(["python",util.STATIC_DIR+"/NE/make_features_dutch.py","nl",self.texsis_dir+"/texsis.pos",self.texsis_dir+"/texsis.tok",util.STATIC_DIR+"/NE/gazetteer.dutch",util.STATIC_DIR+"/NE/celex_dutch",self.texsis_dir+"/featurefile"],shell=False)
        elif self.lang == "en":
            ff = subprocess.Popen(["python",util.STATIC_DIR+"/NE/make_features_english.py","en",self.texsis_dir+"/texsis.pos",self.texsis_dir+"/texsis.tok",util.STATIC_DIR+"/NE/gazetteer.english",util.STATIC_DIR+"/NE/celex_english",self.texsis_dir+"/featurefile"],shell=False)
        ff.wait()
        
    def run_crf(self):
        out = codecs.open(self.texsis_dir+"/ne_tagged","w")
        if self.lang == "nl":
            crf = subprocess.Popen(["/usr/bin/crf_test","-m",util.STATIC_DIR+"/NE/model_dutch",self.texsis_dir+"/featurefile"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False)
        elif self.lang == "en":
            crf = subprocess.Popen(["/usr/bin/crf_test","-m",util.STATIC_DIR+"/NE/model_english",self.texsis_dir+"/featurefile"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False)

        crf.wait()
        output=crf.communicate()[0]
        out.write(output)
        out.close()
    
        #os.system("/usr/local/bin/crf_test -m "+util.STATIC_DIR+"/NE/NE_model /tmp/featurefile > /tmp/ne_tagged")
    
    def get_labels(self, sentence):
	'''
	
	For each word in the input sentence the lable (NE or not) is extracted from the file predicted by crf.
	If the label is 1 a special character is returned as a suggestion, if not the original token is returned.

	**parameters**, **types**,**return**,**return types**::
		:param sentence: flooding corrected original message
		:type sentence: unicode string 
		:return: original tokens aligned with the suggestion of the form [[ori,[sug]],[ori2,[u"ਊ"]]]
		:rtype: list of lists

	'''
        results = []
        split_sent = sentence.split()
        ne_file = open(self.texsis_dir+"/ne_tagged","r")
        ne_lines = ne_file.readlines()
        result_rules = self._run_named_entity_replace(sentence)
        for num,line in enumerate(ne_lines):
            if line.strip():
                token = split_sent[num]
                label = line.split("\t")[-1].strip()
                if label == "1":
                    results.append([unicode(token), [u"ਊ"]])
                elif self._replace_atreplies(token)==u"ਊ":
                    results.append([unicode(token), [u"ਊ"]])
                elif result_rules[num][1]==[u"ਊ"]:
                    results.append([unicode(token), [u"ਊ"]])
                else:
                    results.append([unicode(token), [unicode(token)]])
                
        ne_file.close()
        return results

    def _replace_atreplies(self,t):
	'''
	
	@replies are returned as a special character

	**parameters**, **types**,**return**,**return types**::
		:param t: token
		:type t: unicode string 
		:return: t itself or  u"ਊ" in case the token is an @-reply
		:rtype: list of lists

	'''
        t = re.sub(r"@[\w\d]+", u"ਊ", t)
        return t


    def clean_up(self):
	'''
	Delete the directory with all texsis files.
	'''
        shutil.rmtree(self.texsis_dir)

    def _run_named_entity_replace(self,text_string):
	'''
	Rule based component of the module. Search for upper case first letters, search in gazetteer list,

	**parameters**, **types**,**return**,**return types**::
		:param text_string: flooding corrected original sentence
		:type t: unicode string 
		:return: original tokens aligned with the suggestion of the form [[ori,[sug]],[ori2,[u"ਊ"]]]
		:rtype: list of lists
	
	'''
        ori = text_string
        returnlist=[]
        text = text_string.split()
        
        for i in range(0,len(text)):
            upper_token = False
            if i !=0 and len(text[i])>1:
                if text[i-1].strip() not in ["!",".","?","-",":","..."] and text[i][0].isupper() and text[i][1:].islower():
                    upper_token = True
            if text[i].lower() in self.gazjson or upper_token:
                returnlist.append([unicode(ori[i]),[u"ਊ"]])
            else:
                returnlist.append([unicode(ori[i]),[text[i].strip()]]) 
            
        
       
        return returnlist       
        
