#include <iostream>
using namespace std;

//ͨ��ͼ��������ȱ�������1-n��ȫ����
const int N = 13;   //n�����ֵ
int d[N];     //��¼��
int v[N];     //��¼ĳ��ֵ�Ƿ񱻱����� 0:δ���� 1:�ѱ���
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
