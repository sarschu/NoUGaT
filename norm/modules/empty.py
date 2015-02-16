
import util
import logging
empty_log = logging.getLogger("norm.module.empty")

class Empty(object):
    '''
    Assuming that words can be superfluous, this module returns an empty string.
    '''


    def __init__(self,normalizer):
  	self.normalizer = normalizer
        super(Empty, self).__init__()

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
        empty_log.info("start empty module")
        words = sentence.split()
        results = []
        for word_ind,word in enumerate(words):
            if word_ind in corr_list:
                results.append([word,[""]])
            else:
                results.append([word,word])
        empty_log.debug(results)
        empty_log.info("finished empty module")
        return results
