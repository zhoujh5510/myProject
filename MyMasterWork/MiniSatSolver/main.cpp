#include "solver.h"

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
using namespace std;

#define _CRT_SECURE_NO_WARNINGS
int currentCap = 0;
int currentSize = 0 ;

//�������Լ�ʵ��Ĵ���,���ͣ�
//���ļ��ж�������
char* readFile(FILE *in)
{
	char* data = (char*)malloc(65536); 
	int cap = 65536;                  //65536��2��16�η�
	int size = 0;
	
	while (!feof(in)){
		//�����if������int�ķ�Χ�ǵ�65535��cap��ֵΪ65536
		if (size == cap){ 
			cap *= 2;
			data = (char*)realloc(data,cap);
		}
		size += fread(&data[size],1,65536,in);
	}
		data = (char*)realloc(data,size+1);
		data[size] = '\0'; //���ֵһ�����з������ַ�����
		currentCap = cap;
		currentSize = size;
	    return data;
}


/* ����ĺ������Լ�д��ʶ��ո���ĺ���
void skipWhitespace(char** in){
	while( **in != ' '){
		printf("%s\n",*in);
		(*in)++;
		printf("next\n");
	}
	(*in)++;
	currentSize--;
}*/

//���ǳ������˼���ڶ���Ĺ�����������뵽�˿հ׷���ʱ�������,���Ի��ǵð���ԭ������
void skipWhitespace(char** in){
	while((**in >= 9 && **in <=13) || **in == 32){
	     (*in)++;
	}
}

void skipLine(char** in){
    for(;;){
	   if(**in == 0) return;
	   if(**in == '\n'){ (*in)++;   return ;}
	   (*in)++;
	}
}


//����ĺ����ǽ��ļ��ж���ķ�ʽת��������
//�����Ҿ���ֻ��ת����ʽ�е�һ��������
int parseInt(char** in){
    int val = 0;
	int _neg = 0;
	skipWhitespace(in);  //���Ƿ��ǿհ׷�
	if (**in == '-')
	{ 
		_neg = 1;          
		(*in)++;    //����Ƿ񶨷�ʽ ָ�����һλ
	}
	else if(**in == '+') 
	{ 
		(*in)++;
	}
	//��������ݲ���0��9�ͱ���,��������������ȡ�ļ���ʱ�������ֻ������,�������ַ�
	if(**in < '0' && **in > '9') 
	{
		fprintf(stderr,"PARSE ERROR! Unexpected char: %c\n",**in);
		exit(1);
	}
	//�ļ�����Ķ�������,��ô�Ͷ�����д���
	while (**in >= '0' && **in <= '9')
	{
		val = val*10 +(**in - '0');
		(*in)++;
		//printf("%c\n",**in);
	}
	//����Ǹ�����,����Ӧ��ת��������������ֵҲΪ��
	return _neg ? -val : val;
}


/*
**readClause�����Ǵ��ļ��ж�ȡһ���Ӿ�,�Ӿ���0��Ϊ����Ԫ��
*/
static void readClause(char** in, solver* s, veci* lits) {
    int parsed_lit, var;
    veci_resize(lits,0);     //�Ƚ�lits���������size��Ϊ0
    for (;;){
        parsed_lit = parseInt(in);    //��ȡ�ļ��е�����,�����ļ��е��ַ�ת��Ϊ����
        if (parsed_lit == 0) break;   
        var = abs(parsed_lit)-1;      //��ת�����������ֵ��Ӧ�ļ�1
		//��ת����õ��ı�����ֵѹ������֮��
        veci_push(lits, (parsed_lit > 0 ? toLit(var) : lit_neg(toLit(var))));
    }
}

/*
**����ĺ����Ĺ���:
**����:������ ���������
**���:�Ӿ��Ƿ�ɹ����뵽������� �Ƿ���ȷ�Ļ��� lbool��һ���ַ�
**ͨ�����ļ��������ж������ݣ�������뵽������� ������������е��Ӿ�
*/
static lbool parse_DIMACS_main(char* in, solver* s) {
    veci lits;
    veci_new(&lits);      //�ȳ�ʼ��һ��veciʵ��

    for (;;){
        skipWhitespace(&in);      //�������������ݵĿհ׷���
        if (*in == 0)             //��������������0��ô������forѭ��,������һ���Ĳ���
            break;
        else if (*in == 'c' || *in == 'p')         //Ҫ���ļ���������ʽ���ַ�c�����ַ�p��Ϊ��ͷ c������ע�� �����p�ַ���ʾ�������cnf��ʽ
            skipLine(&in);                         //�����е����ݶ�û��ʲô����,���Կ���ֱ������
        else{
            lit* begin;                            
            readClause(&in, s, &lits);           //��������������ж�ȡһ�� Ҳ����һ���Ӿ� ���������һ��������
            begin = veci_begin(&lits);           //int���͵�beginָ��ָ������Ӿ�������ĵ�һ��Ԫ��
            if (!solver_addclause(s, begin, begin+veci_size(&lits))){      //�������Ӿ���������뵽solver�����s��ȥ
				//begin+veci_size(&lits)�õ��Ĵ����Ӿ��������������С begin���Ӿ��lits�д�����Ӿ�Ŀ�ʼָ��
                veci_delete(&lits);         //������Ӿ��������뵽������е�ʱ����� ��ɾ���ú����ж�����Ӿ�����
                return l_False;             //���ز������� �����ڶ�ȡ�ļ���������ʱ�����
            }
        }
    }
    veci_delete(&lits);                     //��ȷ�Ľ��Ӿ����solver�е�ʱ��,Ҳ��ɾ�������ж������ʱ������
    return solver_simplify(s);              //����simplify��������������е��Ӿ�
}


