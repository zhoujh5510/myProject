from ..ltlparser.ast import TraceStep, BoolNot, Node, Type, TraceStem, TraceLoop

class Trace(object):

    __slots__ = ['k', 'l', 'signals', 'values', 'vars']

    def __init__(self):
        self.k = 0
        self.l = 0
        self.signals = []
        ''' list of syntrax tree nodes corresponding to the elements in self.values '''
        
        self.values  = []
        ''' list of [True,False,...] lists specificying the signals' values '''
        
        self.vars    = []
        ''' list of indices of those signals representing variables '''
        
    def to_trace_formula(self):
        stem = []
        for t in range(0,self.l):
            step = []
            for i in self.vars:
                if self.values[i][t] == True:
                    step += [self.signals[i]]
                else:
                    step += [BoolNot(self.signals[i])]
            stem += [TraceStep(*step)]
        loop = []
        for t in range(self.l,self.k+1):
            step = []
            for i in self.vars:
                if self.values[i][t] == True:
                    step += [self.signals[i]]
                else:
                    step += [BoolNot(self.signals[i])]
            loop += [TraceStep(*step)]
        return Node(Type.Trace,TraceStem(*stem),TraceLoop(*loop))
            
            
            
    
    def pretty_print(self, vars_only=False, order=None):
        '''
        vars_only: only print the signals of variables (True/False) 
        order: if not none, determines the print order (list of strings representing the variables, e.g. ['a', 'b', 'c']) 
               (only useful together with vars_only=True)
        '''
        import sys
        consider = list(enumerate(self.signals))
        if vars_only:
            consider = [s for i,s in enumerate(self.signals) if i in self.vars]
        if len(consider) == 0:
            return
        f_width = max(map(len,map(lambda s: str(s[1]),consider)))
        print 
        print (f_width+self.k+7) * "=",
        if order:
            consider = sorted(enumerate(consider),key=lambda s: order.index(str(s[1])))
        for i,f in consider:
            print
            print str(f).ljust(f_width) + "   ",  
            for j in range(self.k+1):
                if j == self.l:
                    print "| ", 
                sys.stdout.write("X" if self.values[i][j] else "_") 
        print
        print (f_width+self.k+7) * "="
