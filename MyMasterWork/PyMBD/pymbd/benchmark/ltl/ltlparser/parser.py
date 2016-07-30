import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'lib', 'dparser', 'python'))
from ast import Until, Identifier, BoolAnd, BoolOr, Spec, Next, \
    BoolNot, Finally, Globally, WeakUntil, Release, Implies, Equivalent, Trace, \
    TraceStem, TraceLoop, TraceStep, Constant, BoolXor, InstrumentationMode
from util.helper import flatten
import dparser
import os

"""
This is an LTL parser using DParser (a scannerless GLR parser based on the Tomita 
algorithm). The parser consists of methods starting with "d_" containing the production 
rules as the function docstring (e.g. d_spec function results in a symbol spec being 
available in the productions). Those methods are then compiled to a parser table 
by DParser upon loading the file (with some caches being maintained) and used by the 
Parser class or parse() method below. 

Due to the parser algorithm used, there is no need to remove left-recursive productions
and operator priorities are handled using those integer numbers on the right. 
The d_ methods are passed a (list of...) list of matched tokens during the parse 
process. Their return value should be result of a production rule after 
the parsing process, which can be any arbitrary object. For example 

def d_foobar(t):
    '''    expr     :    '(' expr ')'       '''
    return Foobar(t[1])
    
returns an object constructed from the second element of t (t[1]) thus omitting 
the left and right parentheses.
   
For the complete manual of DParser see http://dparser.sourceforge.net/d/manual.html.
Be aware that DParser distinguishes between single and double quotes in production rules.

Introducing a new foobar operator would work by just defining a new expr production, e.g. 

def d_foobar(t):
    '''    expr     :    expr 'foobar' expr     $left     400
    '''
    return Foobar(t[0], t[2])

"""

# ==================================================================================
#                           Basic Boolean and  LTL operators
# ==================================================================================


def no_str(input):
    return not isinstance(input, str)

def d_spec(t):
    '''     spec    :    formula ('.' formula)* '.'?
    '''
    return Spec(*filter(no_str, flatten(t)))

def d_identifier_or_constant(t):
    '''    identifier_or_constant      :    "[a-zA-Z0-9]+" instmode
    '''    #                     you need to use double quotes here!
    if t[0].lower() == "true" or t[0] == "1":
        return Constant("True", instmode=t[1])
    elif t[0].lower() == "false" or t[0] == "0":
        return Constant("False", instmode=t[1])
    else:
        return Identifier(t[0], instmode=t[1])

def d_identifier(t):
    '''    identifier      :    "[a-zA-Z0-9]+" instmode
    '''    #                     you need to use double quotes here!
    return Identifier(t[0], instmode=t[1])

def d_expr_id(t):
    '''    expr     :    identifier_or_constant
    '''
    return t[0]

def d_formula(t):
    '''    formula  :     expr
    '''
    return t[0]

def d_parenthised_expr(t):
    '''    expr     :    '(' expr ')'
    '''
    return t[1]

def d_bool_not(t):
    '''    expr     :    ('not'|'!'|'~') instmode expr           $right     2000
    '''
    return BoolNot(t[2], instmode=t[1])

def d_next(t):
    '''    expr     :    ('next'|'X') instmode expr           $right    2000
    '''
    return Next(t[2], instmode=t[1])

def d_bool_and(t):

    '''    expr     :    expr ('and'|'&&'|'*') instmode expr     $left     400
    '''
    return BoolAnd(t[0], t[3], instmode=t[2])

def d_bool_or(t):
    '''    expr     :    expr ('or'|'||'|'+') instmode expr      $left      350
    '''
    return BoolOr(t[0], t[3], instmode=t[2])

def d_bool_xor(t):
    '''    expr     :    expr ('xor'|'^') instmode expr        $left     450
    '''
    return BoolXor(t[0], t[3], instmode=t[2])

def d_until(t):
    '''    expr     :    expr ('until!'|'U') instmode expr   $left      850
    '''
    return Until(t[0], t[3], instmode=t[2])

def d_weak_until(t):
    '''    expr     :    expr ('until'|'W') instmode expr    $left      830
    '''
    return WeakUntil(t[0], t[3], instmode=t[2])

def d_release(t):
    '''    expr     :    expr ('release'|'R') instmode expr  $left      840
    '''
    return Release(t[0], t[3], instmode=t[2])  

