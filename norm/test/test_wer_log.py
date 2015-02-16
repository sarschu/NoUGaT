import sys
sys.path.insert(0, '/home/sarah/NoUGaT/norm/')
from normalizer import Normalizer as N
from data import Text

def test_function(d):
	n = N(language="nl",eval_dir="/home/sarah/NoUGaT/log/test")
	n._open_log_for_each_module()
	mod = n.modules[0]
	t = Text(d["ori"], n)

	n._log_sugg_per_module(d["ori"],d["alt"],d["ori"],d["tgt"],mod,False)

	return n.m_wer_list2[mod]


d = {"ori": u"studente", "alt": [u"stu dente"], "tgt": u"studente"}
assert test_function(d) == {'I': 1, 'S': 1, 'D': 0, 'N': 1}

#testen
