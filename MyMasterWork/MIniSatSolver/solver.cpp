#include <stdio.h>
#include <assert.h>
#include <math.h>

#include "solver.h"
#include <fstream>
#include <iostream>

//=================================================================================================
// Debug:
//自定义宏
#define dev  
  using namespace std;

//#define VERBOSEDEBUG

// For derivation output (verbosity level 2)
#define L_IND    "%-*d"
//solver_dlevel返回的是求解器当前的决策层数
#define L_ind    solver_dlevel(s)*3+3,solver_dlevel(s)
//下面的两个宏定义就是输出文字
#define L_LIT    "%sx%d"
//下面的lit_sign函数是对输入的文字与1进行&操作 当输入的文字为正文字 则返回0 负文字则返回1
#define L_lit(p) lit_sign(p)?"~":"", (lit_var(p))   //如果lit_sign(p)的值是1 表明p是负文字 需要加一个非符号

// Just like 'assert()' but expression will be evaluated in the release version as well.
//检查expr是否为1
static inline void check(int expr) { assert(expr); }



//自己写的函数 将冲突子句输出到文本文件中
void outConflict(lit* begin,lit* end)
{
	FILE *out;
	int i ;
	assert((end - begin) > 0);
	if((out = fopen("E:\\conflict.txt","at+")) == NULL)
	{
		printf("cannot open file conflict.txt!");
	}
	else
	{
		for(i = 0 ; i < end - begin ; i++)
		{
		    if(lit_sign(begin[i]))
		      {
				  fprintf(out,"%cx%d ",'-',lit_var(begin[i]));
		      }
		     else
		     {
				 fprintf(out,"x%d ",lit_var(begin[i]));
		      }
		}
		fputc('\n',out);
	}
	fclose(out);
}


//输出文字 函数
//给出头指针和尾指针 输出文字
static void printlits(lit* begin, lit* end)
{
#ifdef dev
	fstream cout("E:\\out.txt",ios::app);  //重定向输出流 将其定向到输出的文件
#endif
	int i;
	for (i = 0; i < end - begin; i++)
	{
		printf(L_LIT" ", L_lit(begin[i]));    //根据文字的正负输出其相应的标志
        if(lit_sign(begin[i]))
		{
			cout<<"~x";
			cout<<lit_var(begin[i]);
			cout<<" ";
		}else{
		    cout<<"x";
			cout<<lit_var(begin[i]);
			cout<<" ";
		}
	}
	cout<<endl;
}

//=================================================================================================
// Random numbers:


// Returns a random float 0 <= x < 1. Seed must never be 0.
static inline double drand(double* seed) {
	int q;
	*seed *= 1389796;
	q = (int)(*seed / 2147483647);
	*seed -= (double)q * 2147483647;
	return *seed / 2147483647;
}


// Returns a random integer 0 <= x < size. Seed must never be 0.
static inline int irand(double* seed, int size) {
	return (int)(drand(seed) * size);
}              //这里的drand函数式随机的产生0到1之间的值函数


//=================================================================================================
// Predeclarations:

void sort(void** array, int size, int(*comp)(const void *, const void *));

//=================================================================================================
// Clause datatype + minor functions:

struct clause_t
{
	int size_learnt;
	//下面的这个数组应该是还没有申请空间的数组,等到需要的时候才会去申请相应的空间
	lit lits[0];                
};


//下面的这几个函数我实在是需要时间去熟悉弄懂
static inline int   clause_size(clause* c)          { return c->size_learnt >> 1; }
static inline lit*  clause_begin(clause* c)          { return c->lits; }      //返回子句c中的文字
static inline int   clause_learnt(clause* c)          { return c->size_learnt & 1; }
static inline float clause_activity(clause* c)          { return *((float*)&c->lits[c->size_learnt >> 1]);}
static inline void  clause_setactivity(clause* c, float a) { *((float*)&c->lits[c->size_learnt >> 1]) = a; }

//=================================================================================================
// Encode literals in clause pointers:  重新将clause中的元素进行编码 再表示

//从子句的指针中读出一个子句
clause* clause_from_lit(lit l)     { return (clause*)((unsigned long)l + (unsigned long)l + 1); }
//判断一个子句中的文字么？我不太懂这个函数的目的是什么？
bool    clause_is_lit(clause* c) { /*printf("%d\n",(unsigned long)c & 1);*/   return ((unsigned long)c & 1); }
//从一个子句中读出相应的文字
lit     clause_read_lit(clause* c) { /*printf("%d\n",((unsigned long)c >> 1));*/ return (lit)((unsigned long)c >> 1); }    //读取文字的时候右移一位

//=================================================================================================
// Simple helpers:

//下面的这个函数的功能其实就是返回solver 对象中s的一个属性s->trail的长度
//其实该函数的功能也就是返回求解器现在正在的决策层数
static inline int     solver_dlevel(solver* s)    { return veci_size(&s->trail_lim); }   //这里的s->trail是一个veci类型的变量
static inline vecp*   solver_read_wlist(solver* s, lit l){ return &s->wlists[l]; }  //s->wlist是一个vecp类型的指针 返回的是子句集合中的与l相关的子句
static inline void    vecp_remove(vecp* v, void* e)   //void类型的指针意味着该类型的指针可以指向其他任意类型的指针
{
	void** ws = vecp_begin(v);
	int    j = 0;

	for (; ws[j] != e; j++);
	assert(j < vecp_size(v));                                 //保证每个子句中都有元素

	//在这里vecp是二重指针 它指向的每个元素都是一个veci 所以删除一个vecp元素 其实就相当于删除了一个子句
	for (; j < vecp_size(v) - 1; j++) ws[j] = ws[j + 1];     //通过依次向前移动一个元素达到将e这个子句删除的目的
	vecp_resize(v, vecp_size(v) - 1);         //更新删除后的vecp类型v的大小
}

//=================================================================================================
// Variable order functions:
//根据输入的文字v 将其下面的文字根据排序
static inline void order_update(solver* s, int v) // updateorder  
{
	int*    orderpos = s->orderpos;           //指向动态变量的列表的头指针
	//这里的activity是每个变量的活动性的值 在选择变量进行赋值后约束传播的过程中 程序会选择活动性值高的变量
	double* activity = s->activity;           
	int*    heap = veci_begin(&s->order);    //order是一个veci类型的变量
	int     i = orderpos[v];              //指向顺序序列的第v个元素
	int     x = heap[i];              //找到veci中的要指向的元素
	int     parent = (i - 1) / 2;          //找到i节点元素的父节点

	assert(s->orderpos[v] != -1);             //保证在orde序列中的文字v存在活动状态

	//将变量按照活动性高低进行排序 降序排序
	while (i != 0 && activity[x] > activity[heap[parent]]){
		heap[i] = heap[parent];
		orderpos[heap[i]] = i;
		i = parent;
		parent = (i - 1) / 2;
	}
	heap[i] = x;
	orderpos[x] = i;
}


static inline void order_assigned(solver* s, int v)      //对序列中的元素进行赋值 
{
}


//对序列中的元素撤销赋值
static inline void order_unassigned(solver* s, int v) // undoorder    
{
	//order是根据文字的活动性得到的文字的优先级队列
	//orderpos是指向优先级队列的头指针
	int* orderpos = s->orderpos;                   //orderpos 是没有赋值的变量序列的头指针
	if (orderpos[v] == -1){                        
		orderpos[v] = veci_size(&s->order);
		veci_push(&s->order, v);
		order_update(s, v);
	}
}

//函数去选择一个新的 没有赋值的变量
//将根据random_var_freq的值选择使使用随机策略还是使用VSID策略
static int  order_select(solver* s, float random_var_freq) // selectvar   随机的选择变量
{
	int*    heap;
	double* activity;
	int*    orderpos;

	lbool* values = s->assigns;                 //lbool是char类型 当前赋值队列给values

	// Random decision:   随机策略就是随机的选择一个变量进行赋值
	//random_seed在新建一个solver对象的时候会被初始化 d_rand返回的是0到1之间的一个float值
	if (drand(&s->random_seed) < random_var_freq){
		int next = irand(&s->random_seed, s->size);     //i_random返回的是0到s->size之间的一个值 但是绝不可能为0
		assert(next >= 0 && next < s->size);           //确保next的值在0到s->szie之间
		if (values[next] == l_Undef)                   //如果值为0的情况 还没有进行赋值的时候
			return next;                   //返回next 意味着可以选择该变量进行赋值
	}

	// Activity based decision: 基于活动性的策略 跟VSID这种策略差不多

	heap = veci_begin(&s->order);       //获得具有活动性文字队列的第一个元素 
	activity = s->activity;                 //这个应该是一个指针 指向变量的活动性的一个一维数组上
	orderpos = s->orderpos;


	while (veci_size(&s->order) > 0){   //当solver对象s中的活动性队列中还存在文字的时候
		int    next = heap[0];         //next指向第一个元素
		int    size = veci_size(&s->order) - 1;
		int    x = heap[size];                  //x指向最后的一个元素

		veci_resize(&s->order, size);

		orderpos[next] = -1;

		if (size > 0){
			double act = activity[x];   //得到最后的一个元素的活动性值

			int    i = 0;
			int    child = 1;

			//下面的几行代码 找到活动性最大的变量
			while (child < size){				if (child + 1 < size && activity[heap[child]] < activity[heap[child + 1]])
					child++;

				assert(child < size);     //保证child增长 但是不能大于变量的个数

				if (act >= activity[heap[child]])
					break;                            //找到具有最大活动性的变量 则跳出while循环

				heap[i] = heap[child];
				orderpos[heap[i]] = i;
				i = child;
				child = 2 * child + 1;
			}
			heap[i] = x;
			orderpos[heap[i]] = i;
		}

		if (values[next] == l_Undef)         //1_undef的值为0 0表示的是还没有进行赋值 已经赋值为true则为1 赋值为false则为-1
			return next;   //如果next还没有赋值 那么可以选择这个变量进行赋值
	}

	return var_Undef;               //如果没有赋值成功 则返回-1 即变量还未赋值
}

