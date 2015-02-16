#!/usr/bin/env python
# encoding: utf-8       


import sys
import os
import logging
import codecs
import random
import util
import string

phonemic_log = logging.getLogger("norm.module.phonemic")

import subprocess
from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary
from alignment.sequencealigner import SimpleScoring, GlobalSequenceAligner
import os

class Phonemic(object):
    '''
    Access via web service the MBT grapeme-to-phoneme-to-grapheme conversion.
    Implemented by Guy DePauw.
	
    '''


    def __init__(self):
        
        super(Phonemic, self).__init__()
        

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
        phonemic_log.info("start phonemic module")
        
	#replace a whole bunch of special characters the learner cannot handle. Later replace it back.
	t = sentence.replace(" ","%20")
        t = t.replace(u"&",u"ʚ")
        t= t.replace(u"\n","%0A")
        t= t.replace(u"|",u"ʘ")
        t=t.replace(u";",u"Þ")
        t =t.replace(u"-",u"¥")
        t = t.replace(u"#",u"¤")
        t =t.replace("\u200e","")
        #smt_log.info("run token module")
        filename = "phone_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
	#call Antwerps webservice via wget
        proc = subprocess.Popen(['wget','http://www.clips.uantwerpen.be:3000/g2p2g?text='+t.encode('utf-8'),"-O",filename],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False) 
        out,err = proc.communicate()
        output= codecs.open(filename,"r","utf8").readlines()
        out = unicode(output[0].strip())
        out = out.replace(u"¤",u"#")
	out=out.replace(u"¥",u"-")
        out = out.replace(u"ʚ",u"&")
        out= out.replace(u"ʘ",u"|")
        out= out.replace(u"%0A",u"\n")
        out = out.replace(u"£",u" ")
        out = out.replace(u"%20",u" ")
        out=out.replace(u"Þ",u";")
        os.remove(filename)

        phonemic_log.debug(err)

        returnList = util.align(sentence, out)
	for num,elem in enumerate(returnList):
            if num not in corr_list:
                returnList[num]=[elem[0],[elem[0]]]
        	
       	
        phonemic_log.debug(returnList)
        phonemic_log.info("finished phonemic module")
	
        #smt_log.info("token module finished")
        return returnList
    
 
