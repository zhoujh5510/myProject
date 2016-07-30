/*
 * python_types.cpp
 *
 *  Created on: Jun 28, 2011
 *      Author: tq
 *
 *  http://misspent.wordpress.com/2009/09/27/how-to-write-boost-python-converters/
 *
 */

#include "types.h"
#include "Description.h"
#include "hsdag/Graph.h"
#include "python_types.h"
#include <boost/python.hpp>
#include <algorithm>
#include <exception>
#include <list>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>
#include <boost/python/converter/rvalue_from_python_data.hpp>

namespace bp=boost::python;

/*    ====================================== to-python converters ====================================== */

PyObject* BitsetToPySetConverter::convert(Bs const& x)
{
	bp::list l;
	for(size_t i = 0; i < x.size(); i++) {
		if(x.test(i)) {
			l.append(i);
		}
	}
	return PyFrozenSet_New(l.ptr());
}

PyObject* BitsetPtrToPySetConverter::convert(BsPtr const& x)
{
	bp::list l;
	for(size_t i = 0; i < x->size(); i++) {
		if(x->test(i)) {
			l.append(i);
		}
	}
	return PyFrozenSet_New(l.ptr());
}

PyObject* ShsToPySetConverter::convert(ShsPtr const& x)
{
	bp::list outer;
	for(Shs::iterator it = x->begin(); it != x->end(); ++it) {
		bp::list inner;
		for(Hs::size_type it2 = 0; it2 < it->size(); ++it2) {
			if(it->test(it2)) {
				inner.append(it2);
			}
		}
		PyObject* hs = PyFrozenSet_New(inner.ptr());
		PyList_Append(outer.ptr(), hs);
		Py_DECREF(hs);
//		std::cout << "HS: " << Py_REFCNT(hs) << std::endl;
	}
	PyObject* shs = PySet_New(outer.ptr());
//	std::cout << "SHS: " << Py_REFCNT(shs) << std::endl;
	return shs;
}



/*    ====================================== from-python converters ====================================== */

void* PySetToBitsetConverter::convertible(PyObject* obj_ptr)
{
	if(PyAnySet_Check(obj_ptr)) {
		return obj_ptr;
	} else {
		return NULL;
	}
}

void PySetToBitsetConverter::construct(PyObject* obj_ptr, boost::python::converter::rvalue_from_python_stage1_data* data)
{
	if(Description::SIZE == 0) {
		std::cout << "ERROR: you must set the problem size before calling any C methods using c_algorithm.set_problem_size(int size)" << std::endl;;
		throw std::runtime_error("you must set the problem size before calling any C methods using c_algorithm.set_problem_size(int size)");
	}
	// Grab pointer to memory into which to construct the new QString
	void* storage = ((boost::python::converter::rvalue_from_python_storage<Bs>*)data)->storage.bytes;

//	std::cout << "SIZE=" << SIZE << std::endl;
	Bs* bs = new (storage) Bs(Description::SIZE);

	PyObject* iter = PyObject_GetIter(obj_ptr);
	while(PyObject* e = PyIter_Next(iter)) {
		long bit = bp::extract<long>(e);
//			bs->resize(std::max((long int)bs->size(), bit+1));
		bs->set(bit, true);
		Py_DECREF(e);
	}
	Py_DECREF(iter);

	// Stash the memory chunk pointer for later use by boost.python
	data->convertible = storage;
}



PyObject* IntListConverter::convert(std::list<int> const & x)
{
	bp::list l;
	for(std::list<int>::const_iterator it = x.begin(); it != x.end(); ++it) {
		l.append(*it);
	}
	return bp::incref(l.ptr());
}


void* PyToCppScsConverter::convertible(PyObject* obj_ptr)
{
	if(PyAnySet_Check(obj_ptr) or PyList_Check(obj_ptr)) {
		// Note: Also list objects can be converted to a SCS
		return obj_ptr; // todo maybe check if elements are only sets!?
	} else {
		return NULL;
	}
}

void PyToCppScsConverter::construct(PyObject* obj_ptr, boost::python::converter::rvalue_from_python_stage1_data* data)
{
//	std::cout << "PyToCppScsConverter::construct called" << std::endl;
	// Grab pointer to memory into which to construct the new QString
	void* storage = ((boost::python::converter::rvalue_from_python_storage<ScsPtr>*)data)->storage.bytes;

	ScsPtr* scs = new (storage) ScsPtr(new Scs());

	PyObject* iter = PyObject_GetIter(obj_ptr);
	while(PyObject* e = PyIter_Next(iter)) {
		CsPtr cs(new Cs(Description::SIZE));
		PyObject* iter2 = PyObject_GetIter(e);
		while(PyObject* e2 = PyIter_Next(iter2)) {
			long bit = bp::extract<long>(e2);
			cs->set(bit, true);
			Py_DECREF(e2);
		}
		(*scs)->push_back(cs);
		Py_DECREF(iter2);
		Py_DECREF(e);
	}
	Py_DECREF(iter);

	// Stash the memory chunk pointer for later use by boost.python
	data->convertible = storage;
}

/*    ====================================== registration ====================================== */

void register_types()
{
	bp::converter::registry::push_back(&PyToCppScsConverter::convertible, &PyToCppScsConverter::construct,boost::python::type_id<ScsPtr>());
	bp::converter::registry::push_back(&PySetToBitsetConverter::convertible, &PySetToBitsetConverter::construct,boost::python::type_id<Bs>());
	bp::to_python_converter<Bs, BitsetToPySetConverter, false>();
//	bp::to_python_converter<BsPtr, BitsetPtrToPySetConverter, false>();
	bp::to_python_converter<ShsPtr, ShsToPySetConverter, false>();
	bp::to_python_converter<std::list<int>, IntListConverter, false>();
	bp::register_ptr_to_python<ScsPtr>();
	bp::register_ptr_to_python<HsPtr>();
}