//=================================================================================================
// Activity functions:
//重新调节变量的活动性 
//var_inc： Amount to bump next clause with
static inline void act_var_rescale(solver* s) {
	double* activity = s->activity;
	int i;
	for (i = 0; i < s->size; i++)
		activity[i] *= 1e-100;              //将变量的activity的值乘以1e-100   将文字的活动性都降低了
	s->var_inc *= 1e-100;                   //这个var_inc是solver对象s的一个属性 用于调节activity用的 
}

//bump取消   
static inline void act_var_bump(solver* s, int v) {
	double* activity = s->activity;
	if ((activity[v] += s->var_inc) > 1e100)
		act_var_rescale(s);                    //调节变量的活动性

	//printf("bump %d %f\n", v-1, activity[v]);

	if (s->orderpos[v] != -1)
		order_update(s, v);           //如果变量还没有赋值 则将变量加入活动性排序        

}

//将求解器整体的文字的活动性缩减
static inline void act_var_decay(solver* s) { s->var_inc *= s->var_decay; }


//重新调节子句集合  在MiniSat中子句也相应的具有活动性
static inline void act_clause_rescale(solver* s) {
	clause** cs = (clause**)vecp_begin(&s->learnts);     //这里的learnts是vecp类型 是学习子句的集合
	int i;
	for (i = 0; i < vecp_size(&s->learnts); i++){
		float a = clause_activity(cs[i]);                //调用clause_activity函数得到子句的活动性 赋值给float
		clause_setactivity(cs[i], a * (float)1e-20);     //设置子句的活动性
	}
	s->cla_inc *= (float)1e-20;
}

//bump 取消的意思 那么在这里我可以猜测该函数的功能是取消子句的活动性
//根据活动性将子句从原始的子句集合中删除  其实就是取消子句的活动性
static inline void act_clause_bump(solver* s, clause *c) {
	float a = clause_activity(c) + s->cla_inc;         //得到子句c的活动性值并加上一个cla_inc
	clause_setactivity(c, a);                          //重新设置子句c的活动性
	if (a > 1e20) act_clause_rescale(s);               
}

//我觉得在这里inc是increase的简写 是增量的意思
static inline void act_clause_decay(solver* s) { s->cla_inc *= s->cla_decay; }   //decay 衰退 衰减


//=================================================================================================
// Clause functions:

/* pre: size > 1 && no variable occurs twice
*/
/*新建一个子句 在一个子句中同一个变量不可能出现两次 
**而且子句的长度我觉得必须大于1  因为在一个子句中必须用0作为结尾
*/
/*
constructor function for clauses. return false if top-level conflict is detected 
clause c maybe set to NULL if the new clause is satisfied under the current top-level assignment
learnt是标志位 如果为0 表明是加入的原始子句 如果为1的话表明加入的是学习子句
*/
static clause* clause_new(solver* s, lit* begin, lit* end, int learnt)
{
	int size;                      //要加入到子句中的变量的个数
	clause* c;
	int i;

	assert(end - begin > 1);               //保证存在变量要加入到子句中
	assert(learnt >= 0 && learnt < 2);     //learnt只有0和1两个值 原始子句和学习子句的标志位 
	size = end - begin;                    //要加入的子句的大小               
	c = (clause*)malloc(sizeof(clause)+sizeof(lit)* size + learnt * sizeof(float));   //给子句c分配空间
	c->size_learnt = (size << 1) | learnt;    //子句的大小 被向左移了一位             
	assert(((unsigned int)c & 1) == 0);

	for (i = 0; i < size; i++)
		c->lits[i] = begin[i];                        //将所有的变量都加入到子句中去

	if (learnt)    //learnt是原始子句和学习子句的标志位 0为原始子句 1为学习子句
		*((float*)&c->lits[size]) = 0.0;   //如果是学习子句 将子句的最后一个文字赋值为0

	//因为在MiniSat中采用的是watch literals的策略 所以着重考虑的是刚开始的文字

	assert(begin[0] >= 0);
	assert(begin[0] < s->size * 2);
	assert(begin[1] >= 0);
	assert(begin[1] < s->size * 2);

	assert(lit_neg(begin[0]) < s->size * 2);
	assert(lit_neg(begin[1]) < s->size * 2);

	//vecp_push(solver_read_wlist(s,lit_neg(begin[0])),(void*)c);
	//vecp_push(solver_read_wlist(s,lit_neg(begin[1])),(void*)c);

	//solver_read_wlist返回的是wlist中的某一个子句  看变量的个数是否大于2个
	//读出与第一个文字相关的子句 并将其加入到vecp*的队列中去考虑 并将与第二个文字相关的子句加入到第一个末尾
	//lit_neg是对输入的文字进行异或操作 相同为0 不同为1 表明是返回与输入相反的值
	//将与文字相关的子句加入到观察队列的子句集合中去
	
	vecp_push(solver_read_wlist(s, lit_neg(begin[0])), (void*)(size > 2 ? c : clause_from_lit(begin[1])));
	vecp_push(solver_read_wlist(s, lit_neg(begin[1])), (void*)(size > 2 ? c : clause_from_lit(begin[0])));

	return c;
}


//将子句集合中的子句移走
//调用vecp的remove函数将给定的子句从子句集合中删除掉
static void clause_remove(solver* s, clause* c)
{
	lit* lits = clause_begin(c);     //返回的是子句集合的头指针
	assert(lit_neg(lits[0]) < s->size * 2);
	assert(lit_neg(lits[1]) < s->size * 2);

	//vecp_remove(solver_read_wlist(s,lit_neg(lits[0])),(void*)c);
	//vecp_remove(solver_read_wlist(s,lit_neg(lits[1])),(void*)c);

	assert(lits[0] < s->size * 2);
	//vecp_remove函数的功能好像是将子句集合中的跟输入的参数相等的子句删除
	//将与观察的文字相关的在观察队列中的子句也一块从子句集合中移除
	vecp_remove(solver_read_wlist(s, lit_neg(lits[0])), (void*)(clause_size(c) > 2 ? c : clause_from_lit(lits[1])));
	vecp_remove(solver_read_wlist(s, lit_neg(lits[1])), (void*)(clause_size(c) > 2 ? c : clause_from_lit(lits[0])));

	if (clause_learnt(c)){
		s->stats.learnts--;     //如果删除的是学习子句 那么相应的学习子句的长度需要减一
		s->stats.learnts_literals -= clause_size(c);     //学习子句中变量的个数减去学习子句的长度那么多个
	}
	else{
		s->stats.clauses--;        //如果是一般的子句 那么子句集合中子句的个数减一 
		s->stats.clauses_literals -= clause_size(c);     //对应的 子句的变量的个数也需要对应减掉那么多
	}

	free(c);                     //释放移走的子句的空间
}


//下面的函数是将子句进行简化的过程
//在top_level层调用的函数 化简子句集合 根据当前的赋值情况判断输入的子句c的可满足性
static lbool clause_simplify(solver* s, clause* c)
{
	lit*   lits = clause_begin(c);   //lit指向子句c开始的元素
	lbool* values = s->assigns;      //assigns这个指针是指向已经赋值的变量
	int i;

	assert(solver_dlevel(s) == 0);  //需要保证在top_level层才化简子句集合

	for (i = 0; i < clause_size(c); i++){
		//经过lit_sign()函数的处理 输入的参数lits[i]的值变成了1或者-1 
		//下面的这一句代码得到已经赋值的文字的赋值 在本函数中根据其赋值判断子句是否可满足的
		lbool sig = !lit_sign(lits[i]); sig += sig - 1;      //lbool为char类型 
		if (values[lit_var(lits[i])] == sig)
			return l_True;
	}
	return l_False;
}

//=================================================================================================
// Minor (solver) functions:
//下面是solver的一些函数


