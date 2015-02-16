
import util
import logging
original_log = logging.getLogger("norm.module.original")
class Original(object):
    '''
    This class contains functions which return the original
    as an option
    '''

    def __init__(self,normalizer):
        self.normalizer = normalizer
        super(Original, self).__init__()
    
    def generate_alternatives(self,sentence,corr_list):
	'''
   	Generate suggestion

	**parameters**, **types**,**return**,**return types**::
		:param sentence: flooding corrected original message
		:type sentence: unicode string 
		:param corr_list: list containing all indices of the tokens that have to be normalized (hard filtering just some, otherwise all, no influence here)
		:type corr_list: list of integers
		:return: original tokens aligned with the suggestion of the form [[ori,[sug]],[ori2,[sug2]]]
		:rtype: list of lists
	
   	 '''
        original_log.info("start original module")
        sent_split = sentence.split()
        results = []
        for ori in sent_split:
            results.append([ori,[ori]])
        original_log.debug(results)
	original_log.debug("ORIGINAL CUT ME OUT "+sentence)
        original_log.info("finished original module")
        return results
    
