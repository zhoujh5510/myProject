#ifndef solver_h
#define solver_h

//#ifdef _WIN32
//#define inline __inline // compatible with MS VS 6.0
//#endif

#include "vec.h"

//=================================================================================================
// Simple types:

// does not work for c++
//typedef int  bool;
//static const bool  true      = 1;
//static const bool  false     = 0;

typedef int                lit;         //����һ������ lit������Ҳ��int 
typedef char               lbool;       //lbool������Ҳ��char����

#ifdef _WIN32
typedef signed __int64     uint64;
#else
typedef unsigned long long uint64;
#endif

static const int   var_Undef = -1;
static const lit   lit_Undef = -2;

static const lbool l_Undef   =  0;           //lbool������Ϊchar
static const lbool l_True    =  1;
static const lbool l_False   = -1;

static inline lit  toLit   (int v) { return v + v; }     
static inline lit  lit_neg (lit l) { return l ^ 1; }       //������ ��ͬΪ0 ��ͬΪ1
static inline int  lit_var (lit l) { return l >> 1; }      //���ｫһ����������һλ��ʲô������ ����2 �ﵽ��1ת��Ϊ0 
//�����ǽ���λ�����㣬�Ὣ������Ӧ��ÿһλ����������
static inline int  lit_sign(lit l) { return (l & 1); }     //��������ı�����ֵ����һ��״̬ ֻ��1�Ż᷵��1 �����Ķ�����0(С��10����)


//=================================================================================================
// Public interface:

struct solver_t;
typedef struct solver_t solver;         

extern solver* solver_new(void);                           //�½�һ��solverʵ������ĺ���
extern void    solver_delete(solver* s);                   //ɾ��һ��solverʵ������

extern bool    solver_addclause(solver* s, lit* begin, lit* end);           //��solver������Ӿ�
extern bool    solver_simplify(solver* s);                                  //����solver���� ��ʵ���ǻ������е��Ӿ�
extern bool   solver_solve(solver* s, lit* begin, lit* end);                //��ʼ�������

extern int     solver_nvars(solver* s);                                      
extern int     solver_nclauses(solver* s);
extern int     solver_nconflicts(solver* s);                                //��ͻ

extern void    solver_setnvars(solver* s,int n);                           //����n��������ֵ


//���ýṹ�嶨����һЩ״̬
struct stats_t
{
    uint64   starts, decisions, propagations, inspects, conflicts;    //inspect ���  propagation ���� decision ����
    uint64   clauses, clauses_literals, learnts, learnts_literals, max_literals, tot_literals;
};
typedef struct stats_t stats;

//=================================================================================================
// Solver representation:

struct clause_t;
typedef struct clause_t clause;

struct solver_t
{
    int      size;          // nof variables     �����ĸ���
    int      cap;           // size of varmaps   
    int      qhead;         // Head index of queue.
    int      qtail;         // Tail index of queue.

    // clauses
    vecp     clauses;       // List of problem constraints. (contains: clause*)  �����Լ���б�
    vecp     learnts;       // List of learnt clauses. (contains: clause*)

    // activities
    double   var_inc;       // Amount to bump next variable with.
    double   var_decay;     // INVERSE decay factor for variable activity: stores 1/decay. 
    float    cla_inc;       // Amount to bump next clause with.
    float    cla_decay;     // INVERSE decay factor for clause activity: stores 1/decay.

    vecp*    wlists;        // 
    double*  activity;      // A heuristic measurement of the activity of a variable. ���ڻ����������ʽ����
    lbool*   assigns;       // Current values of variables. ��ǰ�����ĸ�ֵ���
    int*     orderpos;      // Index in variable order.
    clause** reasons;       //
    int*     levels;        //
    lit*     trail;

    clause*  binary;        // A temporary binary clause
    lbool*   tags;          //
    veci     tagged;        // (contains: var)
    veci     stack;         // (contains: var)

    veci     order;         // Variable order. (heap) (contains: var)
    veci     trail_lim;     // Separator indices for different decision levels in 'trail'. (contains: int)
    veci     model;         // If problem is solved, this vector contains the model (contains: lbool).

    int      root_level;    // Level of first proper decision. �ʵ��ľ��߲�
    int      simpdb_assigns;// Number of top-level assignments at last 'simplifyDB()'.
    int      simpdb_props;  // Number of propagations before next 'simplifyDB()'.
    double   random_seed;
    double   progress_estimate;
    int      verbosity;     // Verbosity level. 0=silent, 1=some progress report, 2=everything

    stats    stats;
};

#endif