/*
**@author:周建华
**function:基于枚举树的层次遍历实现模型诊断算法
**date:2015-8-26
**version 2.0
*/

#include <set>
#include <vector>
#include <algorithm>
#include <iostream>
#include "picosat.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <assert.h>
using namespace std;

//these two h files are for linux
#include <sys/times.h> 
#include <unistd.h>

//define time
 struct tms tmsstart,tmsend,tmscmp1,tmscmp2;
clock_t start_time,end_time,real;


//varibles
int num_vars;
int num_clauses;
int num_comp;
PicoSAT *picosat;



//variable used in program
int seq[100];                                  
int unitMax;
int lastIndex;
int MAX;                                   
int com;                                   //the number of component
int DigLen;                                //The minimal Diagnosis length
int everyLevIndex[20];
int sat_count;
set< set<int> > slt;                    //store the solutions of diagnosis
set<int> tempset;                     //use it to store temple set


/* ***************************************************************************** */
/*
* read cnf file
* init PicoSAT
* para: filename
*/

void readfile(char *filename)
{
	assert(filename != NULL);
    FILE   *fp;
    char   *tempstr;
    char   tempstr1[10];
    char   tempstr2[10];
    char   line[100];
    int    i;
    int	   lit;
    int    temp;
    
    printf("cnf name : %s\n", filename);
    
    fp = fopen(filename, "r");
    if(fp==NULL) 
    {
		printf("Cannot find the input file. Make sure the filename is correct.\n");
		exit(0);
    }
	
    tempstr=fgets(line, 100, fp);
    while (line[0] != 'p')
	tempstr=fgets(line, 100, fp);
    sscanf(line, "%s %s %d %d %d", tempstr1, tempstr2, &num_vars, &num_clauses, &num_comp);	
    
    printf("vairable number : %d\n",num_vars); 
    printf("clause   number : %d\n",num_clauses); 
    printf("component number: %d\n",num_comp);
 

    //init picosat
    picosat=picosat_init();
    picosat_save_original_clauses (picosat);
    picosat_adjust (picosat, num_vars);
   
    //add cluases into Picosat
    for (i = 0; i < num_clauses; i++) 
    {
		temp = fscanf(fp, "%d", &lit);
		//printf("%d\n",lit);
		picosat_add(picosat,lit);
		while (lit != 0) {
		temp = fscanf(fp, "%d", &lit);
		//printf("%d\n",lit);
        picosat_add(picosat,lit);
      }
    }
    
//close file
    fclose(fp);
    
}



/*
* use picosat to solve 
* para: array of ps[]
* return: 0 or 1
*/
int usePicosat(int ps[]){                  
	int i;
    int j;
	int *pm;
	pm=&ps[0];
    MAX++;
    /*
	for(i = 0 ; i <= lastIndex; i++){
     if(ps[i])
		printf("%d   ",ps[i]);
    }
    printf("\n");
    */
    //printf("start\n");
	//printf("%d\n",Mcard);
        for(i = 0 ; i <= lastIndex; i++) 
         {
              if((ps[i] == 0))
                {
                     break;
                }
              else if(ps[i] != 0)
                {
					//printf("---%d---\n",ps[i]);
                    //printf("done!\n");
                    picosat_assume(picosat,ps[i]);
                }
         }
         //printf("end\n");
         for(j = 1 ; j <= com ; j++)
         {
              if( j == *pm)
				{
					pm++;
				}
				else
				{
					//printf("do!\n");
					picosat_assume(picosat,j*-1);
				}
         } 
	

        int digres = 0;
        digres = picosat_sat(picosat,-1);

        //use sat_count to remember the times of use PICOSAT
        sat_count = sat_count + 1;
        if(digres == 10) //SAT
        {
               return 1;
        }
        else if(digres == 20) //UNSAT
        {
               return 0;
        }        
}



/*-----------------------------------------------------------------------------*/
//construct and initialize
//inital unitMax lastIndex seq[]
void initial(int unitMax1)
{
		unitMax = unitMax1;
		lastIndex = -1;
                int i;
		for (i = 0; i<100; i++) 
        {
            seq[i] = 0;
        }
}

//return the length of seq[]
int length()
{
	return lastIndex + 1;
}


//print array of seq[]
void print()
{
		//if seq is only 0, then do nothing
		if (lastIndex<0){
			//cout << "0 " << endl;
            printf("\n");
			return;
		}
		
                int i;
                //printf("%d\n",lastIndex);
		for (i = 0; i <= lastIndex; i++){
			printf("%d  ",seq[i]);
		}
		printf("\n");
             
}



 /**
	state machine:
	According to the element indexed by currIndex,
	if the element hasn't reached its max, this element can be incremented,
	otherwise the former element should be accessed.
	The former situation is status 1, for instance number 126 while currIndex
	is 1, the later situation is status 2, for instance number 156 while currIndex
	is 1. And when some element is incremented, it is done, the status shifted to
	status 0, end.
	There is a special situation. Consider the current number is 56 while max is 6
	and the method incr is called. First, 6 is considered, status is set to 2, Second,
	5 is considered, status is set to 2 again, in the next loop, currIndex becomes -1
	and currMax becomes 4. In this situation the structure of the number is changed because
	the next number is 123. As a solution, seq[0] is set 0 and status is set to 1, and
	in the next loop it can be resolved.
 */

