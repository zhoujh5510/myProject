/*
 * python_types.h
 *
 *  Created on: Jun 28, 2011
 *      Author: tq
 */

#ifndef PYTHON_TYPES_H_
#define PYTHON_TYPES_H_

#include <boost/python.hpp>
#include <list>

void register_types();

class BitsetToPySetConverter
{
public:
    static PyObject* convert(Bs const& x);
};

class BitsetPtrToPySetConverter
{
public:
    static PyObject* convert(BsPtr const& x);
};

class ShsToPySetConverter
{
public:
    static PyObject* convert(ShsPtr const& x);
};

class PySetToBitsetConverter
{
public:
	static void* convertible(PyObject* obj_ptr);
	static void construct(PyObject* obj_ptr, boost::python::converter::rvalue_from_python_stage1_data* data);
};

class IntListConverter
{
public:
    static PyObject* convert(std::list<int> const & x);
};

class PyToCppScsConverter
{
public:
	static void* convertible(PyObject* obj_ptr);
	static void construct(PyObject* obj_ptr, boost::python::converter::rvalue_from_python_stage1_data* data);
};

#endif /* PYTHON_TYPES_H_ */