//在求解器中创建新的的变量
void solver_setnvars(solver* s, int n)               //根据输入 设置n个变量的值
{
	int var;

	if (s->cap < n){

		while (s->cap < n) s->cap = s->cap * 2 + 1;          //申请大于n那么多的空间

		//都是根据变量的多少 为solver对象s申请相应大小的空间
		s->wlists = (vecp*)realloc(s->wlists, sizeof(vecp)*s->cap * 2);      //wlist是vecp类型 指的是watch literals么？
		s->activity = (double*)realloc(s->activity, sizeof(double)*s->cap);
		s->assigns = (lbool*)realloc(s->assigns, sizeof(lbool)*s->cap);
		s->orderpos = (int*)realloc(s->orderpos, sizeof(int)*s->cap);
		s->reasons = (clause**)realloc(s->reasons, sizeof(clause*)*s->cap);
		s->levels = (int*)realloc(s->levels, sizeof(int)*s->cap);
		s->tags = (lbool*)realloc(s->tags, sizeof(lbool)*s->cap);
		s->trail = (lit*)realloc(s->trail, sizeof(lit)*s->cap);
	}

	for (var = s->size; var < n; var++){       //对于大于solver对象s实际长度的变量的处理
		vecp_new(&s->wlists[2 * var]);
		vecp_new(&s->wlists[2 * var + 1]);
		s->activity[var] = 0;                    //设置其活动性为0
		s->assigns[var] = l_Undef;               //设置变量还没有复赋值
		s->orderpos[var] = veci_size(&s->order);
		s->reasons[var] = (clause*)0;
		s->levels[var] = 0;
		s->tags[var] = l_Undef;

		/* does not hold because variables enqueued at top level will not be reinserted in the heap
		assert(veci_size(&s->order) == var);
		*/
		veci_push(&s->order, var);
		order_update(s, var);                      //一轮赋值完成以后 对这些变量按照活动性进行相应的排序
	}

	s->size = n > s->size ? n : s->size;         //看进行相应的处理后 solver对象s的实际长度是否发生了变化
}

//enqueue 排队 入队 列队 将变量赋值 并且入队
//根据赋值将变量加入到传播队列之中去
/*
put a new fact on the propagation queue ,as well as immediately updating the varable's value in
the assignment vector. if a conflict arises ,FALSE is returned and the propagation queue cleared
else return true
the parameter from contains a reference to the constraint from which l is propagated(default to NULL if omitted)
omitted 省略的
*/
static inline bool enqueue(solver* s, lit l, clause* from)
{
	lbool* values = s->assigns;                //指向已经赋值的列表的头指针
	int    v = lit_var(l);                     //得到输入的文字的值
	lbool  val = values[v];                   //得到已经赋值了的某一个变量的值 如果文字赋值的话 得到赋值后的值
#ifdef VERBOSEDEBUG
	printf(L_IND"enqueue("L_LIT")\n", L_ind, L_lit(l));
#endif

	//经过lit_sign()函数的相应的处理 l的值变为了1或者-1了
	//下面的这句代码的目的就是得到l已经赋的值
	lbool sig = !lit_sign(l); sig += sig - 1;     
	if (val != l_Undef){
		return val == sig;                 //如果变量已经进行了赋值  判断传进来的准备传播的变量是否等于它已经赋的值
	}
	else{       //如果传入进来的变量还没有进行赋值的情况 要入队的变量还没有赋值的情况
		// New fact -- store it.  
#ifdef VERBOSEDEBUG
		printf(L_IND"bind("L_LIT")\n", L_ind, L_lit(l));
#endif
		int*     levels = s->levels;         //得到每个变量被赋值的层数
		clause** reasons = s->reasons;       //得到每个变量赋值后得到的蕴含赋值子句

		values[v] = sig;                    //对变量进行赋值 而且在我看来是对其赋值为假
		levels[v] = solver_dlevel(s);       //得到赋值变量时的层数
		reasons[v] = from;                 //将导致该变量赋值的子句加入到变量的蕴含子句 也就是学习子句
		s->trail[s->qtail++] = l;           //根据赋值的时间顺序 将赋值的变量加入到赋值队列的队尾

		order_assigned(s, v);              //赋值 但是这个函数没有编写函数体 order是动态变量(没有赋值)的序列
		return true;
	}
}


//assume 假定 猜想 函数是对变量l进行假定赋值
//如果直接发现或者出现了冲突就返回不可满足 前提条件是传播队列是空队列
static inline void assume(solver* s, lit l){
	assert(s->qtail == s->qhead);
	assert(s->assigns[lit_var(l)] == l_Undef);
#ifdef VERBOSEDEBUG
	printf(L_IND"assume("L_LIT")\n", L_ind, L_lit(l));
#endif
	//trail_lim是根据赋值的层数的不同将变量分开了 
	//将s->qtail加入到veci类型的trail_lim中 为什么要这么做呢？for what？
	veci_push(&s->trail_lim, s->qtail);           
	enqueue(s, l, (clause*)0);        //将变量l赋值入队
}

//level是每个变量被赋值的时候所在的那一层 也就是赋值时候的状态
//until 以前  我觉得函数的功能是取消输入level以前的赋值
//函数的功能是取消几个level的变量的赋值
static inline void solver_canceluntil(solver* s, int level) {
	lit*     trail;                 
	lbool*   values;
	clause** reasons;
	int      bound;
	int      c;

	if (solver_dlevel(s) <= level)      //如果当前solver对象s决策的层数小于等于输入的层数
		return;

	trail = s->trail;
	values = s->assigns;              //将已经赋值的序列赋值给values
	reasons = s->reasons;             //将每个变量的蕴含子句赋值给reasons
	//trail_lim: Separator indices for different decision levels in 'trail'. (contains: int)
	bound = (veci_begin(&s->trail_lim))[level];    //得到输入的参数对应层的那个变量

	//从所有变量的尾指针开始 撤销大于level层的变量的赋值
	for (c = s->qtail - 1; c >= bound; c--) {    //大于level以前的变量都需要重新的赋值 取消其原来的赋值
		int     x = lit_var(trail[c]);
		values[x] = l_Undef;                    //将变量赋值为未赋值的状态
		reasons[x] = (clause*)0;                //将与其相关的蕴含的子句清除
	}

	//order 是没有赋值的变量的veci序列
	//从所有变量的头指针开始 在没有赋值的变量序列中 也看看是否有没有撤销的变量
	for (c = s->qhead - 1; c >= bound; c--)
		order_unassigned(s, lit_var(trail[c]));              

	s->qhead = s->qtail = bound;                        //修改所有变量的头指针和尾指针
	veci_resize(&s->trail_lim, level);                  //撤销一些变量的赋值以后 重新估算其size
}


//记录学习子句的一个函数 将学习子句加入到学习子句的集合learnts中去
//记录一个子句并驱动回溯过程
static void solver_record(solver* s, veci* cls)
{
	lit*    begin = veci_begin(cls);               //得到输入的cls子句的头指针
	lit*    end = begin + veci_size(cls);          //得到cls的末尾元素
	clause* c = (veci_size(cls) > 1) ? clause_new(s, begin, end, 1) : (clause*)0;  //输入的cls长度大于1 则新建一个子句
	enqueue(s, *begin, c);     //将子句c中的变量加入到solver对象的元素队列中

	assert(veci_size(cls) > 0);             //确保cls的长度大于0

	//如果要记录的学习子句的长度不为0 则将其加入到solver对象s的学习子句集合中去
	if (c != 0) {
		vecp_push(&s->learnts, c);                //将c加入到学习子句集合learnts中去       
		act_clause_bump(s, c);                    //从原始的子句集合中删除子句c
		s->stats.learnts++;                       //学习子句的个数加1
		s->stats.learnts_literals += veci_size(cls);             //学习子句中的变量个数相应的加c的长度个
	}
}

 
//progress 进展 发展      

static double solver_progress(solver* s)
{
	lbool*  values = s->assigns;     //已经赋值的变量的集合赋值给values
	int*    levels = s->levels;      //得到变量的决策层数的序列
	int     i;

	double  progress = 0;
	double  F = 1.0 / s->size;    
	for (i = 0; i < s->size; i++)
	if (values[i] != l_Undef)                        //如果变量已经赋值
		progress += pow(F, levels[i]);           //幂运算 progress += F的level[i]次幂         
	return progress / s->size;
}

//=================================================================================================
// Major methods:   solver的主要的函数 实现求解功能
//下面的函数是将变量移动
//在simplify子句集合的时候会用到该函数
//removable 可移动的 可去掉的 可免职的
//函数只是对tags中的文字进行了处理 就达到函数的目的了么

