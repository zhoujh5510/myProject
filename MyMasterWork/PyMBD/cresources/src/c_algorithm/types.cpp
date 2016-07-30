/*
 * types.cpp
 *
 *  Created on: Jun 17, 2011
 *      Author: tq
 */
#include <algorithm>
#include <iostream>
#include <vector>
using std::cout;
using std::endl;
using std::vector;
#include "types.h"

bool compare(const CsPtr& first, const CsPtr& second)
{
	return *first < *second;
}

// compares two sets of conflict sets. be aware that this function
// CREATES COPIES of both sets because they must be ordered for
// comparing, but the arguments shall not be modified.
bool scs_equal(const Scs& cs1, const Scs& cs2)
{
	Scs copy1 = cs1;
	Scs copy2 = cs2;
	sort(copy1.begin(), copy1.end(), &compare);
	sort(copy2.begin(), copy2.end(), &compare);
	return copy1 == copy2;
}


void pad(Bs& s1, Bs& s2)
{
	size_t max = std::max(s1.size(), s2.size());
	s1.resize(max);
	s2.resize(max);
}

bool compare_length(const CsPtr& first, const CsPtr& second)
{
	return first->count() < second->count();
}

bool operator<( const CsPtr& first, const CsPtr& second)
{
    return first->count() < second->count();
}
