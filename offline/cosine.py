import math

from pyStemmer import sStem
from pyUtilities import bIsStopWord,removePunctuation,stripExtraSpaces
import re

_documents = {}
_words = {}
_stem_mapping = {}

def add_document(title, text):
    text = _clean_text(text)
    for word in text.split():
        _words[word] = True
    _documents[title] = text

def clear():
    global _documents, _words, _stem_mapping
    _documents, _words, _stem_mapping = {}, {}, {}
        
def classify_document(target_text):
    ret = {}
    target_text = _clean_text(target_text)
    for title, text in _documents.items():
        calculated_similarity, keywords = _similarity(target_text, text)
        ret[title] = calculated_similarity, keywords
    return ret
    
def _clean_text(text):
    reNum = re.compile('\d+')
    text = ' '.join([w for w in text.split() if not bIsStopWord(w)])
    text = re.sub(reNum,' ',text)
    text = stripExtraSpaces(removePunctuation(text.lower()))

    text, mapping = sStem(text, return_word_mapping=True)
    for k, v in mapping.iteritems():
        if k in _stem_mapping.keys():
            _stem_mapping[k].extend(w for w in v if w not in _stem_mapping[k])
        else:
            _stem_mapping[k] = v
            
    return text
    
def _magnitude(model):
    ret = 0
    for count in model.values():
        ret += count * count
    ret = math.sqrt(ret)
    return ret
    
def _similarity(lhs, rhs):
    ret = 0.0
    keywords = []
    #lhs = _clean_text(lhs) # we are executing _clean_text twice for this text
    #rhs = _clean_text(rhs) # we are executing _clean_text twice for this text
    lhs_words, rhs_words = lhs.split(), rhs.split()
    lhs_model, rhs_model = {}, {}
    
    for word in lhs_words:
        lhs_model[word] = 1 + lhs_model.get(word, 0)
    for word in rhs_words:
        rhs_model[word] = 1 + rhs_model.get(word, 0)
      
    for word in _words:
        if word in lhs_model.keys() and word in rhs_model.keys():
            ret += lhs_model[word] * rhs_model[word]
            keywords.extend(_stem_mapping[word])
            
    if _magnitude(lhs_model) * _magnitude(rhs_model) > 0:
    	ret /= (_magnitude(lhs_model) * _magnitude(rhs_model))
    else:
        ret = 0

    return ret, keywords
        
if __name__ == '__main__':
    
    add_document('foo', 'dog cat mouse goat playing')
    print classify_document('cats parrot mouses play playing')

    #add_document('foo','Provider and insurer and regulation businesses reimbursement rates and methods for physicians, insurance companies, or specific procedures, peer review procedures, prospective system (PPS), appeals processes, rates for HMO services, regional adjustments, risk adjustment, reimbursement for chiropractors, foreign medical graduates, nurse practitioners, for outpatient services See also: 325 workforce training programs; 302 insurer or managed care consumer protections.')

    #add_document('bar', 'my name is bar')

    #print classify_document('To ensure that the fees that small businesses and other entities are charged for accepting debit cards are reasonable and proportional to the costs incurred, and to limit card networks from imposing anti-competitive restrictions on small businesses and other entities that accept cards.')

    #print classify_document('The companies physicians NATO statement did not list the nationality of the soldiers, but troops fighting in southern Afghanistan are predominantly American and British.')

    #print similarity2('my name is foo and yeah this works','my name is bar and yeah this works')
