#include <iostream>
#include <stack>
using namespace std;

/*
**�������ܣ�����stackʵ������
**���룺�������stack
**�����������ɵ�stack
*/

stack<int> stackSort(stack<int> &s)
{
	if (s.size() <= 0)
	{
		return s;
	}

	stack<int> r;
	while (!s.empty())
	{
		int temp = s.top();
		s.pop();
		while (!r.empty() && r.top() < temp)
		{
			s.push(r.top());
			r.pop();
		}
		r.push(temp);
	}

	return r;
}


int main()
{
	stack<int> s;
	int n = 0;
	int temp = 0;
	while (cin >> n)
	{
		for (int i = 0; i < n; i++)
		{
			cin >> temp;
			s.push(temp);
		}
		stack<int> res = stackSort(s);
		while (!res.empty())
		{
			cout << res.top() << " ";
			res.pop();
		}
		cout << endl;
		
	}
}