#!/usr/bin/env python
# encoding: utf-8
'''
Created on June 18, 2013

@author: sarah
usage: python run_prepro.py <infile> <outfile>
'''
import logging
import os
import codecs
import sys
sys.path.append(os.getcwd())
import util
from data import Text
from normalizer_preclass import NormalizerPre
from modules.flooding import Flooding


#creates the logging file with the three levels DEBUG, INFO, WARNING

logger = logging.getLogger('norm')
logger.setLevel(logging.DEBUG)
hdlr = logging.FileHandler(util.logfile)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
lang = sys.argv[1]
logger.info(" Starting with the normalization pipeline")
if lang == "nl":
	n = NormalizerPre(language="nl") # In case of English
else:
	n = NormalizerPre(language="en") # In case of English
############## Changes just here ###########################################
inputFile = os.path.abspath(sys.argv[2])
if not os.path.isfile(inputFile):
    print "Usage: python run_prepro.py [inputfile] [outputfile]"
    print "Could not find", inputFile
    sys.exit()
outputFile = os.path.abspath(sys.argv[3])
if os.path.exists(outputFile):
    print "Usage: python run_prepro.py  [inputfile] [outputfile]"
    print outputFile, "already exists"
    sys.exit()

#############################################################################

my_sms_collection = []
f_in = codecs.open(inputFile,"r","utf-8")
#f_in =open(inputFile,"r")
f_out = codecs.open(outputFile,"w","utf-8")
inputlines = f_in.readlines()
f_in.close()
amount = len(inputlines)
counter = 0
deleted=0
f = Flooding(n)
for i in inputlines:

    counter += 1
 
    print "Processing text %d of %d" % (counter, amount)
    sms = Text(unicode(i), n)
    my_sms_collection.append(sms)
    if sms.text_prepro.strip() !="":
        print "preprocessed version"
        f_out.write(f.flooding_correct(sms.text_prepro) + u"\n")
    if sms.text_prepro.strip()=="":
        deleted+=1
        print "LINE DELETE:"


print "There have been %d lines deleted" % (deleted)

f_out.close()
#n.kill_server_mode(pids)
logger.info(" Done! Enjoy your prepocessed text!")
if __name__ == '__main__':
    pass