// Inserts problem into solver. Returns FALSE upon immediate conflict.
//
//���ļ��ж����Ӿ� ����������������
static lbool parse_DIMACS(FILE * in, solver* s) {
    char* text = readFile(in);             //���ļ�in��������
    lbool ret  = parse_DIMACS_main(text, s);        //�������solverʵ��������
    free(text);                                     
    return ret; }


//=================================================================================================

//������н����һЩ��Ϣ
void printStats(stats* stats, int cpu_time)
{
    double Time    = (float)(cpu_time)/(float)(CLOCKS_PER_SEC);
    printf("restarts          : %12d\n", stats->starts);
    printf("conflicts         : %12.0f           (%9.0f / sec      )\n",  (double)stats->conflicts   , (double)stats->conflicts   /Time);
    printf("decisions         : %12.0f           (%9.0f / sec      )\n",  (double)stats->decisions   , (double)stats->decisions   /Time);
    printf("propagations      : %12.0f           (%9.0f / sec      )\n",  (double)stats->propagations, (double)stats->propagations/Time);
    printf("inspects          : %12.0f           (%9.0f / sec      )\n",  (double)stats->inspects    , (double)stats->inspects    /Time);
    printf("conflict literals : %12.0f           (%9.2f %% deleted  )\n", (double)stats->tot_literals, (double)(stats->max_literals - stats->tot_literals) * 100.0 / (double)stats->max_literals);
    printf("\n");
	printf("CPU time          : %12.2f sec\n", Time);
}

//solver* slv;
//static void SIGINT_handler(int signum) {
//    printf("\n"); printf("*** INTERRUPTED ***\n");
//    printStats(&slv->stats, cpuTime());
//    printf("\n"); printf("*** INTERRUPTED ***\n");
//    exit(0); }


//=================================================================================================



/*
**���õ�SAT�����һ�����Ժ�ϣ����������һЩ��
**��ôֻ��Ҫ���õ��Ľ���Ϊ�Ӿ���¼��뵽ԭ�Ӿۼ�����
**��ΪԼ���Ӿ�,�����г���ͻ�õ������Ľ���
*/

int main(int argc,char* argv[])
{
	FILE *in;                      //�����һ���ļ�����
	FILE *out1;
	solver* s = solver_new();      //����һ��solver�����ʵ��
	lbool st;                      //����һ���ַ�st lboolΪ�ַ�����
	int clk = clock();             //����һ��ʱ�Ӷ��� �൱�ڿ�ʼ��ʱ��


	//char* readData = NULL;
	//int parseint;
	//�����������ļ�
	if ((out1 = fopen("E:\\lab\\result.txt", "at+")) == NULL)
	{
		printf("cannot open file result.txt!");
	}


	if((in =fopen("E:\\lab\\c3540.cnf","r"))==NULL){         //���ļ�
		printf("cannot open file data.txt!");
	} else {
		st = parse_DIMACS(in,s);          //���øú��� ���ļ��ж����Ӿ� ��������뵽solver�������
	}
	fclose(in);                           //�ر��ļ� 


	//printf("%s\n",readData);
	//printf("CurrentCap is: %d\n",currentCap);
	//printf("CurrentSize is: %d\n",currentSize);
	//skipWhitespace(&readData);
	//��ִ������skipLine�����Ժ�,�ļ��е�ָ��ͻ��ƶ�����һ�еĿ�ʼ��
	//skipLine(&readData);     
	//printf("%s\n",readData);
	//printf("CurrentSize is: %d\n",currentSize);
	//parseint = parseInt(&readData);
	//printf("%d\n",parseint);

	if(st == l_False)             //���ļ��ж�ȡ�Ӿ䵽solver�е�ʱ������˴��� �������Ӧ�Ĵ���
	{
	     solver_delete(s);           //ɾ��solver����
	     printf("Trivial problem\nUNSATISFIABLE\n");        //�����ʾ��Ϣ
         exit(20);
	}

	 s->verbosity = 1;

	 st = solver_solve(s,0,0);
     printStats(&s->stats, clock() - clk);         //�������״̬
     printf("\n");
     printf(st == l_True ? "SATISFIABLE\n" : "UNSATISFIABLE\n");

    // print the sat assignment
	 //����ǿ������,���һ����
    if ( st == l_True )
    {
        int k;
        printf( "\nSatisfying solution: " );
		for (k = 0; k < s->model.size; k++)
		{
			printf("x%d=%d ", k, s->model.ptr[k] == l_True);
			fprintf(out1, "x%d=%d \n", k+1, s->model.ptr[k] == l_True);
		}
        printf( "\n" );
    }

    solver_delete(s);

	system("pause");
	return 0;
}