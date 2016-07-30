/******************************************************************************************[Main.C]
MiniSat -- Copyright (c) 2003-2006, Niklas Een, Niklas Sorensson
CryptoMiniSat -- Copyright (c) 2009 Mate Soos
SCryptoMiniSat -- Copyright (c) 2012 Amit Metodi

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT
OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
**************************************************************************************************/

#include <ctime>
#include <cstring>
#include <errno.h>
#include <string.h>
#include <sstream>
#include <iostream>
#include <iomanip>
#include <vector>
#ifdef _MSC_VER
#include <msvc/stdint.h>
#else
#include <stdint.h>
#endif //_MSC_VER

#include <signal.h>

#include "Logger.h"
#include "Solver.h"
#include "time_mem.h"
#include "constants.h"




/*************************************************************************************/

Solver* solver = NULL;
FILE* mystdout = stdout;

uint32_t interestingVars = 0;
int solutionsBound = 0;
int printTime = 0;

static const int SOLVERERROR = -1;
static const int SOLVERTIMEOUT = 5;
static const int SOLVERKILL = 10;
static const int SOLVERUNDEF = 15;
static const int SOLVERUNSAT = 20;

static void printMsgWTime(const char* msg)
{
	if(printTime > 0)
		fprintf(mystdout,"%s <%.3f s>\n",msg,cpuTime());
	else 
		fprintf(mystdout,"%s\n",msg);
}

static void SIGINT_handler(int signum)
{
	printMsgWTime("TIMEOUT");
	fflush(mystdout);
    exit(SOLVERTIMEOUT);
}


//=================================================================================================
// Stream:

#define CHUNK_LIMIT 1024

class StreamBuffer
{
    FILE *  in;

    char    buf[CHUNK_LIMIT];
    int     pos;
	bool    foundEOF;
	
    void assureLookahead() {
        while(!foundEOF && buf[pos]==0) {
            pos  = 0;
			if(fgets(buf, sizeof(buf), in)==NULL)
				foundEOF=true;
        }
    }

public:
    StreamBuffer(FILE * i) : in(i), pos(0) {
        buf[0]=0;
		foundEOF=false;
		assureLookahead();
    }

    int  operator *  () {
        return foundEOF ? EOF : buf[pos];
    }
    void operator ++ () {
        pos++;
        assureLookahead();
    }
};


/*
#define CHUNK_LIMIT 1048576
class StreamBuffer
{
    FILE *  in;

    char    buf[CHUNK_LIMIT];
    int     pos;
    int     size;

	void assureLookahead() {
		if (pos >= size) {
			pos  = 0;
			size = fread(buf, 1, sizeof(buf), in);
		}
	}

public:
    StreamBuffer(FILE * i) : in(i), pos(0), size(0) {
        assureLookahead();
    }

    int  operator *  () {
        return (pos >= size) ? EOF : buf[pos];
    }
    void operator ++ () {
        pos++;
        assureLookahead();
    }
};
*/
//- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

template<class B>
static void skipWhitespace(B& in)
{
    while ((*in >= 9 && *in <= 13) || *in == 32)
        ++in;
}

template<class B>
static int parseInt(B& in)
{
    int     val = 0;
    bool    neg = false;
    skipWhitespace(in);
    if      (*in == '-') neg = true, ++in;
    else if (*in == '+') ++in;
    if (*in < '0' || *in > '9') {
		fprintf(mystdout,"ERROR! Parse unexpected char: %c\n", *in);
		fflush(mystdout);
		exit(SOLVERERROR);
	}
    while (*in >= '0' && *in <= '9')
        val = val*10 + (*in - '0'),
              ++in;
    return neg ? -val : val;
}

template<class B>
static void readClause(B& in, vec<Lit>& lits)
{
    int     parsed_lit;
    Var     var;
    lits.clear();
    for (;;) {
        parsed_lit = parseInt(in);
        if (parsed_lit == 0) break;
        var = abs(parsed_lit)-1;
		while (var >= solver->nVars()) solver->newVar();
        lits.push(Lit(var, (parsed_lit <= 0)));
    }
}

template<class B>
static void readNextWord(B& in, int bufSize, char* buf)
{
    skipWhitespace(in);
	int i=0;
	while(*in > 13 && *in != 32 && *in != EOF) {
		if(i==bufSize) {
			fprintf(mystdout,"ERROR! command is too long: %s...\n", buf) ;
			fflush(mystdout);
			exit(SOLVERERROR);
		}
		buf[i]=*in;
		++in;
		++i;
	}
	buf[i]=0;
}

