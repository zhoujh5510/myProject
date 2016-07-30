from pymbd.sat import yices, picosat, scryptominisat
from pymbd.sat.clause import Clause
from pymbd.sat.description import Sentence
from pymbd.sat.literal import Literal

class PushSentence(Sentence):
    pass
    
class PopSentence(Sentence):
    pass

class BlockingSentence(Sentence):
    
    def __init__(self, solution):
        self.solution = solution



yices.SENTENCE_INTERPRETERS[PushSentence] = lambda a, b, c: "(push)"
yices.SENTENCE_INTERPRETERS_CNF[PushSentence] = lambda a, b, c: "(push)"
picosat.SENTENCE_INTERPRETERS[PushSentence]  = lambda engine, pred, unused: []
scryptominisat.SENTENCE_INTERPRETERS[PushSentence]  = lambda engine, pred, unused: []
yices.SENTENCE_INTERPRETERS_DIMACS[PushSentence]  = lambda engine, pred, unused: []
yices.SENTENCE_INTERPRETERS_CN[PushSentence]  = lambda engine, pred, unused: []


yices.SENTENCE_INTERPRETERS[PopSentence] = lambda a, b, c: "(pop)"
yices.SENTENCE_INTERPRETERS_CNF[PopSentence] = lambda a, b, c: "(pop)"
picosat.SENTENCE_INTERPRETERS[PopSentence]  = lambda engine, pred, unused: []
scryptominisat.SENTENCE_INTERPRETERS[PopSentence]  = lambda engine, pred, unused: []
yices.SENTENCE_INTERPRETERS_DIMACS[PopSentence]  = lambda engine, pred, unused: []
yices.SENTENCE_INTERPRETERS_CN[PopSentence]  = lambda engine, pred, unused: []


def blocking_assertion(sentence):
    if len(sentence.solution) > 0:
        r = "(assert (or"
        for s in sentence.solution:
            r += (" (= ABx%s false)" % s)
        r += "))"
        return r
    else:
        return ""
    
def blocking_clause_cnf(sentence):
#    print sentence.solution
    return [Clause([Literal('ABx'+x, False) for x in sentence.solution])]

yices.SENTENCE_INTERPRETERS[BlockingSentence] = lambda engine, sentence, unused: blocking_assertion(sentence)
yices.SENTENCE_INTERPRETERS_CNF[BlockingSentence] = lambda engine, sentence, unused: blocking_assertion(sentence)
scryptominisat.SENTENCE_INTERPRETERS[BlockingSentence] = lambda engine, sentence, unused: blocking_clause_cnf(sentence)
yices.SENTENCE_INTERPRETERS_DIMACS[BlockingSentence] = lambda engine, sentence, unused: blocking_clause_cnf(sentence)
yices.SENTENCE_INTERPRETERS_CN[BlockingSentence] = lambda engine, sentence, unused: blocking_clause_cnf(sentence)
yices.SENTENCE_INTERPRETERS_CN_CNF[BlockingSentence] = lambda engine, sentence, unused: blocking_assertion(sentence)


