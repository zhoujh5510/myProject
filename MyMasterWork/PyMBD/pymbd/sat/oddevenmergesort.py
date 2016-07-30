
class OddEvenMergeSortNetwork(object):
    def __init__(self, vars):
        self.vars = vars
        self.next_var = max(vars) + 1

    def oddevenmergesort(self, a):
        
        def make_and_clauses(res, a, b):
            return [[-res, a], [-res, b], [res, -a, -b]]
        
        def make_or_clauses(res, a, b):
            return [[res, -a], [res, -b], [-res, a, b]]
        
        def construct_block(i1, i2):
            in1, in2 = self.vars[i1], self.vars[i2]
            self.vars[i1] = self.next_var
            self.next_var += 1
            self.vars[i2] = self.next_var
            self.next_var += 1
            out1, out2 = self.vars[i1], self.vars[i2]
            return make_or_clauses (out1, in1, in2) + make_and_clauses(out2, in1, in2)
        
        def oddevenmerge(a):
            clauses = []
            if len(a) > 2:
                clauses += oddevenmerge(a[::2])
                clauses += oddevenmerge(a[1::2])
                for i in range(len(a))[1:len(a)-2:2]:
                    clauses += construct_block(a[i], a[i+1])
            else:
                clauses += construct_block(a[0], a[1])
            return clauses
        
        clauses = []
        if len(a) > 1:
            clauses += self.oddevenmergesort(a[:len(a)/2]) 
            clauses += self.oddevenmergesort(a[len(a)/2:]) 
            clauses += oddevenmerge(a)
        return clauses
    
###### ###### ###### ###### ###### ###### ###### ###### ###### ###### ######     

class CardinalityNetwork(object):
    def __init__(self, vars, next_var=None):
        self.vars = vars
        if next_var:
            self.next_var = next_var
        else:
            self.next_var = max(vars) + 1
        self.level = 0
    
#    def indent(self):
#        self.level += 1
#        
#    def outdent(self):
#        self.level -= 1
#        
#    def indstr(self):
#        return self.level * "|  " + "+- "
    
    def make_and_clauses(self, res, a, b):
#            return [[-res, a], [-res, b], [res, -a, -b]]
        return [[res, -a, -b]]
    
    def make_or_clauses(self, res, a, b):
#            return [[res, -a], [res, -b], [-res, a, b]]
        return [[res, -a], [res, -b]]
    
    def construct_block(self, i1, i2):
#        self.indent()
#        print self.indstr() + "comparing", i1, "and", i2
#        self.outdent()
        in1, in2 = self.vars[i1], self.vars[i2]
        self.vars[i1] = self.next_var
        self.next_var += 1
        self.vars[i2] = self.next_var
        self.next_var += 1
        out1, out2 = self.vars[i1], self.vars[i2]
        return self.make_or_clauses (out1, in1, in2) + self.make_and_clauses(out2, in1, in2)
    
    def smerge(self, a):
#        print self.indstr() + "smerge(%s)" % map(lambda x: x+1, a)
        clauses = []
        if len(a) > 2:
#            self.indent()
            clauses += self.smerge(a[::2])
            clauses += self.smerge(a[1::2])
#            self.outdent()
#                for i in range(len(a))[1:len(a)-2:2]:
            for i in range(len(a))[1:len(a)/2+1:2]:
                clauses += self.construct_block(a[i], a[i+1])
        else:
            clauses += self.construct_block(a[0], a[1])
        return clauses

    def hsort(self,a):
#        print self.indstr() + "hsort(%s)" % map(lambda x: x+1, a)
        clauses = []
        if len(a) > 1:
#            self.indent()
            clauses += self.hsort(a[:len(a)/2]) 
            clauses += self.hsort(a[len(a)/2:]) 
            clauses += self.smerge(a)
#            self.outdent()
        return clauses
    
    def card(self, a, k):
#        print self.indstr() + "card(%s, %d)" % (map(lambda x: x+1, a), k)
#        self.indent()
        clauses = []
        if len(a) == k:
            clauses =  self.hsort(a)
        else:
            clauses += self.card(a[:k], k)
            clauses += self.card(a[k:], k)
            clauses += self.smerge(a[:2*k])
#        self.outdent()
        return clauses
        
            
        
        