template<class B>
static bool match(B& in, const char* str)
{
    for (; *str != 0; ++str, ++in)
        if (*str != *in)
            return false;
    return true;
}


template<class B>
static int addDimacsToSolver(B& in)
{
    vec<Lit> lits;
	bool xor_clause_inverted;
	for(;;) {
        skipWhitespace(in);
        switch (*in) {
        case EOF:
			return SOLVERERROR;
		case 'e':
            if (match(in, "end"))
				return 0;
			return SOLVERERROR;
			break;
		case 'x':
			++in;
			readClause(in, lits);
			xor_clause_inverted = false;
			for (uint32_t i = 0; i < lits.size(); i++)
				xor_clause_inverted ^= lits[i].sign();
			
			solver->addXorClause(lits, xor_clause_inverted);
			break;
		default:
			readClause(in, lits);
			solver->addClause(lits);
			break;
		}
	}
}

static void writeSolution(FILE* out) {
	printMsgWTime("SAT");
	if(interestingVars == 0) {
		for (Var var = 0; var != solver->nVars(); var++)
			if (solver->model[var] != l_Undef)
				fprintf(out, "%s%d ", (solver->model[var] == l_True)? "" : "-", var+1);
	} else
		for (Var var = 0; var != interestingVars; var++)
			if (solver->model[var] != l_Undef)
				fprintf(out, "%s%d ", (solver->model[var] == l_True)? "" : "-", var+1);
	fprintf(out,"0\n");
	fflush(out);
}

const char* hasPrefix(const char* str, const char* prefix)
{
    int len = strlen(prefix);
    if (strncmp(str, prefix, len) == 0)
        return str + len;
    else
        return NULL;
}

static bool minimizeUnary(vec<int>& minLits)
{
	int tmp_int;
	int vindx;
	vec<Lit> notLast;
	
	do {
		if(minLits.size()==0)
			return true;
		tmp_int = minLits.last();
		minLits.pop();
		vindx = abs(tmp_int)-1;

		 // add { not(tmp_int) } clause
		notLast.clear();
        notLast.push(Lit(vindx, (tmp_int > 0)));
		solver->addClause(notLast);

		if( ((solver->model[vindx] == l_True) && (tmp_int > 0)) ||
			((solver->model[vindx] == l_False) && (tmp_int < 0)) ||
			 (solver->model[vindx] == l_Undef))
			return false;
	} while(1);
}

/*
const void printClause(vec<Lit>& clause)
{
	for(int i=0; i<clause.size(); i++) {
		if(!clause[i].sign())
			printf("-");
		printf("%d ",clause[i].var());
	}
	printf("\n");
}
*/

static bool minimizeBinary(vec<int>& minLits)
{
	int tmp_int;
	int vindx;
	vec<Lit> notLast;

	// remove msb zeros
	do {
		if(minLits.size()==0) // all zeros
			return true;
		tmp_int = minLits.last();
		vindx = abs(tmp_int)-1;
		if( ((solver->model[vindx] == l_True) && (tmp_int > 0)) ||
			((solver->model[vindx] == l_False) && (tmp_int < 0)) ||
			 (solver->model[vindx] == l_Undef))
			 break;
		minLits.pop();
		notLast.clear();
        notLast.push(Lit(vindx, (tmp_int > 0))); // add to clause not(tmp_int)
		solver->addClause(notLast);
//		printClause(notLast);
	} while(1);

	// find last one bit (lsb will be one)
	int msb=minLits.size()-1;
	int lsb=0;
	while(lsb<msb) {
		tmp_int = minLits[lsb];
		vindx = abs(tmp_int)-1;
		// if lsb!=0 then break
		if( ((solver->model[vindx] == l_True) && (tmp_int > 0)) ||
			((solver->model[vindx] == l_False) && (tmp_int < 0)) ||
			 (solver->model[vindx] == l_Undef))
			 break;
		lsb++;
	}
	do { 
		notLast.clear();
		for(int i=minLits.size()-1; i>=msb; i--) {
			tmp_int = minLits[i];
			vindx = abs(tmp_int)-1;
			if( ((solver->model[vindx] == l_True) && (tmp_int < 0)) ||
				((solver->model[vindx] == l_False) && (tmp_int > 0))) { // is false
				notLast.push(Lit(vindx, (tmp_int <= 0))); // add to clause (tmp_int)
			} else { // is true
				notLast.push(Lit(vindx, (tmp_int > 0))); // add to clause not(tmp_int)
			}
		}
		while(msb>lsb) {
			msb--;
			tmp_int = minLits[msb];
			vindx = abs(tmp_int)-1;
			notLast.push(Lit(vindx, (tmp_int > 0))); // add to clause not(tmp_int)
			if( ((solver->model[vindx] == l_True) && (tmp_int < 0)) ||
				((solver->model[vindx] == l_False) && (tmp_int > 0))) 
					break;
		}
//		printClause(notLast);
		solver->addClause(notLast);
	} while(msb>lsb);
	return false;
}

