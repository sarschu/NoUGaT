#!/usr/bin/env python
# encoding: utf-8
'''
Created on May 31, 2013

@author: sarah
usage: run_norm.py <ini> <inputfile> <outputfile> (<csv_doc> <evalDir>)
'''
#if you want to use the preclassifier, normalizer takes a keyword argument pc=True
#you need a csv file for the evaluation
#you need to specifiy the language

import configparser
import codecs
import logging
import os
from prepro.rewrite import Rewrite
import normalisation
import sys
sys.path.append(os.getcwd())
import util
from data import Text
from normalizer import Normalizer

#from normalizer_preclass import NormalizerPre


#creates the logging file with the three levels DEBUG, INFO, WARNING
config = configparser.ConfigParser()
logger = logging.getLogger('norm')
logger.setLevel(logging.DEBUG)
hdlr = logging.FileHandler(util.logfile+"_untuned_"+sys.argv[2].split("/")[-1])
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)

logger.info(" Starting with the normalization pipeline")
# We may want to work on a corpus of texts, or just on one text.
# A text is e.g. 1 tweet or 1 SMS message.
# If we work on multiple texts, we make a Text instance for each one.
# When instantiating a text, we provide the original text as a unicode string
# (making sure that encoding has been handled), and the text type:
# Or in the case of many texts:
# We also instantiate a Normalizer object, which will do the normalization.

#all expected parameters


config.read(sys.argv[1])
try:
	language = config.get("Language", "ln")
	SMT_token =config.get("SMT", "Token")
	SMT_unigram=config.get("SMT", "Unigram")
	SMT_bigram=config.get("SMT", "Bigram")
	SMT_decision=config.get("SMT","Decision")
	MOSES_PATH=config.get("MOSES-PATH", "Moses")
	MOSES_SERVER=config.get("MOSES-PATH", "Mosesserver")
	CRF_PATH=config.get("CRF-PATH", "CRF")
	SETTING=config.get("SETTING", "train_set")
	LM_PATH=config.get("LM","lm")
	modules_string = config.get("Modules","mod")
	modules = modules_string.split()
	filtering = config.get("Filter","filter")
    

except configparser.NoOptionError:
	raise

#for quantitative analysis
    
#for qualitative and quantitative analysis   
csv_dict={} 

#n = Normalizer(language="nl",pc=True) # In case of Dutch
try:
	if len(sys.argv)==6:
	    n = Normalizer(filtering,language,SMT_token, SMT_unigram, SMT_bigram, SMT_decision, MOSES_PATH, MOSES_SERVER,CRF_PATH, LM_PATH, SETTING, modules,eval_dir=sys.argv[5]) 

	    csv_dict = normalisation.get_linedict_from_csv(sys.argv[4],"utf8")
	    print csv_dict
	    n.e._open_log_for_each_module()
	else:
	    n = Normalizer(filtering,language,SMT_token, SMT_unigram, SMT_bigram, SMT_decision, MOSES_PATH, MOSES_SERVER,CRF_PATH, LM_PATH, SETTING, modules)# In case of Dutch
	# n = Normalizer(language="en") # In case of English
	pids = n.start_server_mode()
	input_file = sys.argv[2]
	output_file=sys.argv[3]
	#rewrite object
	r = Rewrite(n)


	testfile = codecs.open(input_file,"r","utf-8")
	my_sms_collection=[]
	testlines = testfile.readlines()
	for line in testlines:
	    my_sms_collection.append(line)
	print my_sms_collection



	list_of_sms = [Text(sms,n,r) for sms in my_sms_collection]
	print list_of_sms
	outfile = codecs.open(output_file,"w","utf-8")
	for num,sms in enumerate(list_of_sms):# in the case of multiple texts
	    print "inputtext"
	    print sms.text_orig.encode("utf-8")
	    print "preprotext"
	    print sms.text_prepro.encode("utf-8")
	    #empty line in input
	    if sms.text_orig.strip() ==u"":
		sms.text_norm = u"\n"
	    else:
		if csv_dict !={}:
		    sms.text_norm = n.normalize_text(sms,csv_dict[unicode(sms.text_orig.strip()).replace(u"\u200e","").replace(u"\xa0"," ")])
		else:
		    sms.text_norm = n.normalize_text(sms,{})    
	    print "normalized"
	    print sms.text_norm
	    outfile.write(sms.text_norm[0])

	if len(sys.argv)==6:
	    n.e.write_cer_to_file()
	    n.e.write_out_match_num_modules()
	n._kill_server_mode(pids)

except Exception as es:
    err = str(es)
    print err

    n._kill_server_mode(pids)
	
outfile.close()
testfile.close()
logger.info(" Done! Enjoy your normalized text!")
if __name__ == '__main__':
    pass