void incr()
{
		if (lastIndex == -1){
			seq[0] = 1;
			lastIndex = 0;
			return;
		}

		int currIndex = lastIndex;
		int currMax = unitMax;
		int status = 0;
		if (seq[currIndex]<currMax) status = 1;
		else status = 2;

		while (status){
			switch (status){
			case 1:
				seq[currIndex]++;
                                int i;
                                int unit;
				for (i = currIndex + 1, unit = seq[currIndex] + 1; i <= lastIndex; i++, unit++)
					seq[i] = unit;
				status = 0;
				break;
			case 2:
				currIndex--;
				currMax--;
				if (currIndex<0){                    // caution: currIndex might be -1
					currIndex = 0;
					seq[0] = 0;
					lastIndex++;
					status = 1;
				}
				else{
					if (seq[currIndex]<currMax) status = 1;
					else status = 2;
				}

				break;
			}
		}
}




/*---------------------------------------------------------------*/
/*
*when we know the number of component
*wo should know the range of solutionns
*/
/*
solve C(m,n) = (m!)/((n!)*(m-n)!)
(m!)/((n!)*(m-n)!) = (m*(m-1)*(m-2)*......*(m-n+2)*(m-n+1))/(n!)
=((m-n+1)/1)*((m-n+2)/2)*......*((m-n+n)/n)
= ∏((m-n+k)/k)[k=1,2,3,…,n]
*/
/*
parameter: m , n
return: C(m,n)
*/

int totalCom(int m,int n)
{
    int sum = 1;
    int k;
    for(k = 1; k <= n ; k++)
      {
           sum = (sum*(m-n+k))/k;   //xian suan chen fa , bi mian chu yi k chu bu jin
      }
    return sum;
}


/*
given n_com and level
return:C(n_com,1) + ...... + C(n_com,level)
*/
int num_node(int n_com,int level)
{
    int total = 0;
    int l ;
    for(l = 1; l <= level; l++)
     {
         total += totalCom(n_com,l);
     }
    return total;
}



/*
* store every level index in the array of everyLevIndex[]
* para: num_com means number of component 
        lev means 1 to DigLen
*/
void setEveryLevIndex(int num_com , int lev)
{
     int res;
     int i;
     for(i = 1; i <= lev; i++)
      {
           res = totalCom(num_com,i);
           everyLevIndex[i-1] = res;
      }
}

/*
* para: the name of array 
*/
void printArray(int arr[])
{
     int *p;
     p = &arr[0];

     while(*p != 0)
       {
            printf("%d ",*p);
            p++;
       }
     printf("\n");
}



/***********************************************************************/
/*
* the functions follows is used to solve the Dignosis solutions
*/
/*
* juge the set son is or not is the subset of set father
* para: father is the contain set
* para: son is sontained set
* return: if son is the suset of father return 1
* else return 0
*/
bool isSuperSet(set<int> &father, set<int> &son)
{
	assert(father.size() > 0 && son.size() > 0);
	vector<int> r(son.size());
	vector<int>::iterator it;
	it = set_intersection(father.begin(), father.end(), son.begin(), son.end(), r.begin());
	r.resize(it - r.begin());

        /*
	vector<int>::iterator iter = r.begin();
	cout << "r in isSuperSet:";
	while (iter!=r.end())
	{
		cout << *(iter++) << " ";
	}
	cout << endl;
        */     

	if (r.size() == son.size())
	{
		return 1;
	}
	else
	{
		return 0;
	}
}


/*
* juge set s is or not is the super set of anyone of set slt
* para: s is the set we think about
* para: slt is the set of set
* return: if s is the super set of anyone of set slt the return 1 
* means s is not the minimal solves
* else s is the solve we add it to slt and return 0 
*/
// 添加成功返回 0， 添加失败返回 1.
int addSet(set< set<int> > *slt, set<int> &s)
{
	assert(slt != NULL && s.size() > 0);
	if (slt->empty())
	{
		slt->insert(s);
		return 0;
	}

	set< set<int> >::iterator iter = slt->begin();
	while (iter!=slt->end())
	{
		if (s.size() != iter->size() && isSuperSet(s, *iter))
		{
			return 1;
		}
		iter++;
	}
	slt->insert(s);
	return 0;
	
}


/*
* given a Array of int , and the length of Array 
* return the format of set express
* para: Arrary and it's length
* return: the set of Array expression 
*/
set<int> generateSet(int arr[], int len)
{
	set<int> r;
	for (int i = 0; i < len; i++)
	{
		r.insert(arr[i]);
	}
	return r;
}



/*
* print the solves Dignosis
* para: set of slt
* return: NULL
*/
void printSlt(set< set<int> >* slt)
{
	assert(slt != NULL);
	set< set<int> >::iterator iter = slt->begin();
	set<int>::iterator it;
	while (iter != slt->end())
	{
		it = iter->begin();
		while (it != iter->end())
		{
			cout << *it++ << " ";
		}
		cout << endl;
		iter++;
	}
}




/************** function main ********************/
int main(int argc,char *argv[])
{

    int result;
    int solutionCount = 0;
	printf("--------------------------------\n");
    readfile(argv[1]);
	//printf("please input num of component: ");
	//scanf("%d", &com);
    //printf("please input diagnosis length: ");
	//scanf("%d",&DigLen);
    com = num_comp;
    DigLen = atoi(argv[2]);


	initial(com);
    setEveryLevIndex(com,DigLen);
    //printArray(everyLevIndex);



    incr();           //first incr() deal situation of 0
	while (length() <= DigLen){
        //print();
        //printf("%d\n",lastIndex);
        result = usePicosat(seq);
        if(result == 1)
        {
            solutionCount++;
            print();                   //print solutions
            //printf("%d\n",result);
        }  
		incr();
	}
    printf("total solutions: %d\n",solutionCount);
    printf("use sat_Solvers: %d\n",sat_count);
    printf("--------------------------------\n");
    return 0;
       
}