template<class B>
static int solveMinimize(B& in, int representation)
{
	lbool ret;
	vec<int> minLits;
	
	do {
		int tmp_int = parseInt(in);
		if (tmp_int == 0) break;
		if (abs(tmp_int) > solver->nVars()) {
				fprintf(mystdout,"ERROR! unknown minimize literal : %d\n",tmp_int) ;
				fflush(mystdout);
				exit(SOLVERERROR);
		}
		minLits.push(tmp_int);
	} while(1);
	
	do {
		ret = solver->solve();
		if(ret == l_True) {
			writeSolution(mystdout);
			bool done=true;
			if(representation==1)
				done=minimizeUnary(minLits);
			else if(representation==2)
				done=minimizeBinary(minLits);
			// no else
			if(done)
				return SOLVERKILL;
		} else if(ret == l_False) {
			printMsgWTime("UNSAT");
			return SOLVERKILL;
		} else if(ret == l_Undef) {
			printMsgWTime("UNSAT ERROR!");
			return SOLVERUNDEF;
		}					
	} while(1);	
}

template<class B>
static int runLoop(B& in)
{
	const int BUF_SIZE = 30;
	char buf[BUF_SIZE+1];
	buf[BUF_SIZE]=0;
	do {
		readNextWord(in, BUF_SIZE, buf);
		if(strcmp(buf,"cnf")==0) {
			if(addDimacsToSolver(in)== -1) {
				fprintf(mystdout,"ERROR! reach EOF.\n");
				return SOLVERERROR;
			}
		} else if(strcmp(buf,"solve")==0) {
			lbool ret = solver->solve();
			if(ret == l_True)
				writeSolution(mystdout);
			else if(ret == l_False) {
				printMsgWTime("UNSAT");
				return SOLVERUNSAT;
			} else if(ret == l_Undef) {
				printMsgWTime("UNSAT ERROR!");
				return SOLVERUNDEF;
			}			
		} else if(strcmp(buf,"allsols")==0) {
			lbool ret;
			int solCnt=0;
			do {
				ret = solver->solve();
				if(ret == l_True) {
					solCnt++;
					writeSolution(mystdout);
					vec<Lit> lits;
					for (Var var = 0; var != solver->nVars() && (var != interestingVars || interestingVars==0); var++)
						if (solver->model[var] != l_Undef)
							lits.push( Lit(var, (solver->model[var] == l_True)? true : false) );
					solver->addClause(lits);
					if(solutionsBound==solCnt)
						break;
				} else if(ret == l_False) {
					if(solCnt==0) {
						printMsgWTime("UNSAT");
						return SOLVERUNSAT;
					} else 
						return SOLVERKILL;
				} else if(ret == l_Undef) {
					printMsgWTime("UNSAT ERROR!");
					return SOLVERUNDEF;
				}
			} while(1);
		} else if(strcmp(buf,"minimize")==0) {
			readNextWord(in, BUF_SIZE, buf);
			if(strcmp(buf,"unary")==0)
				return solveMinimize(in,1);
			else if(strcmp(buf,"binary")==0)
				return solveMinimize(in,2);
			else {
				fprintf(mystdout,"ERROR! unknown minimize representation : %s\n", buf) ;
				fflush(mystdout);
				exit(SOLVERERROR);
			}
		} else if(strcmp(buf,"limitsols")==0) {
			solutionsBound=parseInt(in);
		} else if(strcmp(buf,"output")==0) {
			int tmp=parseInt(in);
			interestingVars=(tmp > 0) ? tmp : 0;
			while (interestingVars > solver->nVars()) solver->newVar();
		} else if(strcmp(buf,"printcputime")==0) {
			printTime=parseInt(in);
		} else if(strcmp(buf,"kill")==0) {
			return SOLVERKILL;		
		} else if(buf[0]==0 && *in==EOF) {
			return SOLVERKILL;
		} else {
			fprintf(mystdout,"ERROR! unknown command : %s\n", buf) ;
			fflush(mystdout);
			exit(SOLVERERROR);
		}
	} while(true);
}

