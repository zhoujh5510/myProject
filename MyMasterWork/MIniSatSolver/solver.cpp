#include <stdio.h>
#include <assert.h>
#include <math.h>

#include "solver.h"
#include <fstream>
#include <iostream>

//=================================================================================================
// Debug:
//�Զ����
#define dev  
  using namespace std;

//#define VERBOSEDEBUG

// For derivation output (verbosity level 2)
#define L_IND    "%-*d"
//solver_dlevel���ص����������ǰ�ľ��߲���
#define L_ind    solver_dlevel(s)*3+3,solver_dlevel(s)
//����������궨������������
#define L_LIT    "%sx%d"
//�����lit_sign�����Ƕ������������1����&���� �����������Ϊ������ �򷵻�0 �������򷵻�1
#define L_lit(p) lit_sign(p)?"~":"", (lit_var(p))   //���lit_sign(p)��ֵ��1 ����p�Ǹ����� ��Ҫ��һ���Ƿ���

// Just like 'assert()' but expression will be evaluated in the release version as well.
//���expr�Ƿ�Ϊ1
static inline void check(int expr) { assert(expr); }



//�Լ�д�ĺ��� ����ͻ�Ӿ�������ı��ļ���
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


//������� ����
//����ͷָ���βָ�� �������
static void printlits(lit* begin, lit* end)
{
#ifdef dev
	fstream cout("E:\\out.txt",ios::app);  //�ض�������� ���䶨��������ļ�
#endif
	int i;
	for (i = 0; i < end - begin; i++)
	{
		printf(L_LIT" ", L_lit(begin[i]));    //�������ֵ������������Ӧ�ı�־
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
}              //�����drand����ʽ����Ĳ���0��1֮���ֵ����


//=================================================================================================
// Predeclarations:

void sort(void** array, int size, int(*comp)(const void *, const void *));

//=================================================================================================
// Clause datatype + minor functions:

struct clause_t
{
	int size_learnt;
	//������������Ӧ���ǻ�û������ռ������,�ȵ���Ҫ��ʱ��Ż�ȥ������Ӧ�Ŀռ�
	lit lits[0];                
};


//������⼸��������ʵ������Ҫʱ��ȥ��ϤŪ��
static inline int   clause_size(clause* c)          { return c->size_learnt >> 1; }
static inline lit*  clause_begin(clause* c)          { return c->lits; }      //�����Ӿ�c�е�����
static inline int   clause_learnt(clause* c)          { return c->size_learnt & 1; }
static inline float clause_activity(clause* c)          { return *((float*)&c->lits[c->size_learnt >> 1]);}
static inline void  clause_setactivity(clause* c, float a) { *((float*)&c->lits[c->size_learnt >> 1]) = a; }

//=================================================================================================
// Encode literals in clause pointers:  ���½�clause�е�Ԫ�ؽ��б��� �ٱ�ʾ

//���Ӿ��ָ���ж���һ���Ӿ�
clause* clause_from_lit(lit l)     { return (clause*)((unsigned long)l + (unsigned long)l + 1); }
//�ж�һ���Ӿ��е�����ô���Ҳ�̫�����������Ŀ����ʲô��
bool    clause_is_lit(clause* c) { /*printf("%d\n",(unsigned long)c & 1);*/   return ((unsigned long)c & 1); }
//��һ���Ӿ��ж�����Ӧ������
lit     clause_read_lit(clause* c) { /*printf("%d\n",((unsigned long)c >> 1));*/ return (lit)((unsigned long)c >> 1); }    //��ȡ���ֵ�ʱ������һλ

//=================================================================================================
// Simple helpers:

//�������������Ĺ�����ʵ���Ƿ���solver ������s��һ������s->trail�ĳ���
//��ʵ�ú����Ĺ���Ҳ���Ƿ���������������ڵľ��߲���
static inline int     solver_dlevel(solver* s)    { return veci_size(&s->trail_lim); }   //�����s->trail��һ��veci���͵ı���
static inline vecp*   solver_read_wlist(solver* s, lit l){ return &s->wlists[l]; }  //s->wlist��һ��vecp���͵�ָ�� ���ص����Ӿ伯���е���l��ص��Ӿ�
static inline void    vecp_remove(vecp* v, void* e)   //void���͵�ָ����ζ�Ÿ����͵�ָ�����ָ�������������͵�ָ��
{
	void** ws = vecp_begin(v);
	int    j = 0;

	for (; ws[j] != e; j++);
	assert(j < vecp_size(v));                                 //��֤ÿ���Ӿ��ж���Ԫ��

	//������vecp�Ƕ���ָ�� ��ָ���ÿ��Ԫ�ض���һ��veci ����ɾ��һ��vecpԪ�� ��ʵ���൱��ɾ����һ���Ӿ�
	for (; j < vecp_size(v) - 1; j++) ws[j] = ws[j + 1];     //ͨ��������ǰ�ƶ�һ��Ԫ�شﵽ��e����Ӿ�ɾ����Ŀ��
	vecp_resize(v, vecp_size(v) - 1);         //����ɾ�����vecp����v�Ĵ�С
}

//=================================================================================================
// Variable order functions:
//�������������v ������������ָ�������
static inline void order_update(solver* s, int v) // updateorder  
{
	int*    orderpos = s->orderpos;           //ָ��̬�������б��ͷָ��
	//�����activity��ÿ�������Ļ�Ե�ֵ ��ѡ��������и�ֵ��Լ�������Ĺ����� �����ѡ����ֵ�ߵı���
	double* activity = s->activity;           
	int*    heap = veci_begin(&s->order);    //order��һ��veci���͵ı���
	int     i = orderpos[v];              //ָ��˳�����еĵ�v��Ԫ��
	int     x = heap[i];              //�ҵ�veci�е�Ҫָ���Ԫ��
	int     parent = (i - 1) / 2;          //�ҵ�i�ڵ�Ԫ�صĸ��ڵ�

	assert(s->orderpos[v] != -1);             //��֤��orde�����е�����v���ڻ״̬

	//���������ջ�Ըߵͽ������� ��������
	while (i != 0 && activity[x] > activity[heap[parent]]){
		heap[i] = heap[parent];
		orderpos[heap[i]] = i;
		i = parent;
		parent = (i - 1) / 2;
	}
	heap[i] = x;
	orderpos[x] = i;
}


static inline void order_assigned(solver* s, int v)      //�������е�Ԫ�ؽ��и�ֵ 
{
}


//�������е�Ԫ�س�����ֵ
static inline void order_unassigned(solver* s, int v) // undoorder    
{
	//order�Ǹ������ֵĻ�Եõ������ֵ����ȼ�����
	//orderpos��ָ�����ȼ����е�ͷָ��
	int* orderpos = s->orderpos;                   //orderpos ��û�и�ֵ�ı������е�ͷָ��
	if (orderpos[v] == -1){                        
		orderpos[v] = veci_size(&s->order);
		veci_push(&s->order, v);
		order_update(s, v);
	}
}

//����ȥѡ��һ���µ� û�и�ֵ�ı���
//������random_var_freq��ֵѡ��ʹʹ��������Ի���ʹ��VSID����
static int  order_select(solver* s, float random_var_freq) // selectvar   �����ѡ�����
{
	int*    heap;
	double* activity;
	int*    orderpos;

	lbool* values = s->assigns;                 //lbool��char���� ��ǰ��ֵ���и�values

	// Random decision:   ������Ծ��������ѡ��һ���������и�ֵ
	//random_seed���½�һ��solver�����ʱ��ᱻ��ʼ�� d_rand���ص���0��1֮���һ��floatֵ
	if (drand(&s->random_seed) < random_var_freq){
		int next = irand(&s->random_seed, s->size);     //i_random���ص���0��s->size֮���һ��ֵ ���Ǿ�������Ϊ0
		assert(next >= 0 && next < s->size);           //ȷ��next��ֵ��0��s->szie֮��
		if (values[next] == l_Undef)                   //���ֵΪ0����� ��û�н��и�ֵ��ʱ��
			return next;                   //����next ��ζ�ſ���ѡ��ñ������и�ֵ
	}

	// Activity based decision: ���ڻ�ԵĲ��� ��VSID���ֲ��Բ��

	heap = veci_begin(&s->order);       //��þ��л�����ֶ��еĵ�һ��Ԫ�� 
	activity = s->activity;                 //���Ӧ����һ��ָ�� ָ������Ļ�Ե�һ��һά������
	orderpos = s->orderpos;


	while (veci_size(&s->order) > 0){   //��solver����s�еĻ�Զ����л��������ֵ�ʱ��
		int    next = heap[0];         //nextָ���һ��Ԫ��
		int    size = veci_size(&s->order) - 1;
		int    x = heap[size];                  //xָ������һ��Ԫ��

		veci_resize(&s->order, size);

		orderpos[next] = -1;

		if (size > 0){
			double act = activity[x];   //�õ�����һ��Ԫ�صĻ��ֵ

			int    i = 0;
			int    child = 1;

			//����ļ��д��� �ҵ�������ı���
			while (child < size){				if (child + 1 < size && activity[heap[child]] < activity[heap[child + 1]])
					child++;

				assert(child < size);     //��֤child���� ���ǲ��ܴ��ڱ����ĸ���

				if (act >= activity[heap[child]])
					break;                            //�ҵ���������Եı��� ������whileѭ��

				heap[i] = heap[child];
				orderpos[heap[i]] = i;
				i = child;
				child = 2 * child + 1;
			}
			heap[i] = x;
			orderpos[heap[i]] = i;
		}

		if (values[next] == l_Undef)         //1_undef��ֵΪ0 0��ʾ���ǻ�û�н��и�ֵ �Ѿ���ֵΪtrue��Ϊ1 ��ֵΪfalse��Ϊ-1
			return next;   //���next��û�и�ֵ ��ô����ѡ������������и�ֵ
	}

	return var_Undef;               //���û�и�ֵ�ɹ� �򷵻�-1 ��������δ��ֵ
}

//=================================================================================================
// Activity functions:
//���µ��ڱ����Ļ�� 
//var_inc�� Amount to bump next clause with
static inline void act_var_rescale(solver* s) {
	double* activity = s->activity;
	int i;
	for (i = 0; i < s->size; i++)
		activity[i] *= 1e-100;              //��������activity��ֵ����1e-100   �����ֵĻ�Զ�������
	s->var_inc *= 1e-100;                   //���var_inc��solver����s��һ������ ���ڵ���activity�õ� 
}

//bumpȡ��   
static inline void act_var_bump(solver* s, int v) {
	double* activity = s->activity;
	if ((activity[v] += s->var_inc) > 1e100)
		act_var_rescale(s);                    //���ڱ����Ļ��

	//printf("bump %d %f\n", v-1, activity[v]);

	if (s->orderpos[v] != -1)
		order_update(s, v);           //���������û�и�ֵ �򽫱�������������        

}

//���������������ֵĻ������
static inline void act_var_decay(solver* s) { s->var_inc *= s->var_decay; }


//���µ����Ӿ伯��  ��MiniSat���Ӿ�Ҳ��Ӧ�ľ��л��
static inline void act_clause_rescale(solver* s) {
	clause** cs = (clause**)vecp_begin(&s->learnts);     //�����learnts��vecp���� ��ѧϰ�Ӿ�ļ���
	int i;
	for (i = 0; i < vecp_size(&s->learnts); i++){
		float a = clause_activity(cs[i]);                //����clause_activity�����õ��Ӿ�Ļ�� ��ֵ��float
		clause_setactivity(cs[i], a * (float)1e-20);     //�����Ӿ�Ļ��
	}
	s->cla_inc *= (float)1e-20;
}

//bump ȡ������˼ ��ô�������ҿ��Բ²�ú����Ĺ�����ȡ���Ӿ�Ļ��
//���ݻ�Խ��Ӿ��ԭʼ���Ӿ伯����ɾ��  ��ʵ����ȡ���Ӿ�Ļ��
static inline void act_clause_bump(solver* s, clause *c) {
	float a = clause_activity(c) + s->cla_inc;         //�õ��Ӿ�c�Ļ��ֵ������һ��cla_inc
	clause_setactivity(c, a);                          //���������Ӿ�c�Ļ��
	if (a > 1e20) act_clause_rescale(s);               
}

//�Ҿ���������inc��increase�ļ�д ����������˼
static inline void act_clause_decay(solver* s) { s->cla_inc *= s->cla_decay; }   //decay ˥�� ˥��


//=================================================================================================
// Clause functions:

/* pre: size > 1 && no variable occurs twice
*/
/*�½�һ���Ӿ� ��һ���Ӿ���ͬһ�����������ܳ������� 
**�����Ӿ�ĳ����Ҿ��ñ������1  ��Ϊ��һ���Ӿ��б�����0��Ϊ��β
*/
/*
constructor function for clauses. return false if top-level conflict is detected 
clause c maybe set to NULL if the new clause is satisfied under the current top-level assignment
learnt�Ǳ�־λ ���Ϊ0 �����Ǽ����ԭʼ�Ӿ� ���Ϊ1�Ļ������������ѧϰ�Ӿ�
*/
static clause* clause_new(solver* s, lit* begin, lit* end, int learnt)
{
	int size;                      //Ҫ���뵽�Ӿ��еı����ĸ���
	clause* c;
	int i;

	assert(end - begin > 1);               //��֤���ڱ���Ҫ���뵽�Ӿ���
	assert(learnt >= 0 && learnt < 2);     //learntֻ��0��1����ֵ ԭʼ�Ӿ��ѧϰ�Ӿ�ı�־λ 
	size = end - begin;                    //Ҫ������Ӿ�Ĵ�С               
	c = (clause*)malloc(sizeof(clause)+sizeof(lit)* size + learnt * sizeof(float));   //���Ӿ�c����ռ�
	c->size_learnt = (size << 1) | learnt;    //�Ӿ�Ĵ�С ����������һλ             
	assert(((unsigned int)c & 1) == 0);

	for (i = 0; i < size; i++)
		c->lits[i] = begin[i];                        //�����еı��������뵽�Ӿ���ȥ

	if (learnt)    //learnt��ԭʼ�Ӿ��ѧϰ�Ӿ�ı�־λ 0Ϊԭʼ�Ӿ� 1Ϊѧϰ�Ӿ�
		*((float*)&c->lits[size]) = 0.0;   //�����ѧϰ�Ӿ� ���Ӿ�����һ�����ָ�ֵΪ0

	//��Ϊ��MiniSat�в��õ���watch literals�Ĳ��� �������ؿ��ǵ��Ǹտ�ʼ������

	assert(begin[0] >= 0);
	assert(begin[0] < s->size * 2);
	assert(begin[1] >= 0);
	assert(begin[1] < s->size * 2);

	assert(lit_neg(begin[0]) < s->size * 2);
	assert(lit_neg(begin[1]) < s->size * 2);

	//vecp_push(solver_read_wlist(s,lit_neg(begin[0])),(void*)c);
	//vecp_push(solver_read_wlist(s,lit_neg(begin[1])),(void*)c);

	//solver_read_wlist���ص���wlist�е�ĳһ���Ӿ�  �������ĸ����Ƿ����2��
	//�������һ��������ص��Ӿ� ��������뵽vecp*�Ķ�����ȥ���� ������ڶ���������ص��Ӿ���뵽��һ��ĩβ
	//lit_neg�Ƕ���������ֽ��������� ��ͬΪ0 ��ͬΪ1 �����Ƿ����������෴��ֵ
	//����������ص��Ӿ���뵽�۲���е��Ӿ伯����ȥ
	
	vecp_push(solver_read_wlist(s, lit_neg(begin[0])), (void*)(size > 2 ? c : clause_from_lit(begin[1])));
	vecp_push(solver_read_wlist(s, lit_neg(begin[1])), (void*)(size > 2 ? c : clause_from_lit(begin[0])));

	return c;
}


//���Ӿ伯���е��Ӿ�����
//����vecp��remove�������������Ӿ���Ӿ伯����ɾ����
static void clause_remove(solver* s, clause* c)
{
	lit* lits = clause_begin(c);     //���ص����Ӿ伯�ϵ�ͷָ��
	assert(lit_neg(lits[0]) < s->size * 2);
	assert(lit_neg(lits[1]) < s->size * 2);

	//vecp_remove(solver_read_wlist(s,lit_neg(lits[0])),(void*)c);
	//vecp_remove(solver_read_wlist(s,lit_neg(lits[1])),(void*)c);

	assert(lits[0] < s->size * 2);
	//vecp_remove�����Ĺ��ܺ����ǽ��Ӿ伯���еĸ�����Ĳ�����ȵ��Ӿ�ɾ��
	//����۲��������ص��ڹ۲�����е��Ӿ�Ҳһ����Ӿ伯�����Ƴ�
	vecp_remove(solver_read_wlist(s, lit_neg(lits[0])), (void*)(clause_size(c) > 2 ? c : clause_from_lit(lits[1])));
	vecp_remove(solver_read_wlist(s, lit_neg(lits[1])), (void*)(clause_size(c) > 2 ? c : clause_from_lit(lits[0])));

	if (clause_learnt(c)){
		s->stats.learnts--;     //���ɾ������ѧϰ�Ӿ� ��ô��Ӧ��ѧϰ�Ӿ�ĳ�����Ҫ��һ
		s->stats.learnts_literals -= clause_size(c);     //ѧϰ�Ӿ��б����ĸ�����ȥѧϰ�Ӿ�ĳ�����ô���
	}
	else{
		s->stats.clauses--;        //�����һ����Ӿ� ��ô�Ӿ伯�����Ӿ�ĸ�����һ 
		s->stats.clauses_literals -= clause_size(c);     //��Ӧ�� �Ӿ�ı����ĸ���Ҳ��Ҫ��Ӧ������ô��
	}

	free(c);                     //�ͷ����ߵ��Ӿ�Ŀռ�
}


//����ĺ����ǽ��Ӿ���м򻯵Ĺ���
//��top_level����õĺ��� �����Ӿ伯�� ���ݵ�ǰ�ĸ�ֵ����ж�������Ӿ�c�Ŀ�������
static lbool clause_simplify(solver* s, clause* c)
{
	lit*   lits = clause_begin(c);   //litָ���Ӿ�c��ʼ��Ԫ��
	lbool* values = s->assigns;      //assigns���ָ����ָ���Ѿ���ֵ�ı���
	int i;

	assert(solver_dlevel(s) == 0);  //��Ҫ��֤��top_level��Ż����Ӿ伯��

	for (i = 0; i < clause_size(c); i++){
		//����lit_sign()�����Ĵ��� ����Ĳ���lits[i]��ֵ�����1����-1 
		//�������һ�����õ��Ѿ���ֵ�����ֵĸ�ֵ �ڱ������и����丳ֵ�ж��Ӿ��Ƿ�������
		lbool sig = !lit_sign(lits[i]); sig += sig - 1;      //lboolΪchar���� 
		if (values[lit_var(lits[i])] == sig)
			return l_True;
	}
	return l_False;
}

//=================================================================================================
// Minor (solver) functions:
//������solver��һЩ����


//��������д����µĵı���
void solver_setnvars(solver* s, int n)               //�������� ����n��������ֵ
{
	int var;

	if (s->cap < n){

		while (s->cap < n) s->cap = s->cap * 2 + 1;          //�������n��ô��Ŀռ�

		//���Ǹ��ݱ����Ķ��� Ϊsolver����s������Ӧ��С�Ŀռ�
		s->wlists = (vecp*)realloc(s->wlists, sizeof(vecp)*s->cap * 2);      //wlist��vecp���� ָ����watch literalsô��
		s->activity = (double*)realloc(s->activity, sizeof(double)*s->cap);
		s->assigns = (lbool*)realloc(s->assigns, sizeof(lbool)*s->cap);
		s->orderpos = (int*)realloc(s->orderpos, sizeof(int)*s->cap);
		s->reasons = (clause**)realloc(s->reasons, sizeof(clause*)*s->cap);
		s->levels = (int*)realloc(s->levels, sizeof(int)*s->cap);
		s->tags = (lbool*)realloc(s->tags, sizeof(lbool)*s->cap);
		s->trail = (lit*)realloc(s->trail, sizeof(lit)*s->cap);
	}

	for (var = s->size; var < n; var++){       //���ڴ���solver����sʵ�ʳ��ȵı����Ĵ���
		vecp_new(&s->wlists[2 * var]);
		vecp_new(&s->wlists[2 * var + 1]);
		s->activity[var] = 0;                    //��������Ϊ0
		s->assigns[var] = l_Undef;               //���ñ�����û�и���ֵ
		s->orderpos[var] = veci_size(&s->order);
		s->reasons[var] = (clause*)0;
		s->levels[var] = 0;
		s->tags[var] = l_Undef;

		/* does not hold because variables enqueued at top level will not be reinserted in the heap
		assert(veci_size(&s->order) == var);
		*/
		veci_push(&s->order, var);
		order_update(s, var);                      //һ�ָ�ֵ����Ժ� ����Щ�������ջ�Խ�����Ӧ������
	}

	s->size = n > s->size ? n : s->size;         //��������Ӧ�Ĵ���� solver����s��ʵ�ʳ����Ƿ����˱仯
}

//enqueue �Ŷ� ��� �ж� ��������ֵ �������
//���ݸ�ֵ���������뵽��������֮��ȥ
/*
put a new fact on the propagation queue ,as well as immediately updating the varable's value in
the assignment vector. if a conflict arises ,FALSE is returned and the propagation queue cleared
else return true
the parameter from contains a reference to the constraint from which l is propagated(default to NULL if omitted)
omitted ʡ�Ե�
*/
static inline bool enqueue(solver* s, lit l, clause* from)
{
	lbool* values = s->assigns;                //ָ���Ѿ���ֵ���б��ͷָ��
	int    v = lit_var(l);                     //�õ���������ֵ�ֵ
	lbool  val = values[v];                   //�õ��Ѿ���ֵ�˵�ĳһ��������ֵ ������ָ�ֵ�Ļ� �õ���ֵ���ֵ
#ifdef VERBOSEDEBUG
	printf(L_IND"enqueue("L_LIT")\n", L_ind, L_lit(l));
#endif

	//����lit_sign()��������Ӧ�Ĵ��� l��ֵ��Ϊ��1����-1��
	//������������Ŀ�ľ��ǵõ�l�Ѿ�����ֵ
	lbool sig = !lit_sign(l); sig += sig - 1;     
	if (val != l_Undef){
		return val == sig;                 //��������Ѿ������˸�ֵ  �жϴ�������׼�������ı����Ƿ�������Ѿ�����ֵ
	}
	else{       //�����������ı�����û�н��и�ֵ����� Ҫ��ӵı�����û�и�ֵ�����
		// New fact -- store it.  
#ifdef VERBOSEDEBUG
		printf(L_IND"bind("L_LIT")\n", L_ind, L_lit(l));
#endif
		int*     levels = s->levels;         //�õ�ÿ����������ֵ�Ĳ���
		clause** reasons = s->reasons;       //�õ�ÿ��������ֵ��õ����̺���ֵ�Ӿ�

		values[v] = sig;                    //�Ա������и�ֵ �������ҿ����Ƕ��丳ֵΪ��
		levels[v] = solver_dlevel(s);       //�õ���ֵ����ʱ�Ĳ���
		reasons[v] = from;                 //�����¸ñ�����ֵ���Ӿ���뵽�������̺��Ӿ� Ҳ����ѧϰ�Ӿ�
		s->trail[s->qtail++] = l;           //���ݸ�ֵ��ʱ��˳�� ����ֵ�ı������뵽��ֵ���еĶ�β

		order_assigned(s, v);              //��ֵ �����������û�б�д������ order�Ƕ�̬����(û�и�ֵ)������
		return true;
	}
}


//assume �ٶ� ���� �����ǶԱ���l���мٶ���ֵ
//���ֱ�ӷ��ֻ��߳����˳�ͻ�ͷ��ز������� ǰ�������Ǵ��������ǿն���
static inline void assume(solver* s, lit l){
	assert(s->qtail == s->qhead);
	assert(s->assigns[lit_var(l)] == l_Undef);
#ifdef VERBOSEDEBUG
	printf(L_IND"assume("L_LIT")\n", L_ind, L_lit(l));
#endif
	//trail_lim�Ǹ��ݸ�ֵ�Ĳ����Ĳ�ͬ�������ֿ��� 
	//��s->qtail���뵽veci���͵�trail_lim�� ΪʲôҪ��ô���أ�for what��
	veci_push(&s->trail_lim, s->qtail);           
	enqueue(s, l, (clause*)0);        //������l��ֵ���
}

//level��ÿ����������ֵ��ʱ�����ڵ���һ�� Ҳ���Ǹ�ֵʱ���״̬
//until ��ǰ  �Ҿ��ú����Ĺ�����ȡ������level��ǰ�ĸ�ֵ
//�����Ĺ�����ȡ������level�ı����ĸ�ֵ
static inline void solver_canceluntil(solver* s, int level) {
	lit*     trail;                 
	lbool*   values;
	clause** reasons;
	int      bound;
	int      c;

	if (solver_dlevel(s) <= level)      //�����ǰsolver����s���ߵĲ���С�ڵ�������Ĳ���
		return;

	trail = s->trail;
	values = s->assigns;              //���Ѿ���ֵ�����и�ֵ��values
	reasons = s->reasons;             //��ÿ���������̺��Ӿ丳ֵ��reasons
	//trail_lim: Separator indices for different decision levels in 'trail'. (contains: int)
	bound = (veci_begin(&s->trail_lim))[level];    //�õ�����Ĳ�����Ӧ����Ǹ�����

	//�����б�����βָ�뿪ʼ ��������level��ı����ĸ�ֵ
	for (c = s->qtail - 1; c >= bound; c--) {    //����level��ǰ�ı�������Ҫ���µĸ�ֵ ȡ����ԭ���ĸ�ֵ
		int     x = lit_var(trail[c]);
		values[x] = l_Undef;                    //��������ֵΪδ��ֵ��״̬
		reasons[x] = (clause*)0;                //��������ص��̺����Ӿ����
	}

	//order ��û�и�ֵ�ı�����veci����
	//�����б�����ͷָ�뿪ʼ ��û�и�ֵ�ı��������� Ҳ�����Ƿ���û�г����ı���
	for (c = s->qhead - 1; c >= bound; c--)
		order_unassigned(s, lit_var(trail[c]));              

	s->qhead = s->qtail = bound;                        //�޸����б�����ͷָ���βָ��
	veci_resize(&s->trail_lim, level);                  //����һЩ�����ĸ�ֵ�Ժ� ���¹�����size
}


//��¼ѧϰ�Ӿ��һ������ ��ѧϰ�Ӿ���뵽ѧϰ�Ӿ�ļ���learnts��ȥ
//��¼һ���Ӿ䲢�������ݹ���
static void solver_record(solver* s, veci* cls)
{
	lit*    begin = veci_begin(cls);               //�õ������cls�Ӿ��ͷָ��
	lit*    end = begin + veci_size(cls);          //�õ�cls��ĩβԪ��
	clause* c = (veci_size(cls) > 1) ? clause_new(s, begin, end, 1) : (clause*)0;  //�����cls���ȴ���1 ���½�һ���Ӿ�
	enqueue(s, *begin, c);     //���Ӿ�c�еı������뵽solver�����Ԫ�ض�����

	assert(veci_size(cls) > 0);             //ȷ��cls�ĳ��ȴ���0

	//���Ҫ��¼��ѧϰ�Ӿ�ĳ��Ȳ�Ϊ0 ������뵽solver����s��ѧϰ�Ӿ伯����ȥ
	if (c != 0) {
		vecp_push(&s->learnts, c);                //��c���뵽ѧϰ�Ӿ伯��learnts��ȥ       
		act_clause_bump(s, c);                    //��ԭʼ���Ӿ伯����ɾ���Ӿ�c
		s->stats.learnts++;                       //ѧϰ�Ӿ�ĸ�����1
		s->stats.learnts_literals += veci_size(cls);             //ѧϰ�Ӿ��еı���������Ӧ�ļ�c�ĳ��ȸ�
	}
}

 
//progress ��չ ��չ      

static double solver_progress(solver* s)
{
	lbool*  values = s->assigns;     //�Ѿ���ֵ�ı����ļ��ϸ�ֵ��values
	int*    levels = s->levels;      //�õ������ľ��߲���������
	int     i;

	double  progress = 0;
	double  F = 1.0 / s->size;    
	for (i = 0; i < s->size; i++)
	if (values[i] != l_Undef)                        //��������Ѿ���ֵ
		progress += pow(F, levels[i]);           //������ progress += F��level[i]����         
	return progress / s->size;
}

//=================================================================================================
// Major methods:   solver����Ҫ�ĺ��� ʵ����⹦��
//����ĺ����ǽ������ƶ�
//��simplify�Ӿ伯�ϵ�ʱ����õ��ú���
//removable ���ƶ��� ��ȥ���� ����ְ��
//����ֻ�Ƕ�tags�е����ֽ����˴��� �ʹﵽ������Ŀ����ô

static bool solver_lit_removable(solver* s, lit l, int minl)
{
	//tags�Ҿ����ǹ۲�����Ĺ۲���� ���й۲�����ĸ�ֵ���
	lbool*   tags = s->tags;                //tags�ڳ�ʼ����Ϊ0  �����ڹ۲����������
	clause** reasons = s->reasons;          //�̺���ֵ���Ӿ�ļ���     
	int*     levels = s->levels;            //ÿ�����ָ�ֵʱ��Ĳ���
	int      top = veci_size(&s->tagged);   //tageed �� stack����veci���͵ı��� �õ�tagged�ĳ���

	assert(lit_var(l) >= 0 && lit_var(l) < s->size);
	assert(reasons[lit_var(l)] != 0);               //ȷ������l����Ӧ��ԭ���Ӿ� lΪ�̺���ֵ
	veci_resize(&s->stack, 0);            //��stack�ĳ�����Ϊ0
	veci_push(&s->stack, lit_var(l));     //������l��ӵ�s->stack��ȥ

	while (veci_size(&s->stack) > 0){          //��stack�д���Ԫ�ص�ʱ��  ��ʵ�������Ԫ�غ󲻾�ֻ��l��һ��Ԫ��
		clause* c;
		int v = veci_begin(&s->stack)[veci_size(&s->stack) - 1];    //�õ�stack�����һ��Ԫ�ص�ֵ Ҳ����l��ֵ
		assert(v >= 0 && v < s->size);
		veci_resize(&s->stack, veci_size(&s->stack) - 1);          //���ڼ�����Ԫ�� �������¸���һ��stack�ĳ���
		assert(reasons[v] != 0);
		c = reasons[v];                                           //����v(Ҳ����l)��ص��̺�(ԭ��)�Ӿ丳ֵ���Ӿ�c 

		if (clause_is_lit(c)){                                   //����̺�l���ָ�ֵ���Ӿ䲻Ϊ��
			int v = lit_var(clause_read_lit(c));                 //�����Ӿ�c�ж����ı�����ֵ��v
			if (tags[v] == l_Undef && levels[v] != 0){           //����ڹ۲������v��û�и�ֵ ����v���ڸ���
				if (reasons[v] != 0 && ((1 << (levels[v] & 31)) & minl)){   //�̺�v��ԭ���Ӿ䲻Ϊ��
					veci_push(&s->stack, v);                        //��v���뵽stack������ �´ζ�����д���
					tags[v] = l_True;                            //�����ڹ۲�Ķ����б���v���ڹ۲� ���Ǹ�ֵ
					veci_push(&s->tagged, v);                    //����v�Ѿ��۲���
				}
				else{  //���̺�v��ֵ��ԭ���Ӿ�Ϊ��ʱ
					int* tagged = veci_begin(&s->tagged);       //����Ѿ��۲���е��б�
					int j;
					//top��ʼ����ʱ����tagged�ĳ��� ����һ�ε��Թ۲����ֵĶ���
					//ͨ��һ��forѭ�������ι۲�����ֶ���ֵΪ0
					for (j = top; j < veci_size(&s->tagged); j++)  
						tags[tagged[j]] = l_Undef;      //�����ڹ۲�Ķ����е����ָ�ֵΪ0 ������û���ܹ۲�
					veci_resize(&s->tagged, top);       //����һ��tagged���еĳ���
					return false;                      //����false
				}
			}
		}
		else{      //�������������l�������̺��丳ֵ���Ӿ�Ϊ�յ�ʱ��
			lit*    lits = clause_begin(c);      //��������������l��ص�ԭ���Ӿ�������б�
			//�������Լ���ӵĴ���
			/*for (int k = 0; k < clause_size(c); k++)
			{
				printf("%d\n", lit_var(lits[k]));
			}*/

			int     i, j;

			for (i = 1; i < clause_size(c); i++){    //��ʼ����ԭ���Ӿ��е�����
				int v = lit_var(lits[i]);            //�õ�ԭ���Ӿ���е�����
				if (tags[v] == l_Undef && levels[v] != 0){    //���������û�и�ֵ �������ֲ���0(��)��
					if (reasons[v] != 0 && ((1 << (levels[v] & 31)) & minl)){  //������ֵ�ԭ���Ӿ䲻Ϊ��
						 
						veci_push(&s->stack, lit_var(lits[i]));  //�����ַ��뵽stack������
						tags[v] = l_True;                        //���������Ѿ��ڹ۲�����й۲���
						veci_push(&s->tagged, v);                //��������뵽�Ѿ��۲�Ķ���
					} 
					else{       //������ֵ�ԭ���Ӿ�Ϊ��
						int* tagged = veci_begin(&s->tagged);                //�õ��Ѿ��۲���Ӿ����
						for (j = top; j < veci_size(&s->tagged); j++)
							tags[tagged[j]] = l_Undef;                      //�����ι۲�����ֶ���ֵΪ0 ������Ϊ�۲�
						veci_resize(&s->tagged, top);                   //����һ���Ѿ��۲�Ķ��еĳ���
						return false;
					}
				}
			}
		}
	}

	return true;
}


/*
**Ҫ���޸��㷨 ����ѧϰ�Ӿ���߳�ͻ�Ӿ� 
**��ôֻ����analyze��������
**ֻ��Ҫ��learnt������Ӧ�Ĳ����Ϳ�����
*/




//����ĺ����Ƿ���������ͻ��ԭ��Ȼ�����Ӿ伯���м��������ͻ��ԭ���Ӿ�
//���� solver����s ��ͻ�Ӿ�c ��Ҫ���뵽�Ӿ伯���е�ѧϰ�Ӿ�learnt
//ǰ��������learnt�Ѿ������ ���ҵ�ǰ��levelҪ���ڸ�level
//��һ��ѧϰ�Ӿ䱻������һ����ͻ�Ӿ��ѧϰ�����е�ʱ�� ���Ļ�Խ����ı� ����
//����Ĳ���c�ǲ����˳�ͻ���Ӿ� ��learnt��������� ��ʾ�ɳ�ͻ���Ӿ�ѧϰ���õ���ѧϰ�Ӿ�

static void solver_analyze(solver* s, clause* c, veci* learnt)
{
	lit*     trail = s->trail;                  //trail�Ǹ�ֵ�ı��������� ��ʱ���Ⱥ�˳��
	lbool*   tags = s->tags;                    //tags�Ҿ����ǹ۲�����Ĺ۲���� ���й۲�����ĸ�ֵ���    
	clause** reasons = s->reasons;              //���̺���ֵ��������Щ�Ӿ����reasons��
	int*     levels = s->levels;                //�õ����е����ָ�ֵ��ʱ�����ڵĲ���
	int      cnt = 0; 
	lit      p = lit_Undef;                     //lit_Undef��ֵΪ-2 �������ֻ�û��ֵ ���ִ���δ�����״̬
	int      ind = s->qtail - 1;                //qtail���������е�βָ�� �Ǵ������� �õ��������е����һ������
	lit*     lits;                              //�洢�������б�
	int      i, j, minl;                        //һЩ��ʱ����
	int*     tagged;                            //��ŵ����Ѿ��۲���ı���
	int      maxlevel;                          //�õ����ݵ����Ĳ��� Ȼ���Լ����Ǽ���ѧϰ�Ӿ�
	lit      addMyLit;                          //�Ӿ�Ҫ����Ļ��ݲ���������

	//generate a conflict clause  ����һ����ͻ�Ӿ�
	veci_push(learnt, lit_Undef);                         //��-2���뵽ѧϰ�Ӿ��� Ϊ�϶�(�����̺����Ӿ��ͻ����Щ����)������ȡ�ռ�

	do{
		assert(c != 0);                     //������Ĳ���(Ҳ���ǲ����˳�ͻ��)�Ӿ�c��Ϊ0��ʱ��  
		//�ȶԳ�ͻ�Ӿ�c���������Ӧ�Ĵ��� Ȼ���ٿ���������ص�ԭ���Ӿ�
		if (clause_is_lit(c)){               //����Ӿ�c�д�������  ����һ�³�ͻ�Ӿ䱾��
			lit q = clause_read_lit(c);               //���Ӿ�c�ж������ֲ���ֵ��q
			assert(lit_var(q) >= 0 && lit_var(q) < s->size);   
			if (tags[lit_var(q)] == l_Undef && levels[lit_var(q)] > 0){   //���q��û�б���ֵҲ����q��û�б���Ϊ�۲������
				tags[lit_var(q)] = l_True;         //������p�Ĺ۲�ֵ��ֵΪ1 �������������ڹ۲�
				veci_push(&s->tagged, lit_var(q));        //������뵽�Ѿ��۲�����ֶ���
				//�����ֵĻ�Խ�����Ӧ�ĸı� Ȼ���������½��л������
				act_var_bump(s, lit_var(q));                   
				//solver_delevel�����ǽ�һ������ÿ��������ֵʱ�Ĳ������ڵ����г��ȷ����� ���൱�ڵõ�������ֵʱ�Ĳ���
				//�����ǰ���������qҲ��������������ڵĲ��� �����ֲ��ǵ��³�ͻ�������̺���ֵ������
				if (levels[lit_var(q)] == solver_dlevel(s))
					cnt++;                   //�Գ�ͻ�Ӿ��е��������ֽ��й۲� cnt++ ���²�������whileѭ��
				else
					//�������q�����ڵ�ǰ�㸳ֵ�� ������ǰ���Ѿ���ֵ ��ô�������ǵ��³�ͻ���������� ��Ҫ�ӵ�learnt��
					veci_push(learnt, q);   //����Ļ� �������ǵ��³�ͻ�������̺������� ������뵽ѧϰ�Ӿ���ȥ
			}
		}
		else{                       //���Ӿ�c�����ڱ�����ʱ�� ��˼��û�г�ͻ�Ӿ�Ĳ���ô
			

			//�������δ�������û������أ�

			if (clause_learnt(c))           //��c��ѧϰ�Ӿ��д��ڱ��� ����Ϊ�յ�ʱ�� 
				act_clause_bump(s, c);      //�޸��Ӿ�c�Ļ��   

			//�൱�ڽ�lits�Ӿ�����˳�ʼ�� ����ʼ�������ͻ�Ӿ���ص�����
			lits = clause_begin(c);              //��ȡ��ͻ�Ӿ�c�������б�   

			//�������������������Լ�ע�͵���
			//һ���������Ҿ�����δ��붼����ִ�е�
			//printf("I think this code will not execute! \n");
			//printlits(lits,lits+clause_size(c)); printf("\n");
			//outConflict(lits,lits+clause_size(c));

			//p��ֵ�ڳ�ʼ����ʱ�����lit_Undef  һһ�Գ�ͻ�Ӿ��е����ֽ��д���
			for (j = (p == lit_Undef ? 0 : 1); j < clause_size(c); j++){
				lit q = lits[j];                                 //q��ֵΪ��ͻ�Ӿ�c�е����� ��0��ʼ
				//�������Լ�����Ĳ��ԵĴ���
				//printf("%d\n",lit_var(q));

				assert(lit_var(q) >= 0 && lit_var(q) < s->size);
				if (tags[lit_var(q)] == l_Undef && levels[lit_var(q)] > 0){    //tags�ڳ�ʼ����ʱ����ǳ�ʼ��Ϊ1_undef
					tags[lit_var(q)] = l_True;               //�ڹ۲�����н��۲�ı�����ֵΪ1
					veci_push(&s->tagged, lit_var(q));       //���ղŹ۲�ı�����ӵ��Ѿ��۲�Ĺ۲������
					act_var_bump(s, lit_var(q));      //��������е�������q ��ʵ���Ǹı����ֵĻ��
					//�����ǰ���������qҲ��������������ڵĲ��� �����ֲ��ǵ��³�ͻ�������̺���ֵ������
					if (levels[lit_var(q)] == solver_dlevel(s))    
						cnt++;
					else
						veci_push(learnt, q);   //����������ǵ��³�ͻ���̺������� ��Ҫ�������뵽ѧϰ�Ӿ���ȥ
				}
			}
		}

		//ѡ����һ���Ӿ���п���
		while (tags[lit_var(trail[ind--])] == l_Undef);

		p = trail[ind + 1];
		c = reasons[lit_var(p)];
		cnt--;

	} while (cnt > 0);

	
	//��ѧϰ�Ӿ�ĵ�һ�����ָ�ֵΪp�ķ�
	*veci_begin(learnt) = lit_neg(p);      //�õ�ѧϰ�Ӿ������ �������ͻ�Ӿ���ص��̺���ֵ������

	lits = veci_begin(learnt);             //ͨ����litsָ��ָ��learnt�Ӿ� ��ô�Ϳ��Բ���lits���޸�ѧϰ�Ӿ���
	minl = 0;
	for (i = 1; i < veci_size(learnt); i++){
		int lev = levels[lit_var(lits[i])];
		minl |= 1 << (lev & 31);
	}

	//simplify conflict clause:
	// simplify (full)
	for (i = j = 1; i < veci_size(learnt); i++){
		//����һЩ�Ӿ�
		if (reasons[lit_var(lits[i])] == 0 || !solver_lit_removable(s, lits[i], minl))
			lits[j++] = lits[i];
	}

	// update size of learnt + statistics
	s->stats.max_literals += veci_size(learnt);
	veci_resize(learnt, j);       //��Ϊ��ѧϰ�Ӿ仯���� �����䳤�ȿ����Ѿ��ı��� ����ѧϰ�Ӿ�Ĵ�С
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

	//�������ҵ����³�ͻ�Ӿ���������ֵ������� ��������Ϊ���ݵĲ���
	if (veci_size(learnt) > 1){
		int max_i = 1;      
		int max = levels[lit_var(lits[1])];    //max���ڳ�ͻ�Ӿ�ĵ�һ�����ֵľ��߲���
		maxlevel = max;                        //�õ����ݵ�������
		lit tmp;

		//ͨ��forѭ���ҵ����Ĳ���
		for (i = 2; i < veci_size(learnt); i++)
		if (levels[lit_var(lits[i])] > max){
			max = levels[lit_var(lits[i])];
			//maxlevel = max;                   //�õ����ݵ�������
			max_i = i;
		}

		tmp = lits[1];
		lits[1] = lits[max_i];     //��֤��lits[]�����е����ֵ������ǰ��ղ����ɴ�С���е�
		lits[max_i] = tmp;

		addMyLit = lits[1];       //��Ϊ��lits�еĵ�һ�����־��ǲ����������� ���Խ��丳ֵ��addMyLit
		maxlevel = levels[lit_var(lits[1])];   //�õ����ݵ�������
	}
#ifdef VERBOSEDEBUG
	{
		int lev = veci_size(learnt) > 1 ? levels[lit_var(lits[1])] : 0;
		printf(" } at level %d\n", lev);
	}
#endif


	//�ڵõ�Ҫ���ݵ��������ͻ��ݵ������������ֵ�ʱ��
	//�������Լ��Ľ���������㷨
	/*
	**���Ƚ�����������������ص�ԭ���Ӿ����
	**Ȼ���ÿ��ԭ���Ӿ��а��������ֵ��Ӿ���д���
	**�԰��������ֵ��Ӿ��еĸ����ֶ�ȡtrue
	**Ȼ������е��Ӿ�ȡ�ǲ��� ������Щ�Ӿ���������γ���Ӧ���Ӿ�
	**���õ����Ӿ���뵽ѧϰ�Ӿ� ���Կ��ܷ�����Ч��
	**reason������Ϊclause**���� ��ôreason[i]��ʾ����clause*����
	*/

	//���Ĳ�����maxlevel ��������������addMyLit
	//printf("maxlevle: %d\n",maxlevel);
	//printf("addMyLit: %d\n",lit_var(lits[1]));

	//clause* clause = reasons[lit_var(lits[1])];   //�õ�����������ص����ֵ�ԭ���Ӿ�
	//��ԭ���Ӿ��д������ֵ�ʱ�������Ӧ�Ĳ���
	//lit* mylit = clause_begin(clause);          //�����ԭ���Ӿ�clause��ص�����
	//ͨ��һ��forѭ����������ص��Ӿ���д���
	//int m;
	//lit templit;
	
	//printlits(mylit,mylit+clause_size(clause));
	//m = clause_size(clause);
	//printf("%d\n",m);

	


}


/*
propagate all enqueued facts. ��ͼ�ҵ���Ԫ�Ӿ�
if a conflict arises . the conflicting clause is returned otherwise NULL
�����˳�ͻ �򽫳�ͻ�Ӿ䷵�� ���򷵻ؿ�ֵ
�ڴ����Ĺ����� ������ѡ��һ���������п��� ����watch literals�Ĳ���������BCP�Ĺ��� ֱ�������˳�ͻΪֹ
���ڲ����˳�ͻ�Ժ� ��Ҫ���ľ��Ǳ����������ͻ�ı������Ӿ���д���
�õ�ѧϰ�Ӿ� Ȼ��ѧϰ�Ӿ���뵽ԭʼ���Ӿ伯����ȥ
*/
clause* solver_propagate(solver* s)
{
	lbool*  values = s->assigns;              //���Ѿ���ֵ�ı������и�ֵ��values
	clause* confl = (clause*)0;               //��ʼ����ͻ�Ӿ�Ϊ��
	lit*    lits;

	//����������ע���˵Ĵ��� �ҽ����⿪����
	//printf("solver_propagate\n");    //���д����Ĺ���
	while (confl == 0 && s->qtail - s->qhead > 0){   //���Ӿ�����д���Ԫ�ص�ʱ�� ��������д洢����δ��ֵ�ı���
		//ѡ��һ���������и�ֵȻ�����Լ������
		lit  p = s->trail[s->qhead++];                          //�õ���ֵ�ı��� �����ñ�����ֵ��p          
		vecp* ws = solver_read_wlist(s, p);                     //�õ���p��ص��Ӿ伯��
		clause **begin = (clause**)vecp_begin(ws);             //�õ��Ӿ��ͷָ��  ���ص�����ָ���ָ��
		clause **end = begin + vecp_size(ws);                  //�õ��Ӿ伯�ϵ�βָ��
		clause **i, **j;

		s->stats.propagations++;           //�������̼�1  ��solver����ר�ŵı�����¼�����Ĺ��� Ҳ���Ǵ����Ĵ���
		s->simpdb_props--;                 //�����´λ����Ӿ伯��ǰ�Ĵ���������һ


		//printf("checking lit %d: "L_LIT"\n", veci_size(ws), L_lit(p));
		for (i = j = begin; i < end;){                     //����p��ص��Ӿ�һһ������Ӧ�Ĵ���
			if (clause_is_lit(*i)){     //���������p��ص�ĳһ���Ӿ䲻Ϊ�� ���Ǵ����Ӿ�
				*j++ = *i;                          //�Ӿ�i��ŵ�����p��ص��Ӿ� ��������ֵ���Ӿ�j
				//clause_read_lit(clause *)�Ǵ��Ӿ��ж�ȡ������ clause_from_lit(lit p)�Ƕ�ȡ��p��ص��Ӿ�
				//enqueue������Դ���ı��������ж� �����Ƿ��Ѿ�����ֵ 
				//����Ѿ�����ֵ ���丳ֵ�Ƿ�Ϊ�� �����Դ���ı�����ֵ ���������丳ֵ���Ӿ���뵽ԭ���Ӿ���ȥ
				
				if (!enqueue(s, clause_read_lit(*i), clause_from_lit(p))){   // ѡ�����p���д��� ���Ƿ������ �����Ŷ�
					//��������p���봫�����е�ʱ������˳�ͻ  ����Ĵ����������ʲô������ ����ѧϰ�Ӿ䣿������
					//A temporary binary clause storing the literals to be propagated directly in the watcher list
					confl = s->binary;        
					//lit_neg(p)�ǽ�p��1�������� ������pΪ1��ʱ��Ϊ0 ��pΪ0��Ϊ1
					//confl�д����ѧϰ�Ӿ�ô confl��ֻ���������� ��һ������enqueue�෴��pֵ  �ڶ�����i�еĵ�һ������ 
					(clause_begin(confl))[1] = lit_neg(p);          
					(clause_begin(confl))[0] = clause_read_lit(*i++);    //�����Ӿ�i�еĵ�һ�����ָ�ֵ��confl�еĵ�һ������          

					// Copy the remaining watches:
					while (i < end)                     //����ͻ�Ӿ丳ֵ��confl���ں��淵�� �������Ӿ丳ֵ���Ӿ�j
						*j++ = *i++;
				}
			}
			else{                   //��clause_is_lit(*i)Ϊ�ٵ����  ָ����i����Ӿ���û�б��������ô��
				lit false_lit;               //lit��int����
				lbool sig;                   //lboolΪchar����

				//��ʵ��clause�ṹ���� ӵ��lit lit[]���͵�����
				//����claise_begin(*i)�Ƿ����Ӿ�i�е�lit���͵����� 
				lits = clause_begin(*i);

				/*�Ҽǵ�MiniSat���õ���watch literals�Ĳ��� ���Բ�����ǰ���n-2������
				**ֻ��Ҫ���ǵ���ѡ���������ֽ�����Ӧ�ĸ�ֵ ��������Լ�������Ĺ�����
				**�����ȶ�ѡ��ĵڶ������ָ�ֵΪ�� Ȼ��õ��̺���ֵ��һ������Ϊ�� 
				**�������εĿ�����ȥ   һ��ѡ���Ӿ��е�ǰ����������Ϊwatch literals���۲������
				*/
				// Make sure the false literal is data[1]: ������ȷ��data[1]Ϊfalse��Ŀ�ĺ���?
				false_lit = lit_neg(p);               //lit_neg�������� ������1������� ��p��ֵpΪ1��false_litΪ0 
				if (lits[0] == false_lit){         //�����һ��������ֵΪ�ٵ�ʱ��
					lits[0] = lits[1];             // �򽫵�һ��������ֵ��ֵ��lit[0]
					lits[1] = false_lit;           //��lit[1]��ֵ��ֵΪfalse
				}
				assert(lits[1] == false_lit);
				//�����������Լ�ע���˵Ĵ��� �ҽ����⿪����  ������������Щ�����м���������p��ص��Ӿ��
				//printf("With the assign value of p , Our program will check the clause with p :\n");
				//printf("checking clause: "); printlits(lits, lits+clause_size(*i)); printf("\n");

				//�ж�һ�¹۲���Ӿ����� Ϊ������ֱ�ӿ���һ����һ���Ӿ� Ϊ�ٵ������Ҫ����ѡ������
				// If 0th watch is true, then clause is already satisfied.
				//watch(�ǹ۲���������ֵ�һ�� ������������lit[1]�Ѿ�Ϊfalse ��ôҪʹ�۲���Ӿ�Ϊ�� ��ôֻ��lits[0]��ֵΪtrue
				sig = !lit_sign(lits[0]); sig += sig - 1;   //�������ĵ�һ��������ֵΪ1��ʱ�� ��sig��ֵΪ0
				if (values[lit_var(lits[0])] == sig){       //��������Ѿ���ֵ  ����Ϊ��������
					*j++ = *i;                              //�������Ӿ� ������һ���Ӿ�
				}
				else{     //�۲���������ֵ�ֵ��Ϊ��ֵ ��������ѡȡ��һ�����ֽ��п���
					// Look for new watch:
					lit* stop = lits + clause_size(*i);   //�õ���i����Ӿ���ص����һ������
					lit* k;
					for (k = lits + 2; k < stop; k++){  //�ӵ��������ֿ�ʼ���� ��Ϊ��һ���͵ڶ��������Ѿ�������
						lbool sig = lit_sign(*k); sig += sig - 1;
						if (values[lit_var(*k)] != sig){
							lits[1] = *k;
							*k = false_lit;
							//�ҵ�һ���µı������뵽watch literals�� ��Ҫ���ñ�����ص��Ӿ���뵽��ñ�����ص��Ӿ����
							vecp_push(solver_read_wlist(s, lit_neg(lits[1])), *i);
							goto next;  //���뵽��һ���Ӿ� ������һ���Ӿ�
						}
					}

					//������Ӿ��������������Ѿ���ֵ ��Ԫ�Ӿ䣿 ���ܾ��ò��������ģ�
					*j++ = *i;
					// Clause is unit under assignment:
					if (!enqueue(s, lits[0], *i)){   //��ô��Ҫ�����������봫���Ķ���
						//����ڽ����������봫�����е�ʱ����ִ��� ��ô��������Ӿ��ǳ�ͻ�� ֱ�ӽ����Ӿ丳ֵ��confl
						confl = *i++;
						// Copy the remaining watches:
						while (i < end)
							*j++ = *i++;    //��ʣ����Ӿ丳ֵ��j
					}
				}
			}
		next:
			i++;
		}

		s->stats.inspects += j - (clause**)vecp_begin(ws);   //�����Ӿ�ļ��Ĵ���
		vecp_resize(ws, j - (clause**)vecp_begin(ws));       //���¼����Ӿ伯�ϵĴ�С
	}

	return confl;                      //�������Ĺ����еĳ�ͻ�Ӿ䷵��
}

/*/
//����ĺ������Լ�д�ĺ��� 
//Ŀ������propagateһ��������ʱ�� ���ڸñ����ĸ�ֵʱ�����˳�ͻ�Ĳ���
//��ô������ñ�����ص��Ӿ� ���ǻ���������Ӧ�Ĵ��� �õ�ѧϰ�Ӿ�
//����ѧϰ�Ӿ���뵽�Ӿ伯����ȥ

clause* solver_ClauseLearnt(solver *s , lit t )    //tΪ��ֵ������ͻ�ı���
{
	clause* conflict = (clause*)0;               //���ڴ洢��󻯼�õ���ѧϰ�Ӿ�
	vecp* ws = solver_read_wlist(s, t);          //��ȡ������t��ص��Ӿ� ������һ����֤��ص��Ӿ���ǰ�������t���Ӿ�ô
	clause **begin = (clause**)vecp_begin(ws);   //�õ���t��ص��Ӿ�ĵ�һ���Ӿ� 
	clause **end = begin + vecp_size(ws);        //�õ���t��ص����һ���Ӿ�
	clause **i, **j;
	int k;
	clause *temp, *temp1;
	lit  *p , *q;
		 
	//��ʼ������t��ص��Ӿ� ������Щ����t���Ӿ���д���
	
	//��������clause_from_lit()���������Ӿ�
	//����clause_read_lit()���Ӿ��ж�������
	//���������ǶԵ�ô������˵���ҵĸ��˸о��أ��Ҿ�CAO�� ���԰�
	
	for (i = j = begin; i < end; i++)
	{
		if (clause_is_lit(*i))       //�Ӿ�ļ��ϴ����Ӿ�����
		{
			*j++ = *i;              //��i��ֵ��ֵ��j ͬʱj��Ӧ�ļ�1
			temp = clause_from_lit(t);    //����t��ص��Ӿ伯���ж����Ӿ�
			
		}
	}

	return conflict;
}
*/


//�Ƚ������Ӿ����
static inline int clause_cmp(const void* x, const void* y) {
	return clause_size((clause*)x) > 2 && (clause_size((clause*)y) == 2 || clause_activity((clause*)x) < clause_activity((clause*)y)) ? -1 : 1;
}

/*
remove half of the learnt clauses minus some locked clauses
a locked clause is a clauses that is reason to  a current assignment 
clauses below a certain lower bound activity  are also be removed
����ѧϰ�Ӿ���Ӿ伯��
*/
void solver_reducedb(solver* s)
{
	int  i, j;
	//����Ե���extra_lim���Ӿ�����
    //���Ӿ�����Ҫ��֤����Ŀ������Բ��ᱻ�޸�
	//�ܶ���������ѧϰ�Ӿ���Ӿ伯�Ͻ�����Ӧ�Ĵ���ô
	double   extra_lim = s->cla_inc / vecp_size(&s->learnts); // Remove any clause below this activity
	clause** learnts = (clause**)vecp_begin(&s->learnts);
	clause** reasons = s->reasons;

	//���ջ�ԵĴ�С��ѧϰ�Ӿ��������
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
and backtracking performed until search can continue  specified�涨��  
Search for a model the specified number of conflicts, keeping the number of learnt clauses
below the provided limit. NOTE! Use negative value for 'nof_conflicts' or 'nof_learnts' to
  indicate infinity.
*/
static lbool solver_search(solver* s, int nof_conflicts, int nof_learnts)
{
	int*    levels = s->levels;
	// INVERSE(�෴��) decay(����) factor for variable activity: stores 1/decay. 
	double  var_decay = 0.95;     
	//����ǰ���ʱ�䷢�����ֵ��0.99��ʱ����ڿ��������������ʱ����һ�������
	//���ǲ�֪���ǲ��Ե�����̫�ٵ�Ե��
	//double var_decay = 0.99;

	double  clause_decay = 0.999;
	//��Ϊ����������random_var_freq��ֵ���ж��������ѡ�����ָ�ֵ�����ǲ���VSIDS����
	double  random_var_freq = 0.02;
	//double  random_var_freq = 0.05;    //���ֵ�øı���Ҫ����Ĳ�������

	int     conflictC = 0;               //��¼��ͻ�Ӿ�ĸ���
	veci    learnt_clause;               //��¼ѧϰ�Ӿ�

	assert(s->root_level == solver_dlevel(s));

	s->stats.starts++;                          //���������������Ĵ�����1
	s->var_decay = (float)(1 / var_decay);      //���������Ĵ�С
	s->cla_decay = (float)(1 / clause_decay);   //�Ӿ������Ĵ�С 
	veci_resize(&s->model, 0);                  //model�д�ŵ��ǽ� ����Ĵ�С����0
	veci_new(&learnt_clause);                  //Ϊ�µ�ѧϰ�Ӿ�������Ӧ�Ŀռ�

	for (;;){    //����ѭ�� ѡ�����ָ�ֵ����BCP�Ĺ��� ֱ����ͻ�Ĳ����������е����ֶ��Ѿ���ֵ ���������
		clause* confl = solver_propagate(s);               //ͨ������solver����s�Ĵ��������õ���ͻ����ֵ��confl
		if (confl != 0){                                   //��confl��Ϊ�յ�ʱ���ʾ�����˳�ͻ ��Ҫ�ҵ����ݵĲ���
			// CONFLICT
			int blevel;                                     //�����洢���ݵĲ���

#ifdef VERBOSEDEBUG
			printf(L_IND"**CONFLICT**\n", L_ind);
#endif
			s->stats.conflicts++; conflictC++;           //��ͻ���Ӿ����Ŀ��1 ���ҳ�ͻ��������1
			if (solver_dlevel(s) == s->root_level){      //��������ĳ�ͻ���ڶ���� ���߲���
				veci_delete(&learnt_clause);            //ɾ��ǰ�������ѧϰ�Ӿ�
				return l_False;                         //�����ڸò�������ǲ���
			}
			//�����˳�ͻ �������ڵľ��߲������Ǹ���

			veci_resize(&learnt_clause, 0);              //��ǰ�������ѧϰ�Ӿ����ռ�
	        //����������ͻ��ԭ�� ����������ѧϰ�Ӿ丳ֵ��learnt_clause
			solver_analyze(s, confl, &learnt_clause);  
			//�ҵ�Ҫ���ݵĲ���
			blevel = veci_size(&learnt_clause) > 1 ? levels[lit_var(veci_begin(&learnt_clause)[1])] : s->root_level;
			//���Ҫ���ݵ���һ���root_level��С ��ô������¿�ʼ���� 
			//��ѧϰ�Ӿ��еĵ�һ����������Ӧ�Ĳ����ǵ��³�ͻ���������ֵ�����
			blevel = s->root_level > blevel ? s->root_level : blevel;
			//ȡ���ڸò�֮ǰ�����б����ĸ�ֵ
			solver_canceluntil(s, blevel);
			//��������ѧϰ�Ӿ���뵽�Ӿ伯����ȥ
			solver_record(s, &learnt_clause);
			//�����˳�ͻ֮�� ��Ҫ���±������Ӿ�Ļ�� �����´ν��б�����ѡ��ֵ
			act_var_decay(s);
			act_clause_decay(s);

		}
		else{
			// NO CONFLICT       confl��ֵΪ�� �Ǿ�����BCP�����Ĺ�����û��������ͻ
			//��ѡ�������һ���������и�ֵ Ȼ�����BCP�Ĺ���
			//��Ȼ��ѡ���������֮ǰ �ῼ��һЩ�����Ƿ������� ������Ӧ�Ĵ���
			int next;

			if (nof_conflicts >= 0 && conflictC >= nof_conflicts){  
				//��ͻ�Ӿ�ĸ�������0 �����Ĺ����в����ĳ�ͻ�Ӿ�ĸ�����������ĳ�ͻ�Ӿ���� conflictC �ڴ����Ĺ����в����ĳ�ͻ�Ӿ����
				// Reached bound on number of conflicts: �ﵽ�˳�ͻ�Ӿ�ķ�Χ �����涨һ����Χ
			
				s->progress_estimate = solver_progress(s); 
				//ȡ���ڸ�����ǰ�ı�����ֵ    �������ĳ�ͻ�Ӿ����̫�� 
				solver_canceluntil(s, s->root_level);
				//ɾ��ǰ�������ѧϰ�Ӿ�
				veci_delete(&learnt_clause);
				//���ﵽ����涨�ĳ�ͻ�Ӿ�ķ�Χ��ʱ�� ��������������Ի���֪�� 
				return l_Undef;
			}
			
			if (solver_dlevel(s) == 0)   //��������Ĺ����лص����� ��ô��Ҫ����һ�������Ӿ�
				// Simplify the set of problem clauses:
				solver_simplify(s);         

			//�������ѧϰ�Ӿ� �����ڴ����Ĺ����в�����ѧϰ�Ӿ�ĸ������������ѧϰ�Ӿ����
			//Ҳ���ǲ�����ѧϰ�Ӿ�ĸ������ڳ�����ƹ涨��ѧϰ�Ӿ�ķ�Χ��ʱ�� ��������ѧϰ�Ӿ�ĸ���
			if (nof_learnts >= 0 && vecp_size(&s->learnts) - s->qtail >= nof_learnts)
				// Reduce the set of learnt clauses:
				solver_reducedb(s);          

			//���ڴ����Ĺ�����û�в�����ͻ�Ӿ䲢��û�дﵽ�������趨���Ӿ䷶Χ �����ѡ�������һ���������о��߹���
			// New variable decision:
			s->stats.decisions++;             //�����߹��̵Ĵ�����1
			next = order_select(s, (float)random_var_freq);              //ѡ��һ������ �����ж�ѡ�����������Ƿ�ֵ

			if (next == var_Undef){                //���ѡ��ı�����û�и�ֵ
				// Model found:  �ҵ����ˣ�
				lbool* values = s->assigns;        //���Ѿ���ֵ�ı����ļ��ϸ�ֵ��values
				int i;
				//model�Ǵ洢���Ľ������
				//values[]�д�ŵ����Ѿ���ֵ�����ֵļ���
				for (i = 0; i < s->size; i++) veci_push(&s->model, (int)values[i]);    //���Ѿ���ֵ�ı������뵽veci���͵�model֮��
				//ΪʲôҪ���ڸ�����ǰ��ֵ�ı���ȡ���أ������������˼�������Ѿ��ǿ��������
				solver_canceluntil(s, s->root_level);  
				//ɾ��ǰ�������ѧϰ�Ӿ�
				veci_delete(&learnt_clause);

				/*
				veci apa; veci_new(&apa);
				for (i = 0; i < s->size; i++)
				veci_push(&apa,(int)(s->model.ptr[i] == l_True ? toLit(i) : lit_neg(toLit(i))));
				printf("model: "); printlits((lit*)apa.ptr, (lit*)apa.ptr + veci_size(&apa)); printf("\n");
				veci_delete(&apa);
		        */

				return l_True;                  //���������ǿ������
			}

			assume(s, lit_neg(toLit(next)));            //��ѡ��ı������м��踳ֵ ������һ�εĵ�Ԫ����
		}
	}

	return l_Undef; // cannot happen   ���ڴ������޵�forѭ�� ����ֻ����forѭ���з��� �����������ﷵ��
}

//=================================================================================================
// External solver functions:

//�½�һ��solver����
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

	s->stats.starts = 0;              //��������
	s->stats.decisions = 0;           //���ߴ���
	s->stats.propagations = 0;        //��������
	s->stats.inspects = 0;            //��� ������
	s->stats.conflicts = 0;           //��ͻ�Ӿ�ĸ���
	s->stats.clauses = 0;             //�ܵ��Ӿ�ĸ���
	s->stats.clauses_literals = 0;    //�ܵ��Ӿ��б����ĸ���
	s->stats.learnts = 0;             //ѧϰ�Ӿ�ĸ���
	s->stats.learnts_literals = 0;    //ѧϰ�Ӿ��б����ĸ���
	s->stats.max_literals = 0;        //�����ı����ĸ���ô��
	s->stats.tot_literals = 0;        //���ܵı����ĸ���ô��

	return s;
}


//ɾ��һ��solver����
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

//��������м����Ӿ�ĺ���
bool solver_addclause(solver* s, lit* begin, lit* end)
{
	lit *i, *j;
	int maxvar;                //���ڴ洢���ı���
	lbool* values;
	lit last;

	if (begin == end) return false;  //������ı���������Ϊ0��ʱ�� �˳�

	//printlits(begin,end); printf("\n");
	// insertion sort  ��������
	//�����maxvar����С��������һ���Ӿ��е����ֵ  �ڸտ�ʼ�����ݵĴ����ʱ�� �Ӿ��е����ֱ�����������
	maxvar = lit_var(*begin);                   //����һ��������ֵ��ֵ��maxvar  

	//���Ҳ�ü�һ��������ݵĺ��� �������ܱ�֤���Ӿ�����е��������
	//printf("%d\n",maxvar);

	//�����Ƕ�һ���Ӿ���д��� ÿ���Ӿ�����0��Ϊ�����ı�־��
	for (i = begin + 1; i < end; i++){
		lit l = *i;
		//�������Լ������������ݵ���� ֻ�ǲ��ԵĹ���
		//printf("%d\n",l);
		maxvar = lit_var(l) > maxvar ? lit_var(l) : maxvar;    //�õ����ı���
		for (j = i; j > begin && *(j - 1) > l; j--)
			*j = *(j - 1);
		*j = l;
	}
	solver_setnvars(s, maxvar + 1);         //��ÿһ���Ӿ�����maxvar+1�������ı����ռ� 

	//printlits(begin,end); printf("\n");
	values = s->assigns;                   //�õ����еı����ĸ�ֵ״�� ����δ��ֵ ��Ϊ0
	
	
	// delete duplicates  ɾ������
	last = lit_Undef;               //last��ֵΪ0
	//ͨ��forѭ���ж�һ��Ҫ������Ӿ��Ƿ��Ǻ����Ӿ�
	for (i = j = begin; i < end; i++){ 
		//printf("lit: "L_LIT", value = %d\n", L_lit(*i), (lit_sign(*i) ? -values[lit_var(*i)] : values[lit_var(*i)]));
		//�ھ���lit_sign()�ı任�Ժ� sig��ֵֻ��0��1 
		//������������Լ�����Ĵ���
		//printf("%d\n", *i);
		//lbool tem = !lit_sign(*i);
		//printf("%d\n",tem);

		lbool sig = !lit_sign(*i); sig += sig - 1;

		//�������Լ�����Ĵ������sig��ֵ sig�����ֻ��1��-1�������
		//printf("%d\n",sig);
		//printf("%d\n", lit_neg(last));

		//���������Ӿ䱾�����һ�����к������ʵ��Ӿ� ��ô���Է���true��
		//�������Լ����������if�����ȷִ�еĸ��ʲ��Ǻܴ�
		if (*i == lit_neg(last) || sig == values[lit_var(*i)])  //�������ı�����ֵΪ�� �������ķ�Ϊ��
			return true;   // tautology  ͬ�巴��
		//���������Ӿ�ı�������û�и�ֵ
		else if (*i != last && values[lit_var(*i)] == l_Undef)
			last = *j++ = *i;      //��������ֵ��last
	}

	//printf("final: "); printlits(begin,j); printf("\n");

	if (j == begin)          // empty clause   jָ��һֱû�� �����ǿ��Ӿ�
		return false;
	else if (j - begin == 1) // unit clause
		return enqueue(s, *begin, (clause*)0);         //����Ԫ�Ӿ�ı����Ӿ���봫���Ķ���

	// create new clause
	//�տ�ʼ������Ӿ����־λlearntΪ0
	vecp_push(&s->clauses, clause_new(s, begin, j, 0));



	s->stats.clauses++;       //�Ӿ�ĸ�����1
	s->stats.clauses_literals += j - begin;      //�Ӿ�ı�����������j-begin��ô���

	return true;           //���ش����µ��Ӿ�ɹ�
}

/*
top-level simplify  of constraint database. �Ӷ��㿪ʼ����һ�������Ӿ�
will remove any satisfied constraint and simplify remianing constraint under(partial �ֲ���) assignment 
if a top-level conflict is found FALSE is returned
ǰ������ decision level must be zero  �������� propagation queue is empty

Simplify the clause database according to the current top-level assigment. Currently, the only
thing done here is the removal of satisfied clauses, but more things can be put here.
*/
bool   solver_simplify(solver* s)
{
	clause** reasons;
	int type;

	assert(solver_dlevel(s) == 0);    //Ҫ�����Ӿ� ����ñ�֤�ڸ��ڵ��ʱ��

	//�ڴ����Ĺ����в����˳�ͻ ��ô�Ϳ���ͨ����ͻ�Ӿ�ѧϰ ����
	if (solver_propagate(s) != 0)     
		return false;

	//int simpdb_assigns: Number of top-level assignments at last 'simplifyDB()' �����Ӿ伯��
	//int simpdb_props��Number of propagations before next 'simplifyDB()'
	//�������Ĵ�������0 ���� �ڶ���ĸ�ֵ�ı����ĸ�����s->qhead��ȵ�ʱ��
	if (s->qhead == s->simpdb_assigns || s->simpdb_props > 0)   
		return true;

	// Remove satisfied clauses:
	//�ڴ����Ĺ�����û�д����ʱ�� �ͻ���ֿ�������Ӿ�
	reasons = s->reasons;   //���̺�������ֵ��ԭ���Ӿ丳ֵ��reasons
	for (type = 0; type < 2; type++){
		vecp*    cs = type ? &s->learnts : &s->clauses;  //�ȶ�ԭʼ���Ӿ伯�ϴ��� �ٶ�ѧϰ�Ӿ������Ӧ�Ĵ���
		clause** cls = (clause**)vecp_begin(cs);

		int i, j;
		for (j = i = 0; i < vecp_size(cs); i++){
			//����Ӿ䲻�ǵ��±����̺���ֵ��ԭ���Ӿ䲢�Ҹ��Ӿ��ǿ������ ��ô��Ҫ�����Ӿ�ɾ�� 
			if (reasons[lit_var(*clause_begin(cls[i]))] != cls[i] &&
				clause_simplify(s, cls[i]) == l_True)
				clause_remove(s, cls[i]);
			else
				cls[j++] = cls[i];      //��cls[i]��ֵ��cls[j] ���Ҷ���һ���Ӿ���д���
		}
		vecp_resize(cs, j);     //�����е��Ӿ䶼��������Ժ� ���Ӿ�ĳ��Ƚ������µ��ж�
	}

	s->simpdb_assigns = s->qhead;
	// (shouldn't depend on 'stats' really, but it will do for now)
	s->simpdb_props = (int)(s->stats.clauses_literals + s->stats.learnts_literals);

	return true;
}



//�������������
/*
main solve method 
ǰ������ if assumptions are used simplify() must be called right before using this method .
if not ,a top-level conflict(resulting in a non-usable internal state) 
connot be distinguished from a conflict under assumption 
*/
bool   solver_solve(solver* s, lit* begin, lit* end)
{
	double  nof_conflicts = 100;        //���ó�ͻ�Ӿ��һ����Χ100
	double  nof_learnts = solver_nclauses(s) / 3;        //����ѧϰ�Ӿ�ķ�ΧΪ�Ӿ����Ŀ������֮һ
	lbool   status = l_Undef;                          //���״̬
	lbool*  values = s->assigns;        //���Ѿ���ֵ�ı�����ֵ��ֵ��values �տ�ʼ��ʱ��϶�Ϊ��
	lit*    i;

	//������ע���˵Ĵ��� �򿪿��� 
	printf("solve: "); printlits(begin, end); printf("\n");
	//��ÿ���Ӿ�����ж�
	for (i = begin; i < end; i++){
		//�ж�һ��*i��ֵ ���Ϊ������ ��lit_sign(*i)Ϊ1
		switch (lit_sign(*i) ? -values[lit_var(*i)] : values[lit_var(*i)]){
		case 1: /* l_True: */
			break;                      //���ֵΪ1 ���ǿ������ ����switch
		case 0: /* l_Undef */
			assume(s, *i);             //�����û�жԱ������и�ֵ ��ô�Ա������и�ֵȻ��BCP����
			if (solver_propagate(s) == NULL)
				break;
			// falltrough
		case -1: /* l_False */               //�����ֵΪ�ٵ����
			solver_canceluntil(s, 0);        //ȡ����0����ǰ�ĸ�ֵ ���¿�ʼ�����Ĺ���
			return false;
		}
	}

	s->root_level = solver_dlevel(s);   

	//verbosity��ֵΪ0����û�н������Ĺ���
	if (s->verbosity >= 1){             //���verbosity���ڵ���1ʱ �����ڽ��д����Ĺ��� ����һЩ����
		printf("==================================[MINISAT]===================================\n");
		printf("| Conflicts |     ORIGINAL     |              LEARNT              |         \n");  //ɾ��Progress
		printf("|           | Clauses Literals |   Limit Clauses Literals  Lit/Cl |         \n");
		printf("==============================================================================\n");
	}

	while (status == l_Undef){    //���״̬û�ж���Ļ�  ��Ȼ��ǰ��ȷʵ��1_Undef
		double Ratio = (s->stats.learnts == 0) ? 0.0 :      //�õ����� ѧϰ�Ӿ��еı����ĸ�����ѧϰ�Ӿ�����ı���
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
		//ѡ�����ֽ��м��踳ֵ��Լ������BCP ֱ�������˳�ͻ���ߵõ������ǿ������
		status = solver_search(s, (int)nof_conflicts, (int)nof_learnts);    
		nof_conflicts *= 1.5;       //�������ó�ͻ�Ӿ�ķ�Χ   �����˳�ͻ�Ӿ�ķ�Χ
		nof_learnts *= 1.1;         //����ѧϰ�Ӿ�ķ�Χ   ������ѧϰ�Ӿ�ķ�Χ
	}
	if (s->verbosity >= 1)   //�����˳�ͻ ȡ����ǰ��һЩ��ֵ �������Ƿ��ǲ��������
		printf("==============================================================================\n");

	solver_canceluntil(s, 0);        //ȡ����ǰ�ĸ�ֵ���
	return status != l_False;
}


//�õ�solver����ı����ĸ���
int solver_nvars(solver* s)
{
	return s->size;
}


//�õ�solver������Ӿ�ĸ���
int solver_nclauses(solver* s)
{
	return vecp_size(&s->clauses);
}


//�õ�solver����ĳ�ͻ�Ӿ�ĸ���
int solver_nconflicts(solver* s)
{
	return (int)s->stats.conflicts;
}

//=================================================================================================
// Sorting functions (sigh):

//��������������ѡ�������㷨
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

//����ѡ��������
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
