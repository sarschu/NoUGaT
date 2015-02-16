'''
Created on May 19, 2014

@author: sarah
'''
from new_NE import New_NE

class Preclassifier(object):
    '''
    This module has been written by Arda Tezcan.
    It preclassifies tokens into "to normalize" or "dont touch"
    on the basis of trigrams in a corpus
    '''


    def __init__(self,normalizer):        
        super(Preclassifier, self).__init__()
        
        self.lm = normalizer.lm

        
        #Extract 2-grams from a list of 1-grams
    #Return a list of 2-grams
    def get_2grams(self,inputlist):
        list_2grams = []
        #if first word in line check sentence boundary before
        list_2grams.append('<s> '+inputlist[0])
        for i in range (0,len(inputlist)-1):
            list_2grams.append(inputlist[i]+' '+inputlist[i+1])
        #if last word in line check sentence boundary after
        list_2grams.append(inputlist[-1]+' </s>')
        return list_2grams
    
    
    #check if string (2-gram) exists in LM
    #Return "True" if it exists
    def check(self,inputstring, lm):
        if (inputstring in lm):
            return True
            
        return False
    
       
    def preclassify(self,sentence):
        new_entrylist = []
        to_correct=[]
        #Store tokens (1-grams) from the line as a list
        list_1grams = sentence.split()
        #Extract 2-grams from the token list
        list_2grams = self.get_2grams(list_1grams)
        for indexword, word in enumerate(list_1grams):
            #Create a new list for each word
            #First element in list is the word
            #Second and third elements are the binary values of the 2-grams including this word
            #2 2-grams cover each word (2-gram with the word before, 2-gram with the word after)
            new_entrylist.append(word)
            new_scorelist = []
            new_scorelist.append(word)
            for item_2gram in list_2grams[indexword:indexword+2]:
                score = self.check(item_2gram, self.lm)
                new_scorelist.append(score)
    
            new_entrylist[indexword] = new_scorelist
    
        print new_entrylist
        new_entry_dict={}
        for entry in new_entrylist:
            if True in entry[1:]:
                new_entry_dict[entry[0]]=False
            else:
                new_entry_dict[entry[0]]=True
    
        for indexword,entry in enumerate(new_entrylist):
            if (entry[1] == False and entry[2] == False):
                #print(entry)
                to_correct.append(indexword)
                    
        return new_entry_dict,to_correct
        
    def hard_filtering(self,n,t)
    	    cor_list=[]
    	    namedentity = New_NE(n)
            word_pre_list,cor_list = self.preclassify(t)
            if n.eval:
 		    n.e.m_log_recall_precision["preclass"]["num_sugg"]+=len(cor_list)
		    n.e.m_log_recall_precision["preclass"]["tokens_overall"]+=len(n.e.ori_tgt_map)

		    for el_num,el in enumerate(n.e.ori_tgt_map):
		        #overcorrection
		         
		        if el[0] == el[1] and el_num in cor_list:
		            n.e.token_log["preclass"]["over_corrected"].append(el[0])
		            n.e.m_log_recall_precision["preclass"]["over_correction"]+=1
		        elif el[0] == el[1] and el_num not in cor_list:
		            n.e.m_log_recall_precision["preclass"]["nothing_to_correct"]+=1
		        #correct    
		        if el[0] != el[1] and el_num in cor_list:
		            n.e.token_log["preclass"]["corrected"].append(el[0])
		            n.e.m_log_recall_precision["preclass"]["corrected"]+=1
		        
		        if el[0] != el[1] and el_num not in cor_list:
		            n.e.token_log["preclass"]["not_found"].append(el[0])
		            n.e.m_log_recall_precision["preclass"]["not_corrected"]+=1

            output_ne = namedentity.generate_alternatives(t,[])

            for num,el in enumerate(output_ne):
                if output_ne[num][1][0]==u"ਊ":

                    if num in corlist:
                        cor_list.remove(num)
           return.cor_list
           
    def soft_filtering(self,soft_list,phrase_dict,ori_sug_map):
        for element in ori_sug_map:
            if len(element.split())>1:
                to_corr=False
                for e in element.split():
                        if soft_list[e] ==True:
                            to_corr=True
                if to_corr==True:
                    for al in ori_sug_map[element]:
                        phrase_dict[al]["module"].append("PRE")
            else:
                if soft_list[element]==True:
                    for al in ori_sug_map[element]:
                        phrase_dict[al]["module"].append("PRE")
                        
        for alternative in phrase_dict.iteritems():
            if alternative[0]==u"ਊ" :
                for o in alternative[1]["ori"]:
                    if o in phrase_dict:
	                    phrase_dict[o]["module"].append("NE")
	                    
      return phrase_dict
           
