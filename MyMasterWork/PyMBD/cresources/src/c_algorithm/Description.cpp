/*
 * Description.cpp
 *
 *  Created on: Jun 16, 2011
 *      Author: tq
 */

#include "Description.h"
#include "types.h"
#include "python_types.h"
#include <iostream>
#include <algorithm>
#include <boost/python.hpp>
using std::cout;
using std::endl;
using namespace boost::python;

void expose_description()
{

	class_<Description>("Description", init<ScsPtr, bool>())
		.def("get_total_time", &Description::getTotalTime)
		.def("get_num_calls", &Description::getNumCalls)
		.def("get_check_calls", &Description::getCheckCalls)
		.def("get_comp_calls", &Description::getCompCalls)
		.def("get_check_time", &Description::getCheckTime)
		.def("get_comp_time", &Description::getCompTime);

}

int Description::SIZE = 0;

Description::Description(ScsPtr scs, bool sort) : sets(scs), numChecks(0), numComps(0), timeChecks(0.0), timeComps(0.0)
{
//	for(Scs::iterator it = sets->begin(); it != sets->end(); ++it) {
//		cout << **it << endl;
//	}
//	cout << "ho" << endl;
	if(sort) {
		std::sort(sets->begin(), sets->end(), &compare_length);
	}
//	components = Bs(Description::SIZE);

//		if(components.size() != it->size()) {
//			cout << "got conflict set of size " << it->size() << " in problem with size " << components.size() << ", did you forget c_algorithm.set_problem_size(int)?" << endl;
//		}
//		components |= *it;
}


Description::~Description() {

}

CsPtr Description::getFirstConflictSet()
{
	return getConflictSet(HsPtr(new Hs()));
}

CsPtr Description::getConflictSet(HsPtr h)
{
	timer.restart();
	numComps += 1;
	for(Scs::iterator it = sets->begin(); it != sets->end(); ++it) {
		if(!(*it)->intersects(*h)) {
			timeComps += timer.elapsed();
			return *it;
		}
	}
	timeComps += timer.elapsed();
	return CsPtr();
}

bool Description::checkConsistency(HsPtr h)
{
	timer.restart();
	numChecks += 1;
//	cout << "Description: checkConsistency(" << *h << ")" << endl;
	for(Scs::iterator it = sets->begin(); it != sets->end(); ++it) {
		if(!(*it)->intersects(*h)) {
			timeChecks += timer.elapsed();
			return false;
		}
	}
	timeChecks += timer.elapsed();
	return true;
}

int Description::debug()
{
	int sum = 0;
	for(Scs::iterator it = sets->begin(); it < sets->end(); ++it) {
		cout << "bitset: " << *it << endl;
		sum += (*it)->to_ulong();
	}
	return sum;
}

std::list<int> Description::getComponents()
{
	std::list<int> comps;
	for(Bs::size_type i = 0; i < components.size(); ++i) {
		if(components.test(i)) {
			comps.push_back(i);
		}
	}
	return comps;
}

int Description::getNumCalls()
{
	return numChecks + numComps;
}

float Description::getTotalTime()
{
	return timeChecks + timeComps;
}

int Description::getNumComponents()
{
	return components.size();
}

ScsPtr Description::getConflictSets()
{
	return sets;
}

int Description::getCheckCalls()
{
	return numChecks;
}

int Description::getCompCalls()
{
	return numComps;
}

float Description::getCheckTime()
{
	return timeChecks;
}

float Description::getCompTime()
{
	return timeComps;
}

