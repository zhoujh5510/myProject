#include "solver.h"

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
using namespace std;

#define _CRT_SECURE_NO_WARNINGS
int currentCap = 0;
int currentSize = 0 ;

//下面是自己实验的代码,加油！
//从文件中读入数据
char* readFile(FILE *in)
{
	char* data = (char*)malloc(65536); 
	int cap = 65536;                  //65536是2的16次方
	int size = 0;
	
	while (!feof(in)){
		//下面的if条件中int的范围是到65535，cap的值为65536
		if (size == cap){ 
			cap *= 2;
			data = (char*)realloc(data,cap);
		}
		size += fread(&data[size],1,65536,in);
	}
		data = (char*)realloc(data,size+1);
		data[size] = '\0'; //最后赋值一个换行符给该字符数组
		currentCap = cap;
		currentSize = size;
	    return data;
}


/* 下面的函数是自己写的识别空格符的函数
void skipWhitespace(char** in){
	while( **in != ' '){
		printf("%s\n",*in);
		(*in)++;
		printf("next\n");
	}
	(*in)++;
	currentSize--;
}*/

//但是程序的意思是在读入的过程中如果读入到了空白符的时候就跳过,所以还是得按照原程序来
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


//下面的函数是将文件中读入的范式转换成整数
//而且我觉得只是转换范式中的一个变量？
int parseInt(char** in){
    int val = 0;
	int _neg = 0;
	skipWhitespace(in);  //看是否是空白符
	if (**in == '-')
	{ 
		_neg = 1;          
		(*in)++;    //如果是否定范式 指针后移一位
	}
	else if(**in == '+') 
	{ 
		(*in)++;
	}
	//读入的数据不是0到9就报错,但是这表明程序读取文件的时候里面的只有数字,不会是字符
	if(**in < '0' && **in > '9') 
	{
		fprintf(stderr,"PARSE ERROR! Unexpected char: %c\n",**in);
		exit(1);
	}
	//文件读入的都是数字,那么就对其进行处理
	while (**in >= '0' && **in <= '9')
	{
		val = val*10 +(**in - '0');
		(*in)++;
		//printf("%c\n",**in);
	}
	//如果是负文字,其相应的转换过来的整数的值也为负
	return _neg ? -val : val;
}


/*
**readClause函数是从文件中读取一个子句,子句以0作为结束元素
*/
static void readClause(char** in, solver* s, veci* lits) {
    int parsed_lit, var;
    veci_resize(lits,0);     //先将lits这个向量的size置为0
    for (;;){
        parsed_lit = parseInt(in);    //读取文件中的数据,并将文件中的字符转换为整数
        if (parsed_lit == 0) break;   
        var = abs(parsed_lit)-1;      //将转换后的整数的值相应的减1
		//将转换后得到的变量的值压入向量之中
        veci_push(lits, (parsed_lit > 0 ? toLit(var) : lit_neg(toLit(var))));
    }
}

/*
**下面的函数的功能:
**输入:数据流 求解器对象
**输出:子句是否成功加入到求解器中 是否正确的化简 lbool是一个字符
**通过从文件数据流中读入数据，将其加入到求解器中 并化简求解器中的子句
*/
static lbool parse_DIMACS_main(char* in, solver* s) {
    veci lits;
    veci_new(&lits);      //先初始化一个veci实例

    for (;;){
        skipWhitespace(&in);      //先跳过读入数据的空白符号
        if (*in == 0)             //如果读入的数据是0那么就跳出for循环,进行下一步的操作
            break;
        else if (*in == 'c' || *in == 'p')         //要求文件的输入形式以字符c或者字符p作为开头 c代表是注释 跟随的p字符表示输入的是cnf范式
            skipLine(&in);                         //这两行的内容都没有什么意义,所以可以直接跳过
        else{
            lit* begin;                            
            readClause(&in, s, &lits);           //从输入的数据流中读取一行 也就是一个子句 并将其存入一个向量中
            begin = veci_begin(&lits);           //int类型的begin指针指向存入子句的向量的第一个元素
            if (!solver_addclause(s, begin, begin+veci_size(&lits))){      //将存入子句的向量加入到solver求解器s中去
				//begin+veci_size(&lits)得到的存入子句的向量的整个大小 begin是子句的lits中存入的子句的开始指针
                veci_delete(&lits);         //如果将子句向量加入到求解器中的时候出错 则删除该函数中定义的子句向量
                return l_False;             //返回不可满足 或者在读取文件数据流的时候出错
            }
        }
    }
    veci_delete(&lits);                     //正确的将子句读入solver中的时候,也得删除函数中定义的临时的向量
    return solver_simplify(s);              //调用simplify函数化简求解器中的子句
}


// Inserts problem into solver. Returns FALSE upon immediate conflict.
//
//从文件中读入子句 并将其读入求解器中
static lbool parse_DIMACS(FILE * in, solver* s) {
    char* text = readFile(in);             //从文件in读入数据
    lbool ret  = parse_DIMACS_main(text, s);        //将其读入solver实例对象中
    free(text);                                     
    return ret; }


//=================================================================================================

//输出运行结果的一些信息
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
**当得到SAT问题的一个解以后还希望获得另外的一些解
**那么只需要将得到的解作为子句从新加入到原子聚集合中
**作为约束子句,再运行程序就会得到其他的解了
*/

int main(int argc,char* argv[])
{
	FILE *in;                      //定义的一个文件对象
	FILE *out1;
	solver* s = solver_new();      //生成一个solver对象的实例
	lbool st;                      //定义一个字符st lbool为字符类型
	int clk = clock();             //定义一个时钟对象 相当于开始计时了


	//char* readData = NULL;
	//int parseint;
	//打开输出结果的文件
	if ((out1 = fopen("E:\\lab\\result.txt", "at+")) == NULL)
	{
		printf("cannot open file result.txt!");
	}


	if((in =fopen("E:\\lab\\c3540.cnf","r"))==NULL){         //打开文件
		printf("cannot open file data.txt!");
	} else {
		st = parse_DIMACS(in,s);          //调用该函数 从文件中读入子句 并将其加入到solver求解器中
	}
	fclose(in);                           //关闭文件 


	//printf("%s\n",readData);
	//printf("CurrentCap is: %d\n",currentCap);
	//printf("CurrentSize is: %d\n",currentSize);
	//skipWhitespace(&readData);
	//当执行完了skipLine函数以后,文件中的指针就会移动到下一行的开始处
	//skipLine(&readData);     
	//printf("%s\n",readData);
	//printf("CurrentSize is: %d\n",currentSize);
	//parseint = parseInt(&readData);
	//printf("%d\n",parseint);

	if(st == l_False)             //从文件中读取子句到solver中的时候出现了错误 则进行相应的处理
	{
	     solver_delete(s);           //删除solver对象
	     printf("Trivial problem\nUNSATISFIABLE\n");        //输出提示信息
         exit(20);
	}

	 s->verbosity = 1;

	 st = solver_solve(s,0,0);
     printStats(&s->stats, clock() - clk);         //输出求解的状态
     printf("\n");
     printf(st == l_True ? "SATISFIABLE\n" : "UNSATISFIABLE\n");

    // print the sat assignment
	 //如果是可满足的,输出一个解
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