static bool solver_lit_removable(solver* s, lit l, int minl)
{
	//tags我觉得是观察变量的观察队列 其中观察变量的赋值情况
	lbool*   tags = s->tags;                //tags在初始化的为0  是正在观察的文字序列
	clause** reasons = s->reasons;          //蕴含赋值的子句的集合     
	int*     levels = s->levels;            //每个文字赋值时候的层数
	int      top = veci_size(&s->tagged);   //tageed 和 stack都是veci类型的变量 得到tagged的长度

	assert(lit_var(l) >= 0 && lit_var(l) < s->size);
	assert(reasons[lit_var(l)] != 0);               //确保文字l有相应的原因子句 l为蕴含赋值
	veci_resize(&s->stack, 0);            //将stack的长度置为0
	veci_push(&s->stack, lit_var(l));     //将变量l添加到s->stack中去

	while (veci_size(&s->stack) > 0){          //当stack中存在元素的时候  其实这个加入元素后不就只有l这一个元素
		clause* c;
		int v = veci_begin(&s->stack)[veci_size(&s->stack) - 1];    //得到stack中最后一个元素的值 也就是l的值
		assert(v >= 0 && v < s->size);
		veci_resize(&s->stack, veci_size(&s->stack) - 1);          //由于加入了元素 所以重新更新一下stack的长度
		assert(reasons[v] != 0);
		c = reasons[v];                                           //将与v(也就是l)相关的蕴含(原因)子句赋值给子句c 

		if (clause_is_lit(c)){                                   //如果蕴含l文字赋值的子句不为空
			int v = lit_var(clause_read_lit(c));                 //将从子句c中读出的变量赋值给v
			if (tags[v] == l_Undef && levels[v] != 0){           //如果在观察队列中v还没有赋值 并且v不在根层
				if (reasons[v] != 0 && ((1 << (levels[v] & 31)) & minl)){   //蕴含v的原因子句不为空
					veci_push(&s->stack, v);                        //将v加入到stack队列中 下次对其进行处理
					tags[v] = l_True;                            //将正在观察的队列中标明v正在观察 就是赋值
					veci_push(&s->tagged, v);                    //标明v已经观察了
				}
				else{  //当蕴含v赋值的原因子句为空时
					int* tagged = veci_begin(&s->tagged);       //获得已经观察队列的列表
					int j;
					//top初始化的时候是tagged的长度 是上一次的以观察文字的队列
					//通过一个for循环将本次观察的文字都赋值为0
					for (j = top; j < veci_size(&s->tagged); j++)  
						tags[tagged[j]] = l_Undef;      //将正在观察的队列中的文字赋值为0 表明还没接受观察
					veci_resize(&s->tagged, top);       //重置一下tagged队列的长度
					return false;                      //返回false
				}
			}
		}
		else{      //当与输入的文字l读出的蕴含其赋值的子句为空的时候
			lit*    lits = clause_begin(c);      //读出与输入文字l相关的原因子句的文字列表
			//下面是自己添加的代码
			/*for (int k = 0; k < clause_size(c); k++)
			{
				printf("%d\n", lit_var(lits[k]));
			}*/

			int     i, j;

			for (i = 1; i < clause_size(c); i++){    //开始处理原因子句中的文字
				int v = lit_var(lits[i]);            //得到原因子句的中的文字
				if (tags[v] == l_Undef && levels[v] != 0){    //如果该文字没有赋值 并且文字不在0(根)层
					if (reasons[v] != 0 && ((1 << (levels[v] & 31)) & minl)){  //如果文字的原因子句不为空
						 
						veci_push(&s->stack, lit_var(lits[i]));  //将文字放入到stack队列中
						tags[v] = l_True;                        //标明文字已经在观察队列中观察了
						veci_push(&s->tagged, v);                //并将其加入到已经观察的队列
					} 
					else{       //如果文字的原因子句为空
						int* tagged = veci_begin(&s->tagged);                //得到已经观察的子句队列
						for (j = top; j < veci_size(&s->tagged); j++)
							tags[tagged[j]] = l_Undef;                      //将本次观察的文字都赋值为0 表明还为观察
						veci_resize(&s->tagged, top);                   //重置一下已经观察的队列的长度
						return false;
					}
				}
			}
		}
	}

	return true;
}


/*
**要想修改算法 加入学习子句或者冲突子句 
**那么只有在analyze函数加入
**只需要对learnt进行相应的操作就可以了
*/




//下面的函数是分析产生冲突的原因然后向子句集合中加入产生冲突的原因子句
//参数 solver对象s 冲突子句c 和要加入到子句集合中的学习子句learnt
//前提条件是learnt已经被清空 而且当前的level要大于根level
//当一个学习子句被用来在一个冲突子句的学习过程中的时候 它的活动性将被改变 增加
//输入的参数c是产生了冲突的子句 而learnt是输出参数 表示由冲突的子句学习而得到的学习子句

