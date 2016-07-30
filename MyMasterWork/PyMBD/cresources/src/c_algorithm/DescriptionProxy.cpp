/*
 * DescriptionProxy.cpp
 *
 *  Created on: Jul 21, 2011
 *      Author: tq
 */

#include "DescriptionProxy.h"
#include <iostream>
#include <boost/python/extract.hpp>
using std::cout;
using std::endl;

DescriptionProxy::DescriptionProxy(object* py_oracle) : py_oracle(py_oracle), cpp_oracle(NULL)
{
}

DescriptionProxy::DescriptionProxy(Description* cpp_oracle) : py_oracle(NULL), cpp_oracle(cpp_oracle)
{
}

DescriptionProxy::~DescriptionProxy()
{
}

CsPtr DescriptionProxy::getFirstConflictSet()
{
	if(py_oracle) {
		object r = py_oracle->attr("get_first_conflict_set")();
		if(r) {
			return CsPtr(new Cs(boost::python::extract<Cs>(r)));
		} else {
			return CsPtr();
		}
	} else if(cpp_oracle) {
		CsPtr r = cpp_oracle->getFirstConflictSet();
		if(r) {
			return r;
		} else {
			return CsPtr();
		}
	} else {
		cout << "ERROR: DescriptionProxy with no oracle" << endl;
		return CsPtr();
	}
}

CsPtr DescriptionProxy::getConflictSet(HsPtr h)
{
	if(py_oracle) {
		object r = py_oracle->attr("get_conflict_set")(*h);
		if(r) {
			return CsPtr(new Cs(boost::python::extract<Cs>(r)));
		} else {
			return CsPtr();
		}
	} else if(cpp_oracle) {
		CsPtr r = cpp_oracle->getConflictSet(h);
		if(r) {
			return r;
		} else {
			return CsPtr();
		}
	} else {
		cout << "ERROR: DescriptionProxy with no oracle" << endl;
		return CsPtr();
	}
}

int DescriptionProxy::getNumComponents()
{
	if(py_oracle) {
		object r = py_oracle->attr("get_num_components")();
		if(r) {
			return boost::python::extract<int>(r);
		} else {
			return -1;
		}
	} else if(cpp_oracle) {
		return cpp_oracle->getNumComponents();
	} else {
		cout << "ERROR: DescriptionProxy with no oracle" << endl;
		return -1;
	}
}

bool DescriptionProxy::checkConsistency(HsPtr h)
{
	if(py_oracle) {
		object r = py_oracle->attr("check_consistency")(*h);
		return boost::python::extract<bool>(r);
	} else if(cpp_oracle) {
		bool r = cpp_oracle->checkConsistency(h);
		return r;
	} else {
		cout << "ERROR: DescriptionProxy with no oracle" << endl;
		return false;
	}
}
