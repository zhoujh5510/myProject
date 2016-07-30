from ltlparser.ast import Identifier, BoolNot, TraceStep, Trace, TraceStem, \
    TraceLoop
import re


def parse_multiple_ascii_traces(input):
    traces = re.split("\n\s*\n",input.strip())
    r = []
    for t in traces:
        tt = parse_ascii_trace(t)
        if len(tt) > 0:
            r.append(tt)
    return r


def parse_ascii_trace(input):
    """
    parses a graphical (ASCII) representation of a trace into a proper ltlparser.ast.Trace object, e.g. 
    
    a         _________XXXXXXXX | __________
    b         _________XXXXXXXX | _________X
    x         _________________ | __________
    
    is a valid input. At least one space is required between the signal name and the signal form, the 
    ``|'' symbol separates the stem from the loop (spaces may or may not be given around the ``|''). 
    _ is interpreted as False, any other character is interpreted as True. Of course, all signal waveforms
    must have the same length. Signals must be separated by newlines (\n).
    """
    lines = filter(lambda l: l.strip(), input.splitlines())
    vars = set()
    signals = {}
    stem_len = 0
    loop_len = 0
    for l in lines:
        l = re.split("#",l.strip())[0]
        v = re.split('\s+',l.strip())
        vars.add(v[0])
        s = re.split('\s*\|\s*', " ".join(v[1:]))
        signals[v[0]] = s
        if stem_len > 0 and stem_len != len(s[0]):
            raise Exception("Parse Error: different length of trace stem for signal %s" % v[0])
        elif loop_len > 0 and loop_len != len(s[1]):
            raise Exception("Parse Error: different length of trace loop for signal %s" % v[0])
        else:
            stem_len = len(s[0])
            loop_len = len(s[1])
    ids = dict(map(lambda v: (v,Identifier(v)), vars))
    trace_stem = []
    for i in xrange(stem_len):
        step = []
        for v in vars:
            if signals[v][0][i] == "_":
                step.append(BoolNot(ids[v]))
            else:
                step.append(ids[v])
        trace_stem.append(TraceStep(*step))
    trace_loop = []
    for i in xrange(loop_len):
        step = []
        for v in vars:
            if signals[v][1][i] == "_":
                step.append(BoolNot(ids[v]))
            else:
                step.append(ids[v])
        trace_loop.append(TraceStep(*step))
    return Trace(TraceStem(*trace_stem), TraceLoop(*trace_loop)) 
        
        
#test = """
#a         _________XXXXXXXX | __________
#b         _________XXXXXXXX | _________X
#x         _________________ | __________
#
#y         ______ | ____
#z         XXXXXX | XXXX
#"""
#print parse_multiple_ascii_traces(test)