static void solver_analyze(solver* s, clause* c, veci* learnt)
{
	lit*     trail = s->trail;                  //trail是赋值的变量的序列 按时间先后顺序
	lbool*   tags = s->tags;                    //tags我觉得是观察变量的观察队列 其中观察变量的赋值情况    
	clause** reasons = s->reasons;              //将蕴含赋值变量的那些子句存在reasons中
	int*     levels = s->levels;                //得到所有的文字赋值的时候所在的层数
	int      cnt = 0; 
	lit      p = lit_Undef;                     //lit_Undef的值为-2 表明文字还没赋值 文字处于未定义的状态
	int      ind = s->qtail - 1;                //qtail是整个队列的尾指针 是传播队列 得到传播队列的最后一个文字
	lit*     lits;                              //存储变量的列表
	int      i, j, minl;                        //一些临时变量
	int*     tagged;                            //存放的是已经观察过的变量
	int      maxlevel;                          //得到回溯的最大的层数 然后自己考虑加入学习子句
	lit      addMyLit;                          //子句要加入的回溯层数的文字

	//generate a conflict clause  产生一个冲突子句
	veci_push(learnt, lit_Undef);                         //将-2加入到学习子句中 为断定(就是蕴含了子句冲突的那些文字)变量留取空间

	do{
		assert(c != 0);                     //当输入的参数(也就是产生了冲突的)子句c不为0的时候  
		//先对冲突子句c本身进行相应的处理 然后再考虑与其相关的原因子句
		if (clause_is_lit(c)){               //如果子句c中存在文字  考虑一下冲突子句本身
			lit q = clause_read_lit(c);               //从子句c中读入文字并赋值给q
			assert(lit_var(q) >= 0 && lit_var(q) < s->size);   
			if (tags[lit_var(q)] == l_Undef && levels[lit_var(q)] > 0){   //如果q并没有被赋值也就是q还没有被作为观察的文字
				tags[lit_var(q)] = l_True;         //将文字p的观察值赋值为1 表明该文字正在观察
				veci_push(&s->tagged, lit_var(q));        //将其加入到已经观察的文字队列
				//将文字的活动性进行相应的改变 然后将文字重新进行活动新排序
				act_var_bump(s, lit_var(q));                   
				//solver_delevel函数是将一个存有每个变量赋值时的层数所在的序列长度返回来 就相当于得到变量赋值时的层数
				//如果当前处理的文字q也是求解器现在所在的层数 该文字不是导致冲突产生的蕴含赋值的文字
				if (levels[lit_var(q)] == solver_dlevel(s))
					cnt++;                   //对冲突子句中的其他文字进行观察 cnt++ 导致不会跳出while循环
				else
					//如果文字q不是在当前层赋值的 而是在前面已经赋值 那么改文字是导致冲突产生的文字 需要加到learnt中
					veci_push(learnt, q);   //否则的话 该文字是导致冲突产生的蕴含的文字 将其加入到学习子句中去
			}
		}
		else{                       //当子句c不存在变量的时候 意思是没有冲突子句的产生么
			

			//下面的这段代码我是没有理解呢？

			if (clause_learnt(c))           //当c的学习子句中存在变量 即不为空的时候 
				act_clause_bump(s, c);      //修改子句c的活动性   

			//相当于将lits子句进行了初始化 并开始处理与冲突子句相关的文字
			lits = clause_begin(c);              //获取冲突子句c的文字列表   

			//下面的输出函数是作者自己注释掉的
			//一般的情况下我觉得这段代码都不会执行的
			//printf("I think this code will not execute! \n");
			//printlits(lits,lits+clause_size(c)); printf("\n");
			//outConflict(lits,lits+clause_size(c));

			//p的值在初始化的时候就是lit_Undef  一一对冲突子句中的文字进行处理
			for (j = (p == lit_Undef ? 0 : 1); j < clause_size(c); j++){
				lit q = lits[j];                                 //q的值为冲突子句c中的文字 从0开始
				//下面是自己加入的测试的代码
				//printf("%d\n",lit_var(q));

				assert(lit_var(q) >= 0 && lit_var(q) < s->size);
				if (tags[lit_var(q)] == l_Undef && levels[lit_var(q)] > 0){    //tags在初始化的时候就是初始化为1_undef
					tags[lit_var(q)] = l_True;               //在观察队列中将观察的变量赋值为1
					veci_push(&s->tagged, lit_var(q));       //将刚才观察的变量添加到已经观察的观察队列中
					act_var_bump(s, lit_var(q));      //从求解器中弹出变量q 其实就是改变文字的活动性
					//如果当前处理的文字q也是求解器现在所在的层数 该文字不是导致冲突产生的蕴含赋值的文字
					if (levels[lit_var(q)] == solver_dlevel(s))    
						cnt++;
					else
						veci_push(learnt, q);   //否则该文字是导致冲突的蕴含的文字 需要将它加入到学习子句中去
				}
			}
		}

		//选择下一个子句进行考虑
		while (tags[lit_var(trail[ind--])] == l_Undef);

		p = trail[ind + 1];
		c = reasons[lit_var(p)];
		cnt--;

	} while (cnt > 0);

	
	//将学习子句的第一个文字赋值为p的非
	*veci_begin(learnt) = lit_neg(p);      //得到学习子句的文字 就是与冲突子句相关的蕴含赋值的文字

	lits = veci_begin(learnt);             //通过将lits指针指向learnt子句 那么就可以操作lits而修改学习子句了
	minl = 0;
	for (i = 1; i < veci_size(learnt); i++){
		int lev = levels[lit_var(lits[i])];
		minl |= 1 << (lev & 31);
	}

	//simplify conflict clause:
	// simplify (full)
	for (i = j = 1; i < veci_size(learnt); i++){
		//化简一些子句
		if (reasons[lit_var(lits[i])] == 0 || !solver_lit_removable(s, lits[i], minl))
			lits[j++] = lits[i];
	}

	// update size of learnt + statistics
	s->stats.max_literals += veci_size(learnt);
	veci_resize(learnt, j);       //因为将学习子句化简了 所以其长度可能已经改变了 重置学习子句的大小
	s->stats.tot_literals += j;

	// clear tags
	tagged = veci_begin(&s->tagged);
	for (i = 0; i < veci_size(&s->tagged); i++)
		tags[tagged[i]] = l_Undef;
	veci_resize(&s->tagged, 0);

#ifdef DEBUG
	for (i = 0; i < s->size; i++)
		assert(tags[i] == l_Undef);
#endif

#ifdef VERBOSEDEBUG
	printf(L_IND"Learnt {", L_ind);
	for (i = 0; i < veci_size(learnt); i++) printf(" "L_LIT, L_lit(lits[i]));
#endif

	//下面是找到导致冲突子句产生的文字的最大层数 以用来作为回溯的层数
	if (veci_size(learnt) > 1){
		int max_i = 1;      
		int max = levels[lit_var(lits[1])];    //max等于冲突子句的第一个文字的决策层数
		maxlevel = max;                        //得到回溯的最大层数
		lit tmp;

		//通过for循环找到最大的层数
		for (i = 2; i < veci_size(learnt); i++)
		if (levels[lit_var(lits[i])] > max){
			max = levels[lit_var(lits[i])];
			//maxlevel = max;                   //得到回溯的最大层数
			max_i = i;
		}

		tmp = lits[1];
		lits[1] = lits[max_i];     //保证在lits[]数组中的文字的排序是按照层数由大到小排列的
		lits[max_i] = tmp;

		addMyLit = lits[1];       //因为在lits中的第一个文字就是层数最大的文字 所以将其赋值给addMyLit
		maxlevel = levels[lit_var(lits[1])];   //得到回溯的最大层数
	}
#ifdef VERBOSEDEBUG
	{
		int lev = veci_size(learnt) > 1 ? levels[lit_var(lits[1])] : 0;
		printf(" } at level %d\n", lev);
	}
#endif


	//在得到要回溯的最大层数和回溯到最大层数的文字的时候
	//下面是自己改进求解器的算法
	/*
	**首先将与最大层数的文字相关的原因子句读出
	**然后对每个原因子句中包含改文字的子句进行处理
	**对包含改文字的子句中的改文字都取true
	**然后对所有的子句取非操作 并将这些子句组合起来形成相应的子句
	**将得到的子句加入到学习子句 测试看能否增加效率
	**reason的类型为clause**类型 那么reason[i]表示的是clause*类型
	*/

	//最大的层数是maxlevel 最大层数的文字是addMyLit
	//printf("maxlevle: %d\n",maxlevel);
	//printf("addMyLit: %d\n",lit_var(lits[1]));

	//clause* clause = reasons[lit_var(lits[1])];   //得到与最大层数相关的文字的原因子句
	//当原因子句中存在文字的时候进行相应的操作
	//lit* mylit = clause_begin(clause);          //获得与原因子句clause相关的文字
	//通过一个for循环对文字相关的子句进行处理
	//int m;
	//lit templit;
	
	//printlits(mylit,mylit+clause_size(clause));
	//m = clause_size(clause);
	//printf("%d\n",m);

	


}


/*
propagate all enqueued facts. 试图找到单元子句
if a conflict arises . the conflicting clause is returned otherwise NULL
产生了冲突 则将冲突子句返回 否则返回空值
在传播的过程中 首先先选择一个变量进行考虑 采用watch literals的策略来进行BCP的过程 直到产生了冲突为止
而在产生了冲突以后 我要做的就是遍历与产生冲突的变量的子句进行处理
得到学习子句 然后将学习子句加入到原始的子句集合中去
*/
clause* solver_propagate(solver* s)
{
	lbool*  values = s->assigns;              //将已经赋值的变量队列赋值给values
	clause* confl = (clause*)0;               //初始化冲突子句为空
	lit*    lits;

	//下面是作者注释了的代码 我将它解开看看
	//printf("solver_propagate\n");    //进行传播的过程
	while (confl == 0 && s->qtail - s->qhead > 0){   //当子句队列中存在元素的时候 这个队列中存储的是未赋值的变量
		//选择一个变量进行赋值然后进行约束传播
		lit  p = s->trail[s->qhead++];                          //得到赋值的变量 并将该变量赋值给p          
		vecp* ws = solver_read_wlist(s, p);                     //得到与p相关的子句集合
		clause **begin = (clause**)vecp_begin(ws);             //得到子句的头指针  返回的是是指针的指针
		clause **end = begin + vecp_size(ws);                  //得到子句集合的尾指针
		clause **i, **j;

		s->stats.propagations++;           //传播过程加1  在solver中有专门的变量记录传播的过程 也就是传播的次数
		s->simpdb_props--;                 //将在下次化简子句集合前的传播数量减一


		//printf("checking lit %d: "L_LIT"\n", veci_size(ws), L_lit(p));
		for (i = j = begin; i < end;){                     //对与p相关的子句一一进行相应的处理
			if (clause_is_lit(*i)){     //如果对于与p相关的某一个子句不为空 就是存在子句
				*j++ = *i;                          //子句i存放的是与p相关的子句 并将它赋值给子句j
				//clause_read_lit(clause *)是从子句中读取出变量 clause_from_lit(lit p)是读取与p相关的子句
				//enqueue函数会对传入的变量进行判断 看其是否已经被赋值 
				//如果已经被赋值 则看其赋值是否为假 否则会对传入的变量赋值 并将导致其赋值的子句加入到原因子句中去
				
				if (!enqueue(s, clause_read_lit(*i), clause_from_lit(p))){   // 选择变量p进行传播 看是否可满足 否则排队
					//当将变量p加入传播队列的时候出现了冲突  下面的代码的用意是什么？？？ 产生学习子句？？？？
					//A temporary binary clause storing the literals to be propagated directly in the watcher list
					confl = s->binary;        
					//lit_neg(p)是将p与1做异或操作 表明当p为1的时候为0 当p为0则为1
					//confl中存的是学习子句么 confl中只有两个文字 第一个是与enqueue相反的p值  第二个是i中的第一个文字 
					(clause_begin(confl))[1] = lit_neg(p);          
					(clause_begin(confl))[0] = clause_read_lit(*i++);    //读出子句i中的第一个文字赋值给confl中的第一个文字          

					// Copy the remaining watches:
					while (i < end)                     //将冲突子句赋值给confl并在后面返回 其他的子句赋值给子句j
						*j++ = *i++;
				}
			}
			else{                   //当clause_is_lit(*i)为假的情况  指的是i这个子句中没有变量的情况么？
				lit false_lit;               //lit是int类型
				lbool sig;                   //lbool为char类型

				//其实在clause结构体中 拥有lit lit[]类型的数组
				//下面claise_begin(*i)是返回子句i中的lit类型的数组 
				lits = clause_begin(*i);

				/*我记得MiniSat采用的是watch literals的策略 所以不考虑前面的n-2个文字
				**只需要考虑的是选择两个文字进行相应的赋值 在这里在约束传播的过程中
				**程序先对选择的第二个文字赋值为假 然后得到蕴含赋值第一个文字为真 
				**这样依次的考虑下去   一般选择子句中的前两个文字作为watch literals所观测的文字
				*/
				// Make sure the false literal is data[1]: 在这里确保data[1]为false的目的何在?
				false_lit = lit_neg(p);               //lit_neg是异或操作 函数与1进行异或 看p的值p为1则false_lit为0 
				if (lits[0] == false_lit){         //如果第一个变量的值为假的时候
					lits[0] = lits[1];             // 则将第一个变量的值赋值给lit[0]
					lits[1] = false_lit;           //将lit[1]的值赋值为false
				}
				assert(lits[1] == false_lit);
				//下面是作者自己注释了的代码 我将它解开看看  该输出是输出那些过程中检测的与文字p相关的子句的
				//printf("With the assign value of p , Our program will check the clause with p :\n");
				//printf("checking clause: "); printlits(lits, lits+clause_size(*i)); printf("\n");

				//判断一下观察的子句的真假 为真的情况直接考虑一下下一个子句 为假的情况需要重新选择文字
				// If 0th watch is true, then clause is already satisfied.
				//watch(是观察的两个文字的一个 在这这里由于lit[1]已经为false 那么要使观察的子句为真 那么只有lits[0]的值为true
				sig = !lit_sign(lits[0]); sig += sig - 1;   //当变量的第一个变量的值为1的时候 则sig的值为0
				if (values[lit_var(lits[0])] == sig){       //如果文字已经赋值  并且为真的情况下
					*j++ = *i;                              //跳过该子句 考虑下一个子句
				}
				else{     //观察的两个文字的值都为假值 考虑重新选取下一个文字进行考虑
					// Look for new watch:
					lit* stop = lits + clause_size(*i);   //得到与i这个子句相关的最后一个文字
					lit* k;
					for (k = lits + 2; k < stop; k++){  //从第三个文字开始考虑 因为第一个和第二个文字已经考虑了
						lbool sig = lit_sign(*k); sig += sig - 1;
						if (values[lit_var(*k)] != sig){
							lits[1] = *k;
							*k = false_lit;
							//找到一个新的变量进入到watch literals中 需要将该变量相关的子句加入到与该变量相关的子句队列
							vecp_push(solver_read_wlist(s, lit_neg(lits[1])), *i);
							goto next;  //进入到下一个子句 考虑下一个子句
						}
					}

					//如果该子句中其他的文字已经赋值 单元子句？ 我总觉得不是这样的？
					*j++ = *i;
					// Clause is unit under assignment:
					if (!enqueue(s, lits[0], *i)){   //那么需要将该文字送入传播的队列
						//如果在将该文字送入传播队列的时候出现错误 那么表明这个子句是冲突的 直接将该子句赋值给confl
						confl = *i++;
						// Copy the remaining watches:
						while (i < end)
							*j++ = *i++;    //将剩余的子句赋值给j
					}
				}
			}
		next:
			i++;
		}

		s->stats.inspects += j - (clause**)vecp_begin(ws);   //计算子句的检查的次数
		vecp_resize(ws, j - (clause**)vecp_begin(ws));       //重新计算子句集合的大小
	}

	return confl;                      //将传播的过程中的冲突子句返回
}

