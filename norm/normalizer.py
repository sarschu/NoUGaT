#!/usr/bin/env python
# encoding: utf-8
import sys
import types
from modules.original import Original
from modules.smt import SMT_Token, SMT_Unigram, SMT_Bigram, SMT_Cascaded
from modules.spellcheck import Hunspell
from modules.compound import Compound
from modules.wordsplit import Word_Split
from modules.flooding import Flooding
from modules.abbreviation import Abbreviation
from modules.new_NE import New_NE
from modules.transliterate import Transliterate
from modules.phonemic import Phonemic
from data import Text
from evaluate import Evaluate
import os
import re
import util
import subprocess
import itertools
import time
import random
import xmlrpclib as x
import codecs
import hunspell
import logging

# from modules import g2p, hunspell, orig, cascade
normalizer_log = logging.getLogger("norm.normalizer")

class Normalizer(object):
    """Pipeline for text normalization

    	Programm flow:
        it gets the preprocessed text
        it flooding corrects
        its sends this corrected version to the
        different modules
        it takes the output per sentence and writes to phrase table
        it starts the moses decoder with this phrase table
        it returns the normalized sentence

	
	
    """

    def __init__(self,filtering,language, SMT_token, SMT_unigram, SMT_bigram, SMT_decision, MOSES_PATH, MOSES_SERVER, CRF_PATH, LM_PATH, SETTING, modules,eval_dir="no_eval",**kwargs):
	"""
	**parameters**, **types**::
		:param filtering: is there any filtering used: soft or hard or none
		:type filtering: string
		:param language: the language of the text you want to normalize, choose from 'en' and 'nl', default is 'nl'
		:type language: string 
		:param SMT_tokmodel: path to the SMT token model
		:type SMT_tokmodel: string
		:param SMT_unimodel: path to the SMT unigram model
		:type SMT_unimodel: string 
		:param SMT_bimodel: path to the SMT bigram model
		:type SMT_bimodel: string
		:param SMT_decision: path to the SMT decision model
		:type SMT_decision: string		
		:param MOSES_PATH: path to Moses executable
		:type MOSES_PATH: string
		:param MOSES_SERVER: path to Mosesserver executable
		:type MOSES_SERVER: string
		:param CRF_PATH: path to crf_test executable
		:type CRF_PATH: string
		:param LM_PATH: path to language model
		:type LM_PATH: string
		:param SETTING: train setting you want to use: for english: bal, ask, twe, unb, you. for dutch: bal, unb, sms, sns, twe
		:type SETTING: string
		:param modules: the modules used for normalization
		:type modules: list of strings
		:param eval_dir: keyword argument. Path to directory to which all evaluation files are written
		:type eval_dir: string


	
	A hunspell object is initialized
	The modules are initialized
	"""

        super(Normalizer, self).__init__()
        if eval_dir != "no_eval":
		self.eval = True
		self.e = Evaluate(self,eval_dir)
	else:
		self.eval = False		        
        self.language = language    
        if self.language =="en":
            self.hobj = hunspell.HunSpell('/usr/share/myspell/dicts/en_US.dic', '/usr/share/myspell/dicts/en_US.aff')
        elif self.language =="nl":
            self.hobj = hunspell.HunSpell('/usr/share/myspell/dicts/new_nl_dict.dic', '/usr/share/myspell/dicts/nl.aff')#extended dict version for Dutch, word list from Dutch wiki dump
        self.filtering = filtering
	self.SMT_tokmodel = SMT_token
	self.SMT_unimodel = SMT_unigram
	self.SMT_bimodel = SMT_bigram
	self.SMT_decision = SMT_decision
	self.MOSES_PATH = MOSES_PATH
	self.MOSES_SERVER= MOSES_SERVER
	self.CRF_PATH = CRF_PATH
	self.LM_PATH = LM_PATH
	self.SETTING = SETTING 
        self.ori_tgt_map =[]
        self.initialize_modules(modules)

        #hard filter list
        self.correction_list=[]
	#soft filter list
        self.soft_list=[]
	#accounts for diff number of features in case of soft filtering (1 for hunspell)
	self.feature_increase = 1

        
    def normalize_text(self,t,csv_sent):
	"""
	returns the normalized sentences in a list
	
	the preprocessed text is first flooding corrected
	then the messages are sent into the pipeline and the normalized sentence is returned

        **parameters**, **types**,**return**,**return types**::
		:param t: object from class Text, containing the original and the preprocessed string 
		:type t: Text object
		:param csv_sent: gold standard sentence in case of normalization, otherwise empty
		:type csv_sent: dictionary
		:return: return normalized sentences
		:rtype: list of strings
	"""        
	assert isinstance(t, Text)
	self.csv_sent = csv_sent
	#in case you run in evaluation mode
	if self.eval:
		self.e.realign_goldstandard(t)
		
        flood = Flooding(self)
	flood_cor = flood.flooding_correct(t.text_prepro)
	normalizer_log.info("run normalization")
	norm_sentences=[]
	#if hard filtering is turned on
	self.correction_list=[]
	if self.filtering == "hard":
		p = Preclassifier(self)
		self.correction_list = p.hard_filtering(self,t.text_prepro)
	
	else:
		for i in range(0,len(t.text_prepro.split())):
                	self.correction_list.append(i)
                	
        if self.filtering =="soft":
		
		self.p = Preclassifier(self)
		self.soft_list = self.p.hard_filtering(self,t.text_prepro)
		
		
        norm_sentences.append(self._normalize_sentence(flood_cor))
        normalizer_log.info("normalizer finished")
        
        return norm_sentences
        
        

    
    def start_server_mode(self):
        """
	start Moses server mode for all three SMT systems

	the SMT modules use the Moses server mode which is started in the beginning of 
	one run for each of the three modes: Token, Unigram and Bigram. They run on a random 
	port between 30000 and 40000. The pids are stored and the server mode is stopped in case of
	error or sucessful finish. Each Moses server waits for a certain amount of seconds after 	 start up to ensure it has enough time to run properly in the background.
	The server modes use the .ini files which are located in ../static/Moses/decoder_files. In 		the ini files themselves you can see which phrase table or language model is accessed.
	"""
        pids=[]
        logfile = util.logfile
        os.system('export LC_ALL="C"')
        
        
        normalizer_log.info("start token server mode")
        log = open(logfile,"a")
        port_tok= str(random.randint(30000, 40000))
        p1 = subprocess.Popen(self.MOSES_SERVER+" -f "+self.SMT_tokmodel +" --server-port "+ port_tok +" --server-log "+util.LOG_DIR+"/server/moses_server_token.log",stdout=log,stderr=log,shell=True)
        log.close()
        pids.append(p1)
        time.sleep(10)
        self.s_token = x.ServerProxy("http://localhost:"+port_tok+"/RPC2",allow_none=True)
        normalizer_log.info("start unigram server mode")
        log = open(logfile,"a")
        port_uni= str(random.randint(30000, 40000))
        p2 = subprocess.Popen(self.MOSES_SERVER+" -f "+ self.SMT_unimodel+" --server-port "+ port_uni +" --server-log "+util.LOG_DIR+"/server/moses_server_unigram.log",stdout= log,stderr=log,shell=True)
        log.close()
        pids.append(p2)
        time.sleep(10)
        self.s_unigram = x.ServerProxy("http://localhost:"+port_uni+"/RPC2",allow_none=True)
        normalizer_log.info("start bigram server mode")
        log = open(logfile,"a")
        port_bi=str(random.randint(30000, 40000))
        p3 = subprocess.Popen(self.MOSES_SERVER+" -f "+self.SMT_bimodel +" --server-port "+ port_bi +" --server-log "+util.LOG_DIR+"/server/moses_server_bigram.log",stdout= log,stderr=log,shell=True)
        log.close()
        pids.append(p3)
        time.sleep(10)
        self.s_bigram = x.ServerProxy("http://localhost:"+port_bi+"/RPC2",allow_none=True)
                        
       
        self.pids=pids
        return pids
    
    def initialize_modules(self, mods):
	"""
	initialize the different module objects

	The module objects are initialized onces for every normalization run. The 
	order of the initialization is important since this order is the same as the 
	weights for the modules in the ini files. 

	For English there are 10 modules:

	Word_Split, Compound, Original, Abbreviation, SMT_Token, SMT_Unigram, SMT_Bigram, SMT_Cascaded, Transliterate, Hunspell

	For Dutch there are 11 modules:

	Word_Split, Compound, Phonemic, Original, Abbreviation, SMT_Token, SMT_Unigram, SMT_Bigram, SMT_Cascaded, Transliterate, Hunspell
	"""

      
	self.modules =[]
	#make an object out of strings in input list
	for m in mods:
		cmd = "mod = %s(self)" % m
		exec cmd
		self.modules.append(mod)
	if self.filtering =="soft":
		self.modules.insert(0,New_NE(self))
	if self.eval:
		self.e.open_cer_log()

        
    def _kill_server_mode(self,proc):
	"""
	kill Moses server mode with the help of the process id.

	**parameters**, **types**::
		:param proc: the process ideas collected when starting up server modes
		:type proc: list of integers	
	
	forces the kill of all running processes with the respective process id
	"""

        for p in proc:
            id1 = p.pid
            os.kill(id1,9)
            os.kill(id1+1,9)
    
    
    def _normalize_sentence(self, sentence):
	"""
	normalize the message, running all modueles and combining their output

	**parameters**, **types**,**return**,**return types**::
		:param sentence: preprocessed and flooding corrected text message
		:type sentence: unicode string
		:return: return normalized sentences
		:rtype: list of strings	

	first all modules generate their suggestion, then these suggestions are collected
	and written out to a phrase table, then the decision module generates one normalized 		sentence
	"""        
	phrase_dict = {}
	if self.eval:
		self.ori_sug_map=[]

	#generate suggestions per options
        for m in self.modules:
            
            print m
            output_system = m.generate_alternatives(sentence,self.correction_list)
		
	    if self.eval: 
	    	self.e._append_cer(self.csv_sent,output_system,m,"tgt")
	    	self.ori_sug_map = self.e.evaluate(output_system,self.csv_sent,m,self.ori_sug_map,"ori","tgt")
            normalizer_log.debug(output_system)
            #compile a dictionary holding all suggestions and original strings. This looks like that
	    # phrase dict:
	    #(u'females', {'module': [<modules.wordsplit.Word_Split object at 0x2c03e10>, <modules.wordsplit.Word_Split object at 0x2c03e10>, <modules.compound.Compound object at 0x2c03e90>, <modules.compound.Compound object at 0x2c03e90>, <modules.original.Original object at 0x2c03f50>, <modules.original.Original object at 0x2c03f50>, <modules.abbreviation.Abbreviation object at 0x2c12190>, <modules.abbreviation.Abbreviation object at 0x2c12190>, <modules.smt.SMT_Token object at 0x2c12b10>, <modules.smt.SMT_Token object at 0x2c12b10>, <modules.smt.SMT_Unigram object at 0x2c12cd0>, <modules.smt.SMT_Unigram object at 0x2c12cd0>, <modules.smt.SMT_Bigram object at 0x2c97350>, <modules.smt.SMT_Bigram object at 0x2c97350>, <modules.smt.SMT_Cascaded object at 0x3ec0210>, <modules.smt.SMT_Cascaded object at 0x3ec0210>, <modules.transliterate_new_unbal.Transliterate_new_unbal object at 0x3ec0250>, <modules.transliterate_new_unbal.Transliterate_new_unbal object at 0x3ec0250>, <modules.spellcheck.Hunspell object at 0x3ec0290>, <modules.spellcheck.Hunspell object at 0x3ec0290>], 'ori': [u'females']})
	

	    for num,item in enumerate(output_system):
	        ori,alternatives = item
        
	        for alt in alternatives:
                    if alt.strip() not in phrase_dict:
                        phrase_dict[alt.strip()]={"module":[],"ori":[ori.strip()]}
                    phrase_dict[alt.strip()]["module"].append(m)
                    

        phrase_table_path = util.get_random_phrase_table_path(prefix = "phrase_table")
        self._write_phrase_table(phrase_dict, phrase_table_path)
        
        print "phrase table written"
        res_decision,normalized_sentence = self._call_moses(sentence, phrase_table_path)
        normalized_sentence= unicode(normalized_sentence, 'utf-8')
        if self.eval:
        	self.e._append_cer(csv_sent,res_decision,"normalized","tgt")
                self.e.evaluate(res_decision, csv_sent, "decision",{},"ori","tgt")
        print "sent  normalized"
        return normalized_sentence
       
            
    
    def _write_phrase_table(self, phrase_dict, phrase_dict_location):
	"""
	write out the phrase table for the run of the decision module

	**parameters**, **types**::
		:param phrase_dict: a dictionary holding all suggestions, with the information of the modules that suggested it and the original token
		:type phrase_dict: dictionary
		:param phrase_dict_location: the path to the phrase table
		:type phrase_dict_location: string
	"""
        
	print "writing...."
        fout = codecs.open(phrase_dict_location, "w", "utf8")
        fout.writelines(self._generate_phrase_table(phrase_dict))
        fout.close()
    
    def _generate_phrase_table(self, phrase_dict):
        """
	generate the per line entry of a phrase table

        **parameters**, **types**::
		:param phrase_dict: a dictionary holding all suggestions, with the information of the modules that suggested it and the original token
		:type phrase_dict: dictionary


	iterate over the phrase_dict and compile an etry of the followng format for each 
	suggestion
	
	ori ||| sug ||| 0 1 0 1 0 1 ....

	the 0 and 1 indicate which module returned the suggestion. The order of the modules is 
	given my the initialization of the modules.
	The last 0 or 1 says if hunspell can find the suggestion as a word or not.
        """
	if self.eval:
		self.e.evaluate_overall(self.ori_sug_map)
	
	#add info about filtering to phrase_dict		
	if self.filtering =="soft":
	
		phrase_dict = self.p.soft_filtering(self.soft_list,phrase_dict,ori_sug_map)
		self.feature_increase +=1
		
        for alternative in phrase_dict.iteritems():
	    # in case you want to use empty module, you have to comment this out	
	    if alternative[1] =="":
	        continue
    
            for i,ori in enumerate(alternative[1]["ori"]):
           
	        modules=""
	        hs_feature=0
	        if util.check_hunspell(self,alternative[0]): 
		    hs_feature=1
	            
	                  
	        for mod in self.modules:
	            if mod in alternative[1]["module"]:
	                modules = modules + str(1)+ " "
	                    
	            else:
	                modules = modules + str(0)+ " "
	                
	        #compile the filter features if turned on        
	        if self.filtering=="soft":
			if "NE" in alternative[1]["module"]:
		                modules = modules + str(1)+ " "
		        else: 
		                modules = modules + str(0)+ " "
		        if "PRE" in alternative[1]["module"]:
		                modules = modules + str(1) +" "
		        else: 
		                modules = modules + str(0)+" "

	    modules = modules.strip() +" "+ str(hs_feature)

	    yield u"%s ||| %s ||| %s\n" % (alternative[1]["ori"][i], alternative[0],modules)


    def _call_moses(self, s, phrase_table):
	"""
	decide for a combination of suggestions

	**parameters**, **types**,**return**,**return types**::
		:param s: is the original message that has also been forwarded to the modules 
		:type s: unicode string
		:param phrase_table: is the path to the phrase table
		:type phrase_table: string
		:return: return normalized sentences
		:rtype: string	
	

	Moses is called including the phrase table that has been generated from the suggestions.
	Using a language model and the phrase table with its features, Moses translates the original sentence into the normalized sentence.
	"""

        normalizer_log.info("start decision module")
        logfile = util.logfile
        log = open(logfile,"a")
        echo = subprocess.Popen(['echo',s.encode("utf8")],stdout=subprocess.PIPE)
	
	proc = subprocess.Popen([self.MOSES_PATH,'-v','2', '-f', self.SMT_decision, '-ttable-file', '0 0 0 '+str(len(self.modules)+self.feature_increase)+' ' + phrase_table, '-lmodel-file', '8 0 5 ' + self.LM_PATH],stdin = echo.stdout, stdout= subprocess.PIPE, stderr= subprocess.PIPE,shell=False)

        out,err = proc.communicate()
	align_text = re.findall("Source and Target Units:.*]",err)

        alignments= re.findall("\[\[(\d+)\.\.(\d+)\]:(.*?)(?= :: c)",align_text[0])
        input_tokens = s.split()
        result_list=[]
        for el in alignments:
            result_list.append([" ".join(input_tokens[int(el[0]):int(el[1])+1]),[unicode(el[2].strip(),"utf8")]])
        log.close()
        normalizer_log.debug("debug decisionmod")
        normalizer_log.debug(result_list)
        
        os.system("rm "+phrase_table)
        normalizer_log.info("finished decision module")
        
        return result_list,out
    
   
        
        

