/*
 * DescriptionProxy.h
 *
 *  Created on: Jul 21, 2011
 *      Author: tq
 */

#ifndef DESCRIPTIONPROXY_H_
#define DESCRIPTIONPROXY_H_

#include <boost/python.hpp>
#include "types.h"
#include "Description.h"
using boost::python::object;

class DescriptionProxy
{
public:
	DescriptionProxy(object* py_oracle);
	DescriptionProxy(Description* cpp_oracle);
	virtual ~DescriptionProxy();
	virtual CsPtr getFirstConflictSet();
	virtual CsPtr getConflictSet(HsPtr h);
	virtual bool checkConsistency(HsPtr h);
	virtual int getNumComponents();

protected:
	object* py_oracle;
	Description* cpp_oracle;
};

#endif /* DESCRIPTIONPROXY_H_ */