/*/
//下面的函数是自己写的函数 
//目的是在propagate一个变量的时候 对于该变量的赋值时导致了冲突的产生
//那么对于与该变量相关的子句 我们会对其进行相应的处理 得到学习子句
//并将学习子句加入到子句集合中去

clause* solver_ClauseLearnt(solver *s , lit t )    //t为赋值产生冲突的变量
{
	clause* conflict = (clause*)0;               //用于存储最后化简得到的学习子句
	vecp* ws = solver_read_wlist(s, t);          //读取与文字t相关的子句 这里能一定保证相关的子句就是包含文字t的子句么
	clause **begin = (clause**)vecp_begin(ws);   //得到与t相关的子句的第一个子句 
	clause **end = begin + vecp_size(ws);        //得到与t相关的最后一个子句
	clause **i, **j;
	int k;
	clause *temp, *temp1;
	lit  *p , *q;
		 
	//开始遍历与t相关的子句 并对这些包含t的子句进行处理
	
	//可以先用clause_from_lit()函数读出子句
	//再用clause_read_lit()从子句中读出变量
	//但是这样是对的么？还是说是我的个人感觉呢？我就CAO了 试试吧
	
	for (i = j = begin; i < end; i++)
	{
		if (clause_is_lit(*i))       //子句的集合存在子句的情况
		{
			*j++ = *i;              //将i的值赋值给j 同时j相应的加1
			temp = clause_from_lit(t);    //从与t相关的子句集合中读出子句
			
		}
	}

	return conflict;
}
*/


//比较两个子句相等
static inline int clause_cmp(const void* x, const void* y) {
	return clause_size((clause*)x) > 2 && (clause_size((clause*)y) == 2 || clause_activity((clause*)x) < clause_activity((clause*)y)) ? -1 : 1;
}

/*
remove half of the learnt clauses minus some locked clauses
a locked clause is a clauses that is reason to  a current assignment 
clauses below a certain lower bound activity  are also be removed
化简学习子句的子句集合
*/
void solver_reducedb(solver* s)
{
	int  i, j;
	//将活动性低于extra_lim的子句移走
    //将子句移走要保证问题的可满足性不会被修改
	//能对下面的这个学习子句的子句集合进行相应的处理么
	double   extra_lim = s->cla_inc / vecp_size(&s->learnts); // Remove any clause below this activity
	clause** learnts = (clause**)vecp_begin(&s->learnts);
	clause** reasons = s->reasons;

	//按照活动性的大小对学习子句进行排序
	sort(vecp_begin(&s->learnts), vecp_size(&s->learnts), &clause_cmp);

	for (i = j = 0; i < vecp_size(&s->learnts) / 2; i++){
		if (clause_size(learnts[i]) > 2 && reasons[lit_var(*clause_begin(learnts[i]))] != learnts[i])
			clause_remove(s, learnts[i]);
		else
			learnts[j++] = learnts[i];
	}
	for (; i < vecp_size(&s->learnts); i++){
		if (clause_size(learnts[i]) > 2 && reasons[lit_var(*clause_begin(learnts[i]))] != learnts[i] && clause_activity(learnts[i]) < extra_lim)
			clause_remove(s, learnts[i]);
		else
			learnts[j++] = learnts[i];
	}

	//printf("reducedb deleted %d\n", vecp_size(&s->learnts) - j);


	vecp_resize(&s->learnts, j);
}