//=================================================================================================
// Main:

int main(int argc, char** argv)
{
    Solver      S;
    S.verbosity = 0;
	S.libraryUsage = false;
	
	const char* value;
	int j = 0;
	for (int i = 0; i < argc; i++) {
        if ((value = hasPrefix(argv[i], "--polarity-mode="))) {
            if (strcmp(value, "true") == 0)
                S.polarity_mode = Solver::polarity_true;
            else if (strcmp(value, "false") == 0)
                S.polarity_mode = Solver::polarity_false;
            else if (strcmp(value, "rnd") == 0)
                S.polarity_mode = Solver::polarity_rnd;
            else if (strcmp(value, "auto") == 0)
                S.polarity_mode = Solver::polarity_auto;
            else {
                printf("ERROR! unknown polarity-mode %s\n", value);
                exit(SOLVERERROR);
            }
        } else if ((value = hasPrefix(argv[i], "--rnd-freq="))) {
            double rnd;
            if (sscanf(value, "%lf", &rnd) <= 0 || rnd < 0 || rnd > 1) {
                printf("ERROR! illegal rnd-freq constant %s\n", value);
                exit(SOLVERERROR);
            }
            S.random_var_freq = rnd;
        } else if ((value = hasPrefix(argv[i], "--verbosity="))) {
            int verbosity = (int)strtol(value, NULL, 10);
            if (verbosity == EINVAL || verbosity == ERANGE) {
                printf("ERROR! illegal verbosity level %s\n", value);
                exit(SOLVERERROR);
            }
            S.verbosity = verbosity;
        } else if ((value = hasPrefix(argv[i], "--randomize="))) {
            uint32_t seed;
            if (sscanf(value, "%d", &seed) < 0) {
                printf("ERROR! illegal seed %s\n", value);
                exit(SOLVERERROR);
            }
//            cout << "c seed:" << seed << endl;
            S.setSeed(seed);
        } else if ((value = hasPrefix(argv[i], "--restrict="))) {
            uint branchTo;
            if (sscanf(value, "%d", &branchTo) < 0 || branchTo < 1) {
                printf("ERROR! illegal restricted pick branch number %d\n", branchTo);
                exit(SOLVERERROR);
            }
            S.restrictedPickBranch = branchTo;
        } else if ((value = hasPrefix(argv[i], "--gaussuntil="))) {
            uint32_t until;
            if (sscanf(value, "%d", &until) < 0) {
                printf("ERROR! until %s\n", value);
                exit(SOLVERERROR);
            }
            S.gaussconfig.decision_until = until;
        } else if ((value = hasPrefix(argv[i], "--restarts="))) {
            uint maxrest;
            if (sscanf(value, "%d", &maxrest) < 0 || maxrest == 0) {
                printf("ERROR! illegal maximum restart number %d\n", maxrest);
                exit(SOLVERERROR);
            }
            S.setMaxRestarts(maxrest);
        } else if ((value = hasPrefix(argv[i], "--greedyunbound"))) {
            S.greedyUnbound = true;
        } else if ((value = hasPrefix(argv[i], "--nonormxorfind"))) {
            S.findNormalXors = false;
        } else if ((value = hasPrefix(argv[i], "--nobinxorfind"))) {
            S.findBinaryXors = false;
        } else if ((value = hasPrefix(argv[i], "--noregbxorfind"))) {
            S.regularlyFindBinaryXors = false;
        } else if ((value = hasPrefix(argv[i], "--noconglomerate"))) {
            S.conglomerateXors = false;
        } else if ((value = hasPrefix(argv[i], "--nosimplify"))) {
            S.schedSimplification = false;
        } else if ((value = hasPrefix(argv[i], "--novarreplace"))) {
            S.performReplace = false;
        } else if ((value = hasPrefix(argv[i], "--nofailedvar"))) {
            S.failedVarSearch = false;
        } else if ((value = hasPrefix(argv[i], "--nodisablegauss"))) {
            S.gaussconfig.dontDisable = true;
        } else if ((value = hasPrefix(argv[i], "--noheuleprocess"))) {
            S.heuleProcess = false;
        } else if ((value = hasPrefix(argv[i], "--nosatelite"))) {
            S.doSubsumption = false;
        } else if ((value = hasPrefix(argv[i], "--noparthandler"))) {
            S.doPartHandler = false;
        } else if ((value = hasPrefix(argv[i], "--noxorsubs"))) {
            S.doXorSubsumption = false;
        } else if ((value = hasPrefix(argv[i], "--nohyperbinres"))) {
            S.doHyperBinRes = false;
        } else if ((value = hasPrefix(argv[i], "--noblockedclause"))) {
            S.doBlockedClause = false;
        } else if ((value = hasPrefix(argv[i], "--novarelim"))) {
            S.doVarElim = false;
        } else if ((value = hasPrefix(argv[i], "--nosubsume1"))) {
            S.doSubsume1 = false;
        } else if ((value = hasPrefix(argv[i], "--nomatrixfind"))) {
            S.gaussconfig.noMatrixFind = true;
        } else if ((value = hasPrefix(argv[i], "--noiterreduce"))) {
            S.gaussconfig.iterativeReduce = false;
        } else if ((value = hasPrefix(argv[i], "--noiterreduce"))) {
            S.gaussconfig.iterativeReduce = false;
        } else if ((value = hasPrefix(argv[i], "--noordercol"))) {
            S.gaussconfig.orderCols = false;
        } else if ((value = hasPrefix(argv[i], "--maxmatrixrows"))) {
            uint32_t rows;
            if (sscanf(value, "%d", &rows) < 0) {
                printf("ERROR! maxmatrixrows: %s\n", value);
                exit(SOLVERERROR);
            }
            S.gaussconfig.maxMatrixRows = rows;
        } else if ((value = hasPrefix(argv[i], "--minmatrixrows"))) {
            uint32_t rows;
            if (sscanf(value, "%d", &rows) < 0) {
                printf("ERROR! minmatrixrows: %s\n", value);
                exit(SOLVERERROR);
            }
            S.gaussconfig.minMatrixRows = rows;
        } else if ((value = hasPrefix(argv[i], "--savematrix"))) {
            uint32_t every;
            if (sscanf(value, "%d", &every) < 0) {
                printf("ERROR! savematrix: %s\n", value);
                exit(SOLVERERROR);
            }
            S.gaussconfig.only_nth_gauss_save = every;
        } else if ((value = hasPrefix(argv[i], "--restart="))) {
            if (strcmp(value, "auto") == 0)
                S.fixRestartType = auto_restart;
            else if (strcmp(value, "static") == 0)
                S.fixRestartType = static_restart;
            else if (strcmp(value, "dynamic") == 0)
                S.fixRestartType = dynamic_restart;
            else {
                printf("ERROR! unknown restart type %s\n", value);
                exit(SOLVERERROR);
            }
        } else if ((value = hasPrefix(argv[i], "--noextrabins"))) {
            S.addExtraBins = false;
        } else if ((value = hasPrefix(argv[i], "--noremovebins"))) {
            S.removeUselessBins = false;
        } else if ((value = hasPrefix(argv[i], "--noregremovebins"))) {
            S.regularRemoveUselessBins = false;
        } else if ((value = hasPrefix(argv[i], "--nosubswithbins"))) {
            S.subsumeWithNonExistBinaries = false;
        } else if ((value = hasPrefix(argv[i], "--norsubswithbins"))) {
            S.regularSubsumeWithNonExistBinaries = false;
        } else if (strncmp(argv[i], "-", 1) == 0 || strncmp(argv[i], "--", 2) == 0) {
            printf("ERROR! unknown flag %s\n", argv[i]);
            exit(SOLVERERROR);
        } else
            argv[j++] = argv[i];
    }
    argc = j;	
	
    FILE * inStream = (argc == 1) ? stdin : fopen(argv[1], "rb");
	if (inStream == NULL) {
		printf("ERROR! Could not open file: %s\n", argc == 1 ? "<stdin>" : argv[1]);
		exit(SOLVERERROR);
	}

	mystdout = (argc > 2) ? fopen(argv[2], "w") : stdout;
	if (mystdout == NULL) {
		printf("ERROR! Could not open file: %s\n", argc == 1 ? "<stdout>" : argv[2]);
		exit(SOLVERERROR);
    }
	
    solver = &S;
	signal(SIGINT,SIGINT_handler);
	signal(SIGTERM,SIGINT_handler);
	StreamBuffer in(inStream);
	int exitcode = runLoop(in);
	printMsgWTime("DONE");
	fflush(mystdout);

	exit(exitcode);
}
