#!/usr/bin/env python
# encoding: utf-8

from __future__ import division

import os
import string
import random
import datetime
from os.path import dirname
from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary
from alignment.sequencealigner import SimpleScoring, GlobalSequenceAligner
import numpy
import codecs
import sys
import itertools
from Levenshtein import distance

ROOT_DIR = os.path.join(dirname(dirname(os.path.abspath(__file__))),"norm")
LOG_DIR = os.path.join(dirname(dirname(os.path.abspath(__file__))), "log")
STATIC_DIR = os.path.join(dirname(dirname(os.path.abspath(__file__))), "static")
TMP_DIR = "/tmp"

t= datetime.datetime.now()
timestamp = t.strftime('%m_%d_%Y_%H_%M_%S')
logfile = ROOT_DIR+"/../log/runs/normalization_"+timestamp+".log"

def get_random_tmp_path(prefix = "norm"):
    filename = str(prefix) + "_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
    return os.path.join(TMP_DIR, filename)

def get_random_phrase_table_path(prefix="phrase_table"):
    filename = str(prefix) + "_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
    return os.path.join("../log/phrasetables", filename)

def get_random_tmp_eval_path(prefix = "phrase_table"):
    filename = str(prefix) + "_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
    return os.path.join(TMP_DIR+"/eval_options", filename)

def calculate_cer(ref,hyp):
    #!/usr/bin/env python

# Compute word error or character error rates.
# Usage: 
# To compute WER: error-rates.py wer REFERENCE-DOC HYPOTHESIS-DOC
# To compute CER: error-rates.py cer REFERENCE-DOC HYPOTHESIS-DOC
    errs = []
    size = 0
    
    R = distance(ref, hyp)
    return "{0:.3f}".format(float(R)/float(len(ref)))

def calculate_wer(r,h):
    #Grzegorz Chrupala
    r = r.split()
    h = h.split()
    d = numpy.zeros((len(r)+1)*(len(h)+1), dtype=numpy.uint8)
    d = d.reshape((len(r)+1, len(h)+1))
    for i in range(len(r)+1):
        for j in range(len(h)+1):
            if i == 0:
                d[0][j] = j
            elif j == 0:
                d[i][0] = i
    
        # computation
    for i in range(1, len(r)+1):
        for j in range(1, len(h)+1):
            if r[i-1] == h[j-1]:
                d[i][j] = d[i-1][j-1]
            else:
                substitution = d[i-1][j-1] + 1
                insertion    = d[i][j-1] + 1
                deletion     = d[i-1][j] + 1
                d[i][j] = min(substitution, insertion, deletion)
    
    return (float(d[len(r)][len(h)]) / float(len(r)))
    
def check_hunspell(n,word):
	"""
	check word for spelling

	**parameters**, **types**,**return**,**return types**::
		:param word: a word
		:type word: unicode string
		:return: return True or False dependent on word being in dict or not
		:rtype: boolean	
	"""
        language = n.language
        word_split = word.split()
        is_word=False
        for word in word_split:
             
            is_word = n.hobj.spell(word.encode("utf8"))
            if is_word == False: 
                break
           
        return is_word
        