/*
assumes and propagates until a conflict is found from which a conflict clause is learnt 
and backtracking performed until search can continue  specified规定的  
Search for a model the specified number of conflicts, keeping the number of learnt clauses
below the provided limit. NOTE! Use negative value for 'nof_conflicts' or 'nof_learnts' to
  indicate infinity.
*/
static lbool solver_search(solver* s, int nof_conflicts, int nof_learnts)
{
	int*    levels = s->levels;
	// INVERSE(相反的) decay(缩减) factor for variable activity: stores 1/decay. 
	double  var_decay = 0.95;     
	//我在前面的时间发现这个值在0.99的时候对于可满足的问题的求解时间有一定的提高
	//但是不知道是测试的例子太少的缘故
	//double var_decay = 0.99;

	double  clause_decay = 0.999;
	//因为求解器会根据random_var_freq的值来判断是随机的选择文字赋值，还是采用VSIDS策略
	double  random_var_freq = 0.02;
	//double  random_var_freq = 0.05;    //这个值得改变需要更多的测试数据

	int     conflictC = 0;               //记录冲突子句的个数
	veci    learnt_clause;               //记录学习子句

	assert(s->root_level == solver_dlevel(s));

	s->stats.starts++;                          //这个代表的是搜索的次数加1
	s->var_decay = (float)(1 / var_decay);      //变量缩减的大小
	s->cla_decay = (float)(1 / clause_decay);   //子句缩减的大小 
	veci_resize(&s->model, 0);                  //model中存放的是解 将解的大小先置0
	veci_new(&learnt_clause);                  //为新的学习子句申请相应的空间

	for (;;){    //无限循环 选择文字赋值进行BCP的过程 直到冲突的产生或者所有的文字都已经赋值 问题可满足
		clause* confl = solver_propagate(s);               //通过调用solver对象s的传播函数得到冲突并赋值给confl
		if (confl != 0){                                   //当confl不为空的时候表示产生了冲突 需要找到回溯的层数
			// CONFLICT
			int blevel;                                     //用来存储回溯的层数

#ifdef VERBOSEDEBUG
			printf(L_IND"**CONFLICT**\n", L_ind);
#endif
			s->stats.conflicts++; conflictC++;           //冲突的子句的数目加1 并且冲突计数器加1
			if (solver_dlevel(s) == s->root_level){      //如果产生的冲突是在顶点层 决策层数
				veci_delete(&learnt_clause);            //删除前面申请的学习子句
				return l_False;                         //返回在该层的搜索是不行
			}
			//产生了冲突 并且现在的决策层数不是根层

			veci_resize(&learnt_clause, 0);              //对前面申请的学习子句分配空间
	        //分析产生冲突的原因 并将产生的学习子句赋值给learnt_clause
			solver_analyze(s, confl, &learnt_clause);  
			//找到要回溯的层数
			blevel = veci_size(&learnt_clause) > 1 ? levels[lit_var(veci_begin(&learnt_clause)[1])] : s->root_level;
			//如果要回溯的那一层比root_level还小 那么不如从新开始搜索 
			//在学习子句中的第一个文字所对应的层数是导致冲突产生的文字的最大层
			blevel = s->root_level > blevel ? s->root_level : blevel;
			//取消在该层之前的所有变量的赋值
			solver_canceluntil(s, blevel);
			//将产生的学习子句加入到子句集合中去
			solver_record(s, &learnt_clause);
			//发现了冲突之后 需要更新变量和子句的活动性 好在下次进行变量的选择赋值
			act_var_decay(s);
			act_clause_decay(s);

		}
		else{
			// NO CONFLICT       confl的值为空 那就是在BCP传播的过程中没有遇到冲突
			//会选择另外的一个变量进行赋值 然后进行BCP的过程
			//当然在选择这个变量之前 会考虑一些条件是否满足了 进行相应的处理
			int next;

			if (nof_conflicts >= 0 && conflictC >= nof_conflicts){  
				//冲突子句的个数大于0 传播的过程中产生的冲突子句的个数大于输入的冲突子句个数 conflictC 在传播的过程中产生的冲突子句个数
				// Reached bound on number of conflicts: 达到了冲突子句的范围 程序会规定一个范围
			
				s->progress_estimate = solver_progress(s); 
				//取消在根层以前的变量赋值    当产生的冲突子句个数太快 
				solver_canceluntil(s, s->root_level);
				//删除前面申请的学习子句
				veci_delete(&learnt_clause);
				//当达到程序规定的冲突子句的范围的时候 返回问题的满足性还不知道 
				return l_Undef;
			}
			
			if (solver_dlevel(s) == 0)   //如果传播的过程中回到顶层 那么需要化简一下问题子句
				// Simplify the set of problem clauses:
				solver_simplify(s);         

			//如果存在学习子句 并且在传播的过程中产生的学习子句的个数大于输入的学习子句个数
			//也就是产生的学习子句的个数大于程序设计规定的学习子句的范围的时候 必须缩减学习子句的个数
			if (nof_learnts >= 0 && vecp_size(&s->learnts) - s->qtail >= nof_learnts)
				// Reduce the set of learnt clauses:
				solver_reducedb(s);          

			//当在传播的过程中没有产生冲突子句并且没有达到程序所设定的子句范围 下面就选择另外的一个变量进行决策过程
			// New variable decision:
			s->stats.decisions++;             //将决策过程的次数加1
			next = order_select(s, (float)random_var_freq);              //选择一个变量 并且判断选择的这个文字是否赋值

			if (next == var_Undef){                //如果选择的变量还没有赋值
				// Model found:  找到解了？
				lbool* values = s->assigns;        //将已经赋值的变量的集合赋值给values
				int i;
				//model是存储求解的解的向量
				//values[]中存放的是已经赋值的文字的集合
				for (i = 0; i < s->size; i++) veci_push(&s->model, (int)values[i]);    //将已经赋值的变量加入到veci类型的model之中
				//为什么要将在根层以前赋值的变量取消呢？程序这里的意思是问题已经是可满足的了
				solver_canceluntil(s, s->root_level);  
				//删除前面申请的学习子句
				veci_delete(&learnt_clause);

				/*
				veci apa; veci_new(&apa);
				for (i = 0; i < s->size; i++)
				veci_push(&apa,(int)(s->model.ptr[i] == l_True ? toLit(i) : lit_neg(toLit(i))));
				printf("model: "); printlits((lit*)apa.ptr, (lit*)apa.ptr + veci_size(&apa)); printf("\n");
				veci_delete(&apa);
		        */

				return l_True;                  //返回问题是可满足的
			}

			assume(s, lit_neg(toLit(next)));            //对选择的变量进行假设赋值 进行下一次的单元传播
		}
	}

	return l_Undef; // cannot happen   由于存在无限的for循环 所以只有在for循环中返回 不可能在这里返回
}

//=================================================================================================
// External solver functions:

//新建一个solver对象
solver* solver_new(void)
{
	solver* s = (solver*)malloc(sizeof(solver));

	// initialize vectors
	vecp_new(&s->clauses);
	vecp_new(&s->learnts);
	veci_new(&s->order);
	veci_new(&s->trail_lim);
	veci_new(&s->tagged);
	veci_new(&s->stack);
	veci_new(&s->model);

	// initialize arrays
	s->wlists = 0;
	s->activity = 0;
	s->assigns = 0;
	s->orderpos = 0;
	s->reasons = 0;
	s->levels = 0;
	s->tags = 0;
	s->trail = 0;


	// initialize other vars
	s->size = 0;
	s->cap = 0;
	s->qhead = 0;
	s->qtail = 0;
	s->cla_inc = 1;
	s->cla_decay = 1;
	s->var_inc = 1;
	s->var_decay = 1;
	s->root_level = 0;
	s->simpdb_assigns = 0;
	s->simpdb_props = 0;
	s->random_seed = 91648253;
	s->progress_estimate = 0;
	s->binary = (clause*)malloc(sizeof(clause)+sizeof(lit)* 2);
	s->binary->size_learnt = (2 << 1);
	s->verbosity = 0;

	s->stats.starts = 0;              //重启次数
	s->stats.decisions = 0;           //决策次数
	s->stats.propagations = 0;        //传播次数
	s->stats.inspects = 0;            //检测 检查次数
	s->stats.conflicts = 0;           //冲突子句的个数
	s->stats.clauses = 0;             //总的子句的个数
	s->stats.clauses_literals = 0;    //总的子句中变量的个数
	s->stats.learnts = 0;             //学习子句的个数
	s->stats.learnts_literals = 0;    //学习子句中变量的个数
	s->stats.max_literals = 0;        //是最大的变量的个数么？
	s->stats.tot_literals = 0;        //是总的变量的个数么？

	return s;
}


//删除一个solver对象
void solver_delete(solver* s)
{
	int i;
	for (i = 0; i < vecp_size(&s->clauses); i++)
		free(vecp_begin(&s->clauses)[i]);

	for (i = 0; i < vecp_size(&s->learnts); i++)
		free(vecp_begin(&s->learnts)[i]);

	// delete vectors
	vecp_delete(&s->clauses);
	vecp_delete(&s->learnts);
	veci_delete(&s->order);
	veci_delete(&s->trail_lim);
	veci_delete(&s->tagged);
	veci_delete(&s->stack);
	veci_delete(&s->model);
	free(s->binary);

	// delete arrays
	if (s->wlists != 0){
		int i;
		for (i = 0; i < s->size * 2; i++)
			vecp_delete(&s->wlists[i]);

		// if one is different from null, all are
		free(s->wlists);
		free(s->activity);
		free(s->assigns);
		free(s->orderpos);
		free(s->reasons);
		free(s->levels);
		free(s->trail);
		free(s->tags);
	}

	free(s);
}

//向求解器中加入子句的函数
bool solver_addclause(solver* s, lit* begin, lit* end)
{
	lit *i, *j;
	int maxvar;                //用于存储最大的变量
	lbool* values;
	lit last;

	if (begin == end) return false;  //当加入的变量个个数为0的时候 退出

	//printlits(begin,end); printf("\n");
	// insertion sort  插入排序
	//下面的maxvar是缩小了两倍的一个子句中的最大值  在刚开始对数据的处理的时候 子句中的文字被扩大了两倍
	maxvar = lit_var(*begin);                   //将第一个变量的值赋值给maxvar  

	//这儿也得加一个输出数据的函数 这样才能保证将子句的所有的数据输出
	//printf("%d\n",maxvar);

	//下面是对一个子句进行处理 每个子句是以0作为结束的标志符
	for (i = begin + 1; i < end; i++){
		lit l = *i;
		//下面是自己加入的输出数据的语句 只是测试的功能
		//printf("%d\n",l);
		maxvar = lit_var(l) > maxvar ? lit_var(l) : maxvar;    //得到最大的变量
		for (j = i; j > begin && *(j - 1) > l; j--)
			*j = *(j - 1);
		*j = l;
	}
	solver_setnvars(s, maxvar + 1);         //对每一个子句申请maxvar+1个变量的变量空间 

	//printlits(begin,end); printf("\n");
	values = s->assigns;                   //得到所有的变量的赋值状况 都还未赋值 都为0
	
	
	// delete duplicates  删除副本
	last = lit_Undef;               //last赋值为0
	//通过for循环判断一下要加入的子句是否是恒真子句
	for (i = j = begin; i < end; i++){ 
		//printf("lit: "L_LIT", value = %d\n", L_lit(*i), (lit_sign(*i) ? -values[lit_var(*i)] : values[lit_var(*i)]));
		//在经过lit_sign()的变换以后 sig的值只有0和1 
		//下面的两行是自己加入的代码
		//printf("%d\n", *i);
		//lbool tem = !lit_sign(*i);
		//printf("%d\n",tem);

		lbool sig = !lit_sign(*i); sig += sig - 1;

		//下面是自己加入的代码测试sig的值 sig的输出只有1和-1两种情况
		//printf("%d\n",sig);
		//printf("%d\n", lit_neg(last));

		//如果加入的子句本身就是一个具有恒真性质的子句 那么可以返回true了
		//不过我自己觉得下面的if语句正确执行的概率不是很大
		if (*i == lit_neg(last) || sig == values[lit_var(*i)])  //如果读入的变量赋值为真 或者它的非为假
			return true;   // tautology  同义反复
		//如果加入的子句的变量都还没有赋值
		else if (*i != last && values[lit_var(*i)] == l_Undef)
			last = *j++ = *i;      //将变量赋值给last
	}

	//printf("final: "); printlits(begin,j); printf("\n");

	if (j == begin)          // empty clause   j指针一直没动 表明是空子句
		return false;
	else if (j - begin == 1) // unit clause
		return enqueue(s, *begin, (clause*)0);         //将单元子句的变量子句进入传播的队列

	// create new clause
	//刚开始加入的子句其标志位learnt为0
	vecp_push(&s->clauses, clause_new(s, begin, j, 0));



	s->stats.clauses++;       //子句的个数加1
	s->stats.clauses_literals += j - begin;      //子句的变量个数加以j-begin这么多个

	return true;           //返回创建新的子句成功
}

