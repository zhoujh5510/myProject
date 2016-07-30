from glob import glob
from io import SEEK_SET, SEEK_END
from subprocess import Popen, PIPE, STDOUT
import time
import signal
import sys
import csv
import os

csv.register_dialect('table', delimiter='\t', quoting=csv.QUOTE_NONE, lineterminator='\n')
csv.field_size_limit(2**32)

class CSVObject(object):
    
    objects = []
    has_header = False
    
    def read(cls, file=None):
        file = cls.file if file is None else file
        if os.path.exists(file):
            cls.objects = []
            reader = csv.DictReader(open(file, 'r'), fieldnames=cls.fields, restkey="additional_data", restval=None, dialect='table')
            if cls.has_header:
                reader.next()
            for row in reader:
                for field in row:
                    if row[field] != None:
                        row[field] = cls.converters[cls.fields.index(field)](row[field])
                    # else:
                    #     row[field] = cls.converters[cls.fields.index(field)]()
                o = cls.__new__(cls)
                o.__init__(**row)
    read = classmethod(read)
    
    def save(cls, file=None):
        file = cls.file if file is None else file
        w = csv.DictWriter(open(file, 'w'), fieldnames=cls.fields, restval="null", extrasaction='ignore', dialect='table')
        w.writerows(map(lambda p: p.__dict__, cls.objects))
    save = classmethod(save)
    
    def __init__(self, **kwargs):
        self.__dict__ = kwargs
        self.__class__.objects.append(self)
        
    def get(cls, id):
        if id > len(cls.objects):
            raise "Problem with id %d does not exist in this file" % id
        return cls.objects[id-1]

    get = classmethod(get)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ",".join(map(lambda v: "%s=%s" % (v[0],v[1]), self.__dict__.iteritems())))
    
    def find(cls, finder):
        for o in cls.objects:
            if finder(o):
                return o
        return None    
    find = classmethod(find)
    
def write_sets(sets):
    """
    >>> write_sets(frozenset([frozenset([1, 2]), frozenset([3, 4])]))
    '1,2|3,4'
            
    >>> write_sets(frozenset([frozenset(['x2', 'x1']), frozenset(['x3'])]))
    'x2,x1|x3'
    
    >>> write_sets(frozenset([frozenset(['23gat', '24gat'])]))
    '23gat,24gat'
    """
    return "|".join(map(lambda cs: ",".join(map(lambda c: str(c), cs)), sets))

def read_sets(string):
    """
    >>> read_sets("1,2|3,4")
    frozenset([frozenset([1, 2]), frozenset([3, 4])])
            
    >>> read_sets('x1,x2|x3')
    frozenset([frozenset(['x2', 'x1']), frozenset(['x3'])])
    
    >>> read_sets('23gat,24gat')
    frozenset([frozenset(['23gat', '24gat'])])
    """
    return frozenset(map(lambda cs: frozenset(map(lambda c: int(c) if c.isdigit() else str(c), cs.split(","))), string.split("|")))

class Datafile(object):
    
    def __init__(self, filename, mode='read'):
        self.filename = filename
        if mode == "read":
            self.file = open(self.filename, 'r')
        elif mode == "append":
            self.file = open(self.filename, 'a')
        elif mode == "write":
            self.file = open(self.filename, 'w')
        self.curline = 1
        self.nextline = 1
        
    def getline(self, lineno):
        if lineno == self.nextline:
            self.nextline += 1
            return self.file.readline().strip()
        elif lineno > self.nextline:
            while self.nextline < lineno:
                self.nextline += 1
                self.file.readline()
            self.nextline += 1
            return self.file.readline().strip()
        elif lineno < self.nextline:
            print "\nWarning: Datafile position must be reset to beginning to get line!"
            self.nextline = 1
            self.file.seek(0)
            while self.nextline < lineno:
                self.nextline += 1
                self.file.readline()
            self.nextline += 1
            return self.file.readline().strip()
    
    def appendline(self, line):
        pos = self.file.tell()
        self.file.seek(0, SEEK_END)
        self.file.writelines([line + '\n'])
        self.file.seek(pos, SEEK_SET)

    def close(self):
        self.file.close()

def save_status(current_task=None):
    if current_task:
        with open("status.txt", 'w') as status_file:
            status_file.write(str(current_task.dict()))
    else:
        if os.path.exists('status.txt'):
            os.remove("status.txt")
        
def get_status():
    if os.path.exists("status.txt"):
        with open("status.txt", "r") as status_file:
            line = status_file.readline()
            if line:
                return eval(line)
            else:
                return dict()
    else:
        return dict()


def remove_results_with_warning(run_id, algorithms=None, dry_run=False):
    if algorithms is None:
    	files = glob('results-*.txt') + glob('output-*.txt')
    else:
        files = reduce(lambda l,f: l + [f[0]] + [f[1]], map(lambda a: ['results-%s.txt'%a,'output-%s.txt'%a],algorithms))
    files = filter(lambda x: os.path.exists(x), files)
    if files:
        print "Warning! Deleting the following files..."
        for f in files:
            print "  %s/%s" % (run_id, f)
        for _ in range(5):
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(1)
        for f in files:
            if os.path.exists(f) and not dry_run:
                os.remove(f)
        print


def formatted_values(*tpls):
    format, values = zip(*tpls)
    return " ".join(format) % values



class Timeout(Exception):
    pass


def alarm_handler(signum, frame):
    raise Timeout()

class timeout_monitor(object):

    def __init__(self, timeout, raise_exc=False):
        self.timeout = timeout
        self.raise_exc = raise_exc
        
    def __enter__(self):
        self.oldalarm = signal.alarm(0)
        self.oldhandler = signal.signal(signal.SIGALRM, alarm_handler)
        self.t0 = time.time()
        signal.alarm(self.timeout)
        
    def __exit__(self, type, value, traceback):
        signal.alarm(0)
        signal.signal(signal.SIGALRM, self.oldhandler)
        if self.oldalarm != 0:
            t1 = time.time()
            remaining = self.oldalarm - int(t1 - self.t0 + 0.5)
            if remaining <= 0:
                os.kill(os.getpid(), signal.SIGALRM)
            else:
                signal.alarm(remaining)
        return (not self.raise_exc and type == Timeout)    