def d_globally(t):
    '''    expr     :     ('globally'|'G') instmode expr      $unary_right      750
    '''
    return Globally(t[2], instmode=t[1])

def d_finally(t):
    '''    expr     :     ('finally'|'F') instmode expr       $unary_right      750
    '''
    return Finally(t[2], instmode=t[1])

#def d_finally(t):
#    '''    expr     :     'finally' expr        $unary_op_right      700
#    '''
#    return Finally(t[1])
#
#def d_finally_short(t):
#    '''    expr    :     'F' "[ \t\r\n]+" expr     $unary_op_right 700
#    '''
#    return Finally(t[2])
#
#def d_finally_globally(t):
#    '''    expr    :     'FG' expr        $unary_op_right 700
#    '''
#    return Finally(Globally(t[1]))

#def d_finally_short_parenthesized(t):
#    '''    expr    :     'F' '(' expr ')'        $unary_op_right 700
#    '''
##    print t
#    return Finally(t[2])

def d_implies(t):
    '''    expr     :     expr ('implies'|'->'|'=>') instmode expr $left      300
    '''
    return Implies(t[0], t[3], instmode=t[2])

def d_equivalent(t):
    '''    expr     :     expr ('equivalent'|'<->'|'<=>'|'=='|'=') instmode expr $left 250
    '''
    return Equivalent(t[0], t[3], instmode=t[2])

def d_assignment(t):
    '''    expr     :     expr '=' instmode expr $left 1200
    '''
    return Equivalent(t[0], t[3], instmode=t[2])

def d_instmode(t):
    '''    instmode    :    ('$'|'$$')?
    '''
    if t == [[["$"]]]:
        return InstrumentationMode.OmitNode
    elif t == [[["$$"]]]:
        return InstrumentationMode.OmitSubtree
    else:
        return InstrumentationMode.Instrument

# ==================================================================================
#                  Trace Specification using <a,b,c;d,e,f><g;i,h>
# ==================================================================================

def d_trace(t):
    '''    expr             :     trace'''
    return t[0]

def d_trace_parts(t):
    '''    trace            :     trace_stem trace_loop'''
    return Trace(t[0], t[1])

def d_trace_stem(t):
    '''    trace_stem       :     '<' trace_word? (';' trace_word)* '>'
    '''
    return TraceStem(*filter(no_str, flatten(t)))

def d_trace_loop(t):
    '''    trace_loop       :     '<' trace_word? (';' trace_word)* '>'
    '''
    return TraceLoop(*filter(no_str, flatten(t)))

def d_trace_word(t):
    '''    trace_word       :      trace_lit (',' trace_lit)*
    '''
    return TraceStep(*filter(no_str, flatten(t)))

def d_trace_lit(t):
    '''    trace_lit        :    trace_pos_lit | trace_neg_lit
    '''
    return t[0]

def d_trace_pos_lit(t):
    '''    trace_pos_lit    :     identifier
    '''
    return t[0]

def d_trace_neg_lit(t):
    '''    trace_neg_lit    :     '!' identifier
    '''
    return BoolNot(t[1]) 

# ==================================================================================
#                           Whitespace and Comment
#                 (taken from lib/dparser/tests/g50.test.g)
# ==================================================================================

def d_whitespace(t):
    '''     whitespace          : ( "[ \t\r\n]+" | singleline_comment | multiline_comment )*
    '''
    pass

def d_singleline_comment(t):
    '''    singleline_comment   : '%' "[^\n]*" '\n'
    '''
    pass

def d_multiline_comment(t):
    '''    multiline_comment    : '/*' ( "[^*]" | '*'+ "[^*\/]" )* '*'+ '/'
    '''
    pass

# ==================================================================================
# ==================================================================================

class Parser(object):
    def parse(self, input, **args):
        try:
            opts = {'parser_folder':os.path.dirname(os.path.abspath(__file__))}
            r = dparser.Parser(**opts).parse(input, **args).getStructure()
            if len(r.children) == 1:
                return r.children[0] # don't return spec object in this case
            else:
                return r
        except dparser.SyntaxError:
            raise Exception("Syntax error while parsing input >>%s<<" % input)

def parse(input):
    return Parser().parse(input)

#r = Parser().parse(""" 
#a and b % and c.
#/*
#% x and y
#f or g
#*/
#<a><b>
#c or d.""")
#write_pdf(dotTree(r), 'pyast.pdf')