def align(ori,tgt):

        tgt_ori=tgt.strip()
	ori_ori=ori.strip()
	ori_ori_split=ori.strip().split()
	tgt_ori_split = tgt.strip().split()
	ori=u"␄"+ori.strip().lower()
	tgt=u"␄"+tgt.strip().lower()
	ori = list(ori)
	tgt = list(tgt.replace("  "," "))
	results=[]
	if len(ori)<len(tgt):
	    for i in range(0,len(tgt)-len(ori)):
	        ori.append(u"␄")
	if len(tgt)<len(ori):
	    for i in range(0,len(ori)-len(tgt)):
	        tgt.append(u"␄")
	if len(ori_ori_split)<250:

		ori = Sequence(ori)
		tgt = Sequence(tgt)
		v = Vocabulary()
		aEncoded = v.encodeSequence(ori)
		bEncoded = v.encodeSequence(tgt)

		# Create a scoring and align the sequences using global aligner.
		scoring = SimpleScoring(2, -1)
		aligner = GlobalSequenceAligner(scoring, -2)
		score, encodeds = aligner.align(aEncoded, bEncoded, backtrace=True)

		alignment = v.decodeSequenceAlignment(encodeds[0])


		ori_al = list(alignment.first)
		tgt_al = list(alignment.second)
		ori_al.append(" ")
		tgt_al.append(" ") 
		o=""
		t=""

		if len("".join(ori_al).split()) == len(ori_ori_split):
	    	    for i,el in enumerate(ori_al):
	#	        if i ==0:

	#	            continue

			if (not (el ==u' ' and tgt_al[i]==u' ')):
			    o+=el
			    t+=tgt_al[i]
			
			else:
			    originaltok=""
			    originaltgt=""
			    for dings in range(len(o.split())):
			         originaltok += ori_ori_split.pop(0)+" "
			    for dings in range(len(t.split())):
			         originaltgt += tgt_ori_split.pop(0)+" "

			    results.append([originaltok.strip(),[originaltgt.strip()]])
			    o=""
			    t=""


		else:
		        man_log = codecs.open("man_align.log","a","utf8")
		        
		        man_log.write("target\n")
		    	man_log.write(tgt_ori+"\n")
		    	man_log.write("original\n")
		    	man_log.write(ori_ori+"\n")
		    	man_log.write("\n\n\n")
		    	man_log.close()
		        sentence_split=ori_ori.split()
			out_split=tgt_ori.split()
			if len(sentence_split)>len(out_split):
			    for ind,el in enumerate(out_split):
			        if ind == len(out_split)-1:
			            results.append([unicode(" ".join(sentence_split[ind:])),[unicode(el)]])
			        else:
			            results.append([unicode(sentence_split[ind]),[unicode(el)]])
			elif len(out_split)>len(sentence_split):
			    for ind,el in enumerate(sentence_split):
			        if ind == len(sentence_split)-1:
			            results.append([unicode(el),[unicode(" ".join(out_split[ind:]))]]) 
			        else:
			            results.append([unicode(el),[unicode(out_split[ind])]]) 
			else:
			    for ind,el in enumerate(out_split):
				results.append([unicode(sentence_split[ind]),[unicode(el)]])
	
	else:
		        man_log = codecs.open("man_align.log","a","utf8")
		        
		        man_log.write("target\n")
		    	man_log.write(tgt_ori+"\n")
		    	man_log.write("original\n")
		    	man_log.write(ori_ori+"\n")
		    	man_log.write("\n\n\n")
		    	man_log.close()
		        sentence_split=ori_ori.split()
			out_split=tgt_ori.split()
			if len(sentence_split)>len(out_split):
			    for ind,el in enumerate(out_split):
			        if ind == len(out_split)-1:
			            results.append([unicode(" ".join(sentence_split[ind:])),[unicode(el)]])
			        else:
			            results.append([unicode(sentence_split[ind]),[unicode(el)]])
			elif len(out_split)>len(sentence_split):
			    for ind,el in enumerate(sentence_split):
			        if ind == len(sentence_split)-1:
			            results.append([unicode(el),[unicode(" ".join(out_split[ind:]))]]) 
			        else:
			            results.append([unicode(el),[unicode(out_split[ind])]]) 
			else:
			    for ind,el in enumerate(out_split):
				results.append([unicode(sentence_split[ind]),[unicode(el)]])
		
	
        return results
    

# def calculate_wer(ref,hyp):
#     errs = []
#     size = 0
#     print itertools.izip(ref, hyp)
#     for r, h in itertools.izip(ref, hyp):
#         words_r = r.split()
#         words_h = h.split()
#         print words_r
#         print words_h
#         if words_r and words_h:
#             R = distance(words_r, words_h)
#             errs.append(R)
#             size += len(words_r)
#     print "{0:.3f}".format(sum(errs)/size)
#     
#     
