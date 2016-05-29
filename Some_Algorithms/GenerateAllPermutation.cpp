#include <iostream>
using namespace std;

//通过图的深度优先遍历生成1-n的全排列
const int N = 13;   //n的最大值
int d[N];     //记录解
int v[N];     //记录某个值是否被遍历过 0:未遍历 1:已遍历
int n;        

void dfs(int depth)
{
	if (depth >= n)
	{
		for (int i = 0; i != n; i++)
		{
			cout << d[i];
		}
		cout << endl;
		return;
	}

	for (int i = 1; i <= n; i++)
	{
		if (v[i] == 0)
		{
			v[i] = 1;
			d[depth] = i;
			dfs(depth + 1);
			v[i] = 0;
		}
	}
}


int main()
{

	while (cin >> n)
	{
		memset(v, 0, n);
		dfs(0);
	}
}
