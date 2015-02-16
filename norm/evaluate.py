#!/usr/bin/env python
# encoding: utf-8
import sys
import os
import util
import types
from modules.new_NE import New_NE
from prepro.rewrite import Rewrite 
from modules.flooding import Flooding
import codecs
import itertools
import re

class Evaluate(object):
	"""
	This class contains functions to evaluate the 
	performance of modules and the overall sytem
	The evaluation is based on the gold standard annotations read it from the csv files
	
	"""

	def __init__(self,normalizer,eval_dir):
		super(Evaluate, self).__init__()
		self.normalizer = normalizer
		self.eval_dir = eval_dir
		os.system("mkdir "+self.eval_dir)
		self.m_log_list={}
		self.m_log_recall_precision={}
		self.m_wer_values={}
		self.m_cer_list={}
		self.token_log={}
		self.tokens_overall=0
		self.correction_list=[]
		self.pre_class_list={}
		self.tokens_found=0
		self.suggestions_overall=0
		self.not_found=0
		self.m_wer_list={}
		self.m_wer_list2={}
		self.D=0.0
		self.I=0.0
		self.S=0.0
		self.N=0.0
		self.N_tgt=0.0

	def realign_goldstandard(self,t):
	    tok_clean=[]
  	    tgt_clean=[]
    	    ori_clean=[]
	    act_count=0
	    for num,el in enumerate(self.normalizer.csv_sent["tok"]):
	       if el != u"<LINEBREAK>":
	           tok_clean.append(el)
	           act_count+=1
	       else:
	           for n,element in enumerate(self.normalizer.csv_sent["ne"]):
	               if element > act_count:
	                   self.normalizer.csv_sent["ne"][n]=element-1

	    for num,el in enumerate(self.normalizer.csv_sent["tgt"]):
	        if el != u"<LINEBREAK>":
	            tgt_clean.append(el)
            for num,el in enumerate(self.normalizer.csv_sent["ori"]):
	        if el != u"<LINEBREAK>":
	            ori_clean.append(el)
	    self.normalizer.csv_sent["ori"]=ori_clean
	    self.normalizer.csv_sent["tok"]=tok_clean
	    self.normalizer.csv_sent["tgt"]=tgt_clean
    	    self.N_tgt= float(len(" ".join(tgt_clean).replace("<com>","").replace("<COM>","").split()))
	    res_prepro =[]
	    #evaluate the preprocessing
	    r = Rewrite(self.normalizer)
	    for tok in self.normalizer.csv_sent["ori"]:
		res_prepro.append([tok,[r.rewrite_text(tok,self.normalizer)]])

	    self.evaluate(res_prepro, self.normalizer.csv_sent, "prepro_module",{},"ori","tok")
	    
	    flood= Flooding(self.normalizer)

    	    gold_tok =  " ".join(self.normalizer.csv_sent["tok"]).replace(" <split>"," ").replace(" <SPLIT>"," ")     
            flood_cor = flood.flooding_correct(gold_tok)
            res_flood=[]
            before_flood_split = gold_tok.split()  
            flood_cor_split= flood_cor.split()

            for num,tok in enumerate(before_flood_split):
                    res_flood.append([tok,[flood_cor_split[num]]])
            self.evaluate(res_flood, self.normalizer.csv_sent, "flooding",{},"tok","tgt")   


	    self._append_cer(self.normalizer.csv_sent, t.text_orig,"before_prepro","tok")
	    self._append_cer(self.normalizer.csv_sent, gold_tok, "beforeflood","tgt")
	    self._append_cer(self.normalizer.csv_sent,flood_cor,"floodingmodule","tgt")
	    
	    #make the tokenized/flooding corr version the original
	    self.normalizer.csv_sent["ori"]=self.normalizer.csv_sent["tok"]
	    self.normalizer.csv_sent["tgt"]=tgt_clean
	    
	    for index,ori_tok in enumerate(self.normalizer.csv_sent["ori"]):
		if ori_tok =="<split>" or ori_tok=="<SPLIT>":
		    continue
	    
	    floodingcorr = flood.flooding_correct(ori_tok)

	    tok_split = floodingcorr.split()
	    count=0
	    for elem in tok_split:
	            
	        position=index+count
	        self.normalizer.csv_sent["ori"][position]= elem
	        count+=1
	    i=0
	    self.ori_tgt_map=[]
	    while i < len(self.normalizer.csv_sent["ori"]):
		t = self.normalizer.csv_sent["tgt"][i]
		if i != len(self.normalizer.csv_sent["ori"])-1 and (self.normalizer.csv_sent["tgt"][i+1] == "<com>" or self.normalizer.csv_sent["tgt"][i+1] == "<com>") :
		    o = self.normalizer.csv_sent["ori"][i] + " " +self.normalizer.csv_sent["ori"][i+1]
		    i+=2
		    self.ori_tgt_map.append([o,t])
		else:
		    o = self.normalizer.csv_sent["ori"][i]
		    while i < len(self.normalizer.csv_sent["ori"])-1 and (self.normalizer.csv_sent["ori"][i+1] == "<split>" or self.normalizer.csv_sent["ori"][i+1] == "<SPLIT>"):
		        t+= " "+self.normalizer.csv_sent["tgt"][i+1]
		        i+=1
		    i+=1
		    self.ori_tgt_map.append([o,t])
		    
            
		    
	def evaluate(self,output_system,csv_sent,m,ori_sug_map,dep,aim):
	    	indexlist=[]
		if csv_sent !={}:
		    for e in csv_sent[dep]:
			indexlist.append(e)
		skipped=0
		com=False
		lastItem =False
		for num,item in enumerate(output_system):
		    if com == True:
			com = False
			continue
		    ori,alternatives = item
		    
		    #Do this for eval
		    if csv_sent !={}:
			skipped =0
			if m=="prepro_module":
			    if ori == u"<SPLIT>" or ori==u"<split>":
			        continue
			elif len(ori.split())>1:
			    skipped+=1
			num = num+skipped
			ori_split = ori.split()
			target = []
			if num == len(output_system)-1:
			    lastItem = True

			for o in ori_split:
			    index=indexlist.index(o)

			    indexlist[index]="processed"
			    
			    if isinstance(m,New_NE):
			        if index in csv_sent["ne"]:
			            target.append(u"ਊ")
			        else:
			            target.append(csv_sent[aim][index])
			    else:
			        if index != len(csv_sent[aim])-1 and (csv_sent[aim][index+1] == "<com>" or csv_sent[aim][index+1] == "<com> "):
			            target.append(csv_sent[aim][index])
			            if len(ori.split()) ==1:
			                ori= ori + " "+ output_system[num+1][0]
			                alternatives[0] = alternatives[0] +" "+ output_system[num+1][1][0]
			                alternatives[0] =alternatives[0].strip()
			                com = True
			        else:
			            target.append(csv_sent[aim][index])
			    while index< len(csv_sent[dep])-1 and( csv_sent[dep][index+1]==u"<split>" or csv_sent[dep][index+1]==u"<SPLIT>"):                            
			        target.append(csv_sent[aim][index+1])
			        index+=1
			    
			tgt = " ".join(target)

			if (tgt=="<split>" or tgt=="<SPLIT>") and (ori =="<split>" or ori =="<SPLIT>"):
			    continue
			if tgt=="<com>" or tgt=="<com>":
			    continue
			tgt =tgt.replace("<com>","").replace(" <split>","").replace(" <SPLIT>","").replace("<com> ","")
			if not (tgt=="" and alternatives[0]=="" and ori ==""):
			    self._log_sugg_per_module(ori, alternatives,ori.strip(),tgt.strip(), m,lastItem)

		    for o in ori.split():
			#bug here

		    	if o in ori_sug_map:
		    	    print ori_sug_map[o]
			    ori_sug_map[o].append(alternatives[0])
			else:
			    ori_sug_map[o]=[alternatives[0]]
	
		    
		return ori_sug_map
	
	
	
	def _open_log_for_each_module(self):
		for m in self.normalizer.modules:
			self.m_wer_list2[m]={"I":0,"D":0,"S":0,"N":0}
			self.m_wer_values[m]=[]
			self.token_log[m]={"corrected":[],"not_found":[],"over_corrected":[]}
		 	self.m_log_recall_precision[m]={"corrected":0,"not_corrected":0,"nothing_to_correct":0,"tokens_overall":0,"num_sugg":0,"over_correction":0}
			self.m_log_list[m] =codecs.open(self.eval_dir+"/module_log_"+str(m),"a","utf8")
		self.m_log_list["decision"]=codecs.open(self.eval_dir+"/module_log_decision","a","utf8")
		self.m_wer_list2["decision"]={"I":0,"D":0,"S":0,"N":0}
		self.m_wer_values["decision"]=[]
		self.token_log["decision"]={"corrected":[],"not_found":[],"over_corrected":[]}
		self.m_log_recall_precision["decision"]={"corrected":0,"not_corrected":0,"nothing_to_correct":0,"tokens_overall":0,"num_sugg":0,"over_correction":0}
		if self.normalizer.filtering in ["hard","soft"]:
		    self.token_log["preclass"]={"corrected":[],"not_found":[],"over_corrected":[]}
		    self.m_log_recall_precision["preclass"]={"corrected":0,"not_corrected":0,"nothing_to_correct":0,"tokens_overall":0,"num_sugg":0,"over_correction":0}
		    self.m_log_list["preclass"] =codecs.open(self.eval_dir+"/module_log_"+str("preclassification"),"a","utf8")
		self.token_log["prepro_module"]={"corrected":[],"not_found":[],"over_corrected":[]}
		self.m_wer_list2["prepro_module"]={"I":0,"D":0,"S":0,"N":0}
		self.m_wer_values["prepro_module"]=[]
		self.m_log_recall_precision["prepro_module"]={"corrected":0,"not_corrected":0,"nothing_to_correct":0,"tokens_overall":0,"num_sugg":0,"over_correction":0}
		self.m_log_list["prepro_module"] =codecs.open(self.eval_dir+"/module_log_"+str("preclassification"),"a","utf8")
		self.token_log["flooding"]={"corrected":[],"not_found":[],"over_corrected":[]}
		self.m_wer_list2["flooding"]={"I":0,"D":0,"S":0,"N":0}
		self.m_wer_values["flooding"]=[]
		self.m_log_recall_precision["flooding"]={"corrected":0,"not_corrected":0,"nothing_to_correct":0,"tokens_overall":0,"num_sugg":0,"over_correction":0}
		self.m_log_list["flooding"] =codecs.open(self.eval_dir+"/module_log_"+str("preclassification"),"a","utf8")
			
			
	def write_out_match_num_modules(self):


		print self.m_log_recall_precision
		for el in self.m_log_recall_precision:
		    if isinstance(el,Original):
			for mod in self.m_log_recall_precision:
			    self.m_log_recall_precision[mod]["nothing_to_correct"] = self.m_log_recall_precision[el]["nothing_to_correct"]

			break
		for m in self.m_log_recall_precision:
		    self.m_log_list[m] =codecs.open(self.eval_dir+"/module_log_"+str(m),"a","utf8")

		    if m =="preclass":
			pre = float(self.m_log_recall_precision[m]["corrected"]+self.m_log_recall_precision[m]["nothing_to_correct"])/float(self.m_log_recall_precision[m]["num_sugg"])
			rec= float(self.m_log_recall_precision[m]["corrected"]+self.m_log_recall_precision[m]["nothing_to_correct"])/float(self.m_log_recall_precision[m]["tokens_overall"])
			self.m_log_list[m].write("\n\n\n")
		    else:
			print m    
			pre = (float(self.m_log_recall_precision[m]["corrected"]+self.m_log_recall_precision[m]["nothing_to_correct"]-self.m_log_recall_precision[m]["over_correction"]))/float(self.m_log_recall_precision[m]["num_sugg"])
			rec= (float(self.m_log_recall_precision[m]["corrected"]+self.m_log_recall_precision[m]["nothing_to_correct"]-self.m_log_recall_precision[m]["over_correction"]))/float(self.m_wer_list2[m]["N"])
			self.m_log_list[m].write("\n\n\n")
		    
		    self.m_log_list[m].write("The following tokens could be corrected: \n")
		    [self.m_log_list[m].write(y+"\n") for y in self.token_log[m]["corrected"]]
		    self.m_log_list[m].write("The following tokens have been over corrected: \n")
		    [self.m_log_list[m].write(y+"\n") for y in self.token_log[m]["over_corrected"]]
		    self.m_log_list[m].write("The following tokens could NOT be corrected: \n")
		    [self.m_log_list[m].write(y+"\n") for y in self.token_log[m]["not_found"]]
		    self.m_log_list[m].write("Corrected: "+ str(self.m_log_recall_precision[m]["corrected"]) +"\n")
		    self.m_log_list[m].write("Not_corrected: "+ str(self.m_log_recall_precision[m]["not_corrected"]) +"\n")
		    self.m_log_list[m].write("The module over corrected: "+ str(self.m_log_recall_precision[m]["over_correction"]))
		    self.m_log_list[m].write("Nothing_to_change: "+ str(self.m_log_recall_precision[m]["nothing_to_correct"]) +"\n")
		    self.m_log_list[m].write("Tokens overall: "+ str(self.tokens_overall) +"\n")
		    self.m_log_list[m].write("Precision: "+ str(pre) +"\n")
		    self.m_log_list[m].write("Recall: "+ str(rec) +"\n")
		    if m !="preclass":
			self.m_log_list[m].write("Number tokens in reference: "+str(self.m_wer_list2[m]["N"])+"\n")
		    self.m_log_list[m].write("num sugg all: "+ str(self.m_log_recall_precision[m]["num_sugg"]) +"\n")

		    self.m_log_list[m].close()
		overallperf = open("../log/"+self.eval_dir+"/overall_numbers","w")
		overallperf.write("From "+str(self.tokens_overall)+" tokens \n there has been found "+str(self.tokens_found)+"\n "+str( self.suggestions_overall)+" suggestions have been generated.\n "+str(self.not_found)+" tokens have not been corrected.")
		precision= float(self.tokens_found)/float(self.suggestions_overall)
		recall= float(self.tokens_found)/(self.tokens_overall)
		overallperf.write("This results in recall: "+str(recall)+" \n")
		overallperf.write("This results in precision: "+str(precision)+" \n")

		overallperf.close()

		    #open lists that can hold cer and wer values for each sentence        
	def open_cer_log(self):
		for m in self.normalizer.modules:
		    self.m_wer_list[m]=[]
		    self.m_cer_list[m] =[]
		self.m_wer_list["before_prepro"]=[]


		self.m_wer_list["floodingmodule"]=[] 

		 
		self.m_wer_list["beforeflood"] = []

	      
		self.m_wer_list["normalized"] = []


		self.m_cer_list["before_prepro"]=[]
		self.m_cer_list["floodingmodule"]=[]    
		self.m_cer_list["beforeflood"] = []
		self.m_cer_list["normalized"] = []
	
	def _close_log_for_each_module(self):
		for m in self.m_log_list:
		    self.m_log_list[m].close()

		    #calculate CER and WER with dynamic alignment and save one value per sentence
	def _append_cer(self,csv,hyp,mod,aim):
		print mod
		if type(hyp) is types.UnicodeType:
		    ref = " ".join(csv[aim]).replace(u"<com>","").strip().replace(u"<LINEBREAK>","").strip()
		    hyp = hyp.replace("<NEWLINE>","").replace(u"<com>","")
		    self.m_cer_list[mod].append(float(util.calculate_cer(ref.lower(),hyp.lower())))
		    self.m_wer_list[mod].append(float(util.calculate_wer(ref.lower(),hyp.lower())))

		else:  
		    if hyp != []:

			cers=0.0
			wers=0.0
			maxi=0
		      
			target=[]
			for x in csv["tgt"]:
			    target.append(x)
			if isinstance(mod,New_NE):    
			    if csv["ne"]!=[]:
			        for ne in csv["ne"]:
			            target[ne]=u"ਊ"
			ref = " ".join(csv[aim]).replace("<com>","").strip().replace(u"<LINEBREAK>","").strip()
			for b in itertools.product(*[a[1] for a in hyp]):
			
			    maxi+=1
			    if maxi > 100:
			        break



			    c = util.calculate_cer(ref.lower()," ".join(x for x in b).lower())
			    w = util.calculate_wer(ref.lower()," ".join(x for x in b).lower())
			    if c > cers:
			        cers =c
			    if w > wers:
			        wers = w

	    

			    
			self.m_cer_list[mod].append(cers)
			self.m_wer_list[mod].append(wers)
		print "append cer done"
	    
		    #average CER and WER using dynamic alignment and WER based on the manual alignment, log it
	def write_cer_to_file(self):
		cer_log_file= codecs.open(util.LOG_DIR+"/"+self.eval_dir+"/cer_log","w","utf8")
		print self.m_cer_list
		print self.m_wer_list2

		cer_log_file.write("Character error rate per module\n\n\n")
		for elem in self.m_cer_list:
		    
		    cer_total=float(0.0)
		    for cer in self.m_cer_list[elem]:
			cer_total += float(cer) 
		    
		    cer_av = cer_total/float(len(self.m_cer_list[elem]))
		    cer_log_file.write(str(elem))
		    cer_log_file.write("\n")
		    cer_log_file.write(str(cer_av)+"\n\n\n")
	
		cer_log_file.write("Word error rate per module\n\n\n")

		for elem in self.m_wer_list:
		    
		    wer_total=float(0.0)
		    for wer in self.m_wer_list[elem]:
			wer_total += float(wer) 
		    
		    wer_av = wer_total/float(len(self.m_wer_list[elem]))
		    cer_log_file.write(str(elem))
		    cer_log_file.write("\n")
		    cer_log_file.write(str(wer_av)+"\n\n\n")
		    
		    
		cer_log_file.write("Word error rate per module 2\n\n\n")
		for el in self.m_wer_list2:
			if isinstance(el,Original):
				for mod in self.m_wer_list2:
					ins = self.m_wer_list2[el]["N"] - self.m_wer_list2[mod]["N"]
					self.m_wer_list2[mod]["N"] = self.m_wer_list2[el]["N"]
					self.m_wer_list2[mod]["I"] += ins
				break
		for e in self.m_wer_list2:
		    
		    wer_av = float((self.m_wer_list2[e]["D"]+self.m_wer_list2[e]["S"]+self.m_wer_list2[e]["I"] ))/float(self.m_wer_list2[e]["N"])
		    
		    cer_log_file.write("\n\n"+str(e))
		    cer_log_file.write("\n")
		    cer_log_file.write(str(wer_av)+"\n\n\n")
		    for w in self.m_wer_values[e]:
		    	cer_log_file.write(str(w)+",")

		cer_log_file.close()
		    
	def evaluate_overall(self,ori_sug_map):

		for num,el in enumerate(self.ori_tgt_map):
		    self.tokens_overall+=len(el[1].split())
		    
		    if el[0] in ori_sug_map:
			if el[1] in ori_sug_map[el[0]]:
			    self.tokens_found+=len(el[1].split())
			else:
			    self.not_found+=len(el[1].split())
		    else:
			self.not_found+=len(el[1].split())
		for el in ori_sug_map:
		    for sug in ori_sug_map[el]:
			self.suggestions_overall+=len(sug.split())
			
			
        def _log_sugg_per_module(self,original,al,ori,tgt,mod,lastItem):
        	self.m_wer_list2[mod]["N"]+=len(tgt.split())


		self.N+=len(tgt.split()) 
		if ori == tgt:
		    if tgt in al:
		        self.m_log_recall_precision[mod]["nothing_to_correct"]+=len(al[0].split())
		    elif tgt not in al:
		        self.m_log_recall_precision[mod]["over_correction"]+=len(al[0].split())
		        self.token_log[mod]["over_corrected"].append(original)
		        if len(al[0].split())<len(tgt.split()):
		            self.m_wer_list2[mod]["D"] +=len(tgt.split())-len(al[0].split())
		            self.D+=len(tgt.split())-len(al[0].split())
		            self.m_wer_list2[mod]["S"] +=len(al[0].split()) - len(set(tgt.split()) & set(al[0].split()))
		            self.S+=len(al[0].split()) - len(set(tgt.split()) & set(al[0].split()))
		        elif len(al[0].split())==len(tgt.split()):
		            self.m_wer_list2[mod]["S"] +=len(al[0].split()) - len(set(tgt.split()) & set(al[0].split()))
		            self.S+=len(al[0].split()) - len(set(tgt.split()) & set(al[0].split()))
		        elif len(al[0].split())>len(tgt.split()):
		            self.m_wer_list2[mod]["I"]+=len(al[0].split())-len(tgt.split())
		            self.I+=len(al[0].split())-len(tgt.split())
		            self.m_wer_list2[mod]["S"] +=(len(al[0].split()) - len(set(tgt.split()) & set(al[0].split())))-(len(al[0].split())-len(tgt.split()))
		            self.S+=(len(al[0].split()) - len(set(tgt.split()) & set(al[0].split())))-(len(al[0].split())-len(tgt.split()))
		elif tgt in al:
		    self.m_log_recall_precision[mod]["corrected"]+=len(al[0].split())
		    self.token_log[mod]["corrected"].append(original)
		else:
		    if len(al[0].split())<len(tgt.split()):
		        self.m_wer_list2[mod]["D"] +=len(tgt.split())-len(al[0].split())
		        self.D=+len(tgt.split())-len(al[0].split())
		        self.m_wer_list2[mod]["S"] +=len(al[0].split()) - len(set(tgt.split()) & set(al[0].split()))
		        self.S+= len(al[0].split()) - len(set(tgt.split()) & set(al[0].split()))
		    elif len(al[0].split())==len(tgt.split()):
		        self.m_wer_list2[mod]["S"] +=len(al[0].split()) - len(set(tgt.split()) & set(al[0].split()))
		        self.S+=  len(al[0].split()) - len(set(tgt.split()) & set(al[0].split()))  
		    elif len(al[0].split())>len(tgt.split()):
		        self.m_wer_list2[mod]["I"]+=len(al[0].split())-len(tgt.split())
		        self.I+=len(al[0].split())-len(tgt.split())
		        self.m_wer_list2[mod]["S"] +=(len(al[0].split()) - len(set(tgt.split()) & set(al[0].split())))-(len(al[0].split())-len(tgt.split()))
		        self.S+=(len(al[0].split()) - len(set(tgt.split()) & set(al[0].split())))-(len(al[0].split())-len(tgt.split()))
		    self.m_log_recall_precision[mod]["not_corrected"]+=len(ori.split())
		    self.token_log[mod]["not_found"].append(original)
		self.m_log_recall_precision[mod]["tokens_overall"]+=len(ori.split())

		self.m_log_recall_precision[mod]["num_sugg"]+=len(al[0].split())

		if lastItem:

		    self.I += float(self.N_tgt-self.N)
		    #this here is not solved yet
		    self.m_wer_values[mod].append(float(float(self.D+self.S+self.I)/float(20.014051522)))
		    self.D=0.0
		    self.S=0.0
		    self.I=0.0
		    self.N=0.0
	      