/*
top-level simplify  of constraint database. 从顶层开始化简一下问题子句
will remove any satisfied constraint and simplify remianing constraint under(partial 局部的) assignment 
if a top-level conflict is found FALSE is returned
前提条件 decision level must be zero  后置条件 propagation queue is empty

Simplify the clause database according to the current top-level assigment. Currently, the only
thing done here is the removal of satisfied clauses, but more things can be put here.
*/
bool   solver_simplify(solver* s)
{
	clause** reasons;
	int type;

	assert(solver_dlevel(s) == 0);    //要化简子句 必须得保证在根节点的时候

	//在传播的过程中产生了冲突 那么就可以通过冲突子句学习 返回
	if (solver_propagate(s) != 0)     
		return false;

	//int simpdb_assigns: Number of top-level assignments at last 'simplifyDB()' 化简子句集合
	//int simpdb_props：Number of propagations before next 'simplifyDB()'
	//当传播的次数大于0 或者 在顶层的赋值的变量的个数和s->qhead相等的时候
	if (s->qhead == s->simpdb_assigns || s->simpdb_props > 0)   
		return true;

	// Remove satisfied clauses:
	//在传播的过程中没有错误的时候 就会出现可满足的子句
	reasons = s->reasons;   //将蕴含变量赋值的原因子句赋值给reasons
	for (type = 0; type < 2; type++){
		vecp*    cs = type ? &s->learnts : &s->clauses;  //先对原始的子句集合处理 再对学习子句进行相应的处理
		clause** cls = (clause**)vecp_begin(cs);

		int i, j;
		for (j = i = 0; i < vecp_size(cs); i++){
			//如果子句不是导致变量蕴含赋值的原因子句并且该子句是可满足的 那么就要将该子句删除 
			if (reasons[lit_var(*clause_begin(cls[i]))] != cls[i] &&
				clause_simplify(s, cls[i]) == l_True)
				clause_remove(s, cls[i]);
			else
				cls[j++] = cls[i];      //将cls[i]赋值给cls[j] 并且对下一个子句进行处理
		}
		vecp_resize(cs, j);     //当所有的子句都处理完成以后 对子句的长度进行重新的判断
	}

	s->simpdb_assigns = s->qhead;
	// (shouldn't depend on 'stats' really, but it will do for now)
	s->simpdb_props = (int)(s->stats.clauses_literals + s->stats.learnts_literals);

	return true;
}



//求解器的求解过程
/*
main solve method 
前置条件 if assumptions are used simplify() must be called right before using this method .
if not ,a top-level conflict(resulting in a non-usable internal state) 
connot be distinguished from a conflict under assumption 
*/
bool   solver_solve(solver* s, lit* begin, lit* end)
{
	double  nof_conflicts = 100;        //设置冲突子句的一个范围100
	double  nof_learnts = solver_nclauses(s) / 3;        //设置学习子句的范围为子句的数目的三分之一
	lbool   status = l_Undef;                          //求解状态
	lbool*  values = s->assigns;        //将已经赋值的变量的值赋值给values 刚开始的时候肯定为空
	lit*    i;

	//下面是注释了的代码 打开看看 
	printf("solve: "); printlits(begin, end); printf("\n");
	//对每个子句进行判断
	for (i = begin; i < end; i++){
		//判断一下*i的值 如果为负文字 则lit_sign(*i)为1
		switch (lit_sign(*i) ? -values[lit_var(*i)] : values[lit_var(*i)]){
		case 1: /* l_True: */
			break;                      //如果值为1 则是可满足的 跳出switch
		case 0: /* l_Undef */
			assume(s, *i);             //如果还没有对变量进行赋值 那么对变量进行赋值然后BCP过程
			if (solver_propagate(s) == NULL)
				break;
			// falltrough
		case -1: /* l_False */               //如果赋值为假的情况
			solver_canceluntil(s, 0);        //取消在0层以前的赋值 从新开始传播的过程
			return false;
		}
	}

	s->root_level = solver_dlevel(s);   

	//verbosity的值为0表明没有进行求解的过程
	if (s->verbosity >= 1){             //如果verbosity大于等于1时 表明在进行传播的过程 存在一些数据
		printf("==================================[MINISAT]===================================\n");
		printf("| Conflicts |     ORIGINAL     |              LEARNT              |         \n");  //删了Progress
		printf("|           | Clauses Literals |   Limit Clauses Literals  Lit/Cl |         \n");
		printf("==============================================================================\n");
	}

	while (status == l_Undef){    //如果状态没有定义的话  当然在前面确实是1_Undef
		double Ratio = (s->stats.learnts == 0) ? 0.0 :      //得到比率 学习子句中的变量的个数与学习子句个数的比率
			s->stats.learnts_literals / (double)s->stats.learnts;

		if (s->verbosity >= 1){
			//printf("| %9.0f | %7.0f %8.0f | %7.0f %7.0f %8.0f %7.1f |\n",
			printf("| %9.0f | %7.0f %8.0f | %7.0f %7.0f %8.0f %7.1f | %6.3f %% |\n",
				(double)s->stats.conflicts,
				(double)s->stats.clauses,
				(double)s->stats.clauses_literals,
				(double)nof_learnts,
				(double)s->stats.learnts,
				(double)s->stats.learnts_literals,
				Ratio,
				s->progress_estimate * 100);
			fflush(stdout);
		}
		//选择文字进行假设赋值和约束传播BCP 直到产生了冲突或者得到问题是可满足的
		status = solver_search(s, (int)nof_conflicts, (int)nof_learnts);    
		nof_conflicts *= 1.5;       //重新设置冲突子句的范围   增大了冲突子句的范围
		nof_learnts *= 1.1;         //设置学习子句的范围   增大了学习子句的范围
	}
	if (s->verbosity >= 1)   //产生了冲突 取消以前的一些赋值 看问题是否是不可满足的
		printf("==============================================================================\n");

	solver_canceluntil(s, 0);        //取消以前的赋值情况
	return status != l_False;
}


//得到solver对象的变量的个数
int solver_nvars(solver* s)
{
	return s->size;
}


//得到solver对象的子句的个数
int solver_nclauses(solver* s)
{
	return vecp_size(&s->clauses);
}


//得到solver对象的冲突子句的个数
int solver_nconflicts(solver* s)
{
	return (int)s->stats.conflicts;
}

//=================================================================================================
// Sorting functions (sigh):

//下面的这个函数是选择排序算法
static inline void selectionsort(void** array, int size, int(*comp)(const void *, const void *))
{
	int     i, j, best_i;
	void*   tmp;

	for (i = 0; i < size - 1; i++){
		best_i = i;
		for (j = i + 1; j < size; j++){
			if (comp(array[j], array[best_i]) < 0)
				best_i = j;
		}
		tmp = array[i]; array[i] = array[best_i]; array[best_i] = tmp;
	}
}

//调用选择排序函数
static void sortrnd(void** array, int size, int(*comp)(const void *, const void *), double* seed)
{
	if (size <= 15)
		selectionsort(array, size, comp);

	else{
		void*       pivot = array[irand(seed, size)];
		void*       tmp;
		int         i = -1;
		int         j = size;

		for (;;){
			do i++; while (comp(array[i], pivot)<0);
			do j--; while (comp(pivot, array[j])<0);

			if (i >= j) break;

			tmp = array[i]; array[i] = array[j]; array[j] = tmp;
		}

		sortrnd(array, i, comp, seed);
		sortrnd(&array[i], size - i, comp, seed);
	}
}

void sort(void** array, int size, int(*comp)(const void *, const void *))
{
	double seed = 91648253;
	sortrnd(array, size, comp, &seed);
}
