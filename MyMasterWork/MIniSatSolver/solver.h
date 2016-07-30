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

typedef int                lit;         //定义一个类型 lit的类型也是int 
typedef char               lbool;       //lbool的类型也是char类型

#ifdef _WIN32
typedef signed __int64     uint64;
#else
typedef unsigned long long uint64;
#endif

static const int   var_Undef = -1;
static const lit   lit_Undef = -2;

static const lbool l_Undef   =  0;           //lbool的类型为char
static const lbool l_True    =  1;
static const lbool l_False   = -1;

static inline lit  toLit   (int v) { return v + v; }     
static inline lit  lit_neg (lit l) { return l ^ 1; }       //异或操作 相同为0 不同为1
static inline int  lit_var (lit l) { return l >> 1; }      //这里将一个整数右移一位是什么用意呢 除以2 达到将1转变为0 
//下面是进行位与运算，会将变量对应的每一位进行与运算
static inline int  lit_sign(lit l) { return (l & 1); }     //根据输入的变量的值返回一个状态 只有1才会返回1 其他的都返回0(小于10的数)


//=================================================================================================
// Public interface:

struct solver_t;
typedef struct solver_t solver;         

extern solver* solver_new(void);                           //新建一个solver实例对象的函数
extern void    solver_delete(solver* s);                   //删除一个solver实例函数

extern bool    solver_addclause(solver* s, lit* begin, lit* end);           //向solver中添加子句
extern bool    solver_simplify(solver* s);                                  //化简solver对象 其实就是化简其中的子句
extern bool   solver_solve(solver* s, lit* begin, lit* end);                //开始进行求解

extern int     solver_nvars(solver* s);                                      
extern int     solver_nclauses(solver* s);
extern int     solver_nconflicts(solver* s);                                //冲突

extern void    solver_setnvars(solver* s,int n);                           //设置n个变量的值


//利用结构体定义了一些状态
struct stats_t
{
    uint64   starts, decisions, propagations, inspects, conflicts;    //inspect 检查  propagation 传播 decision 决定
    uint64   clauses, clauses_literals, learnts, learnts_literals, max_literals, tot_literals;
};
typedef struct stats_t stats;

//=================================================================================================
// Solver representation:

struct clause_t;
typedef struct clause_t clause;

struct solver_t
{
    int      size;          // nof variables     变量的个数
    int      cap;           // size of varmaps   
    int      qhead;         // Head index of queue.
    int      qtail;         // Tail index of queue.

    // clauses
    vecp     clauses;       // List of problem constraints. (contains: clause*)  输入的约束列表
    vecp     learnts;       // List of learnt clauses. (contains: clause*)

    // activities
    double   var_inc;       // Amount to bump next variable with.
    double   var_decay;     // INVERSE decay factor for variable activity: stores 1/decay. 
    float    cla_inc;       // Amount to bump next clause with.
    float    cla_decay;     // INVERSE decay factor for clause activity: stores 1/decay.

    vecp*    wlists;        // 
    double*  activity;      // A heuristic measurement of the activity of a variable. 对于活动变量的启发式规则
    lbool*   assigns;       // Current values of variables. 当前变量的赋值情况
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

    int      root_level;    // Level of first proper decision. 适当的决策层
    int      simpdb_assigns;// Number of top-level assignments at last 'simplifyDB()'.
    int      simpdb_props;  // Number of propagations before next 'simplifyDB()'.
    double   random_seed;
    double   progress_estimate;
    int      verbosity;     // Verbosity level. 0=silent, 1=some progress report, 2=everything

    stats    stats;
};

#endif