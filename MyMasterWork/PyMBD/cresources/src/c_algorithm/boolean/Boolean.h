/*
 * Boolean.h
 *
 *  Created on: Aug 4, 2011
 *      Author: tq
 */

#ifndef BOOLEAN_H_
#define BOOLEAN_H_
#include <boost/python.hpp>
#include <list>
#include "../Timer.h"
#include "Worklist.h"
#include "../Description.h"
using boost::python::object;
using boost::python::tuple;
using boost::python::class_;
using std::list;

namespace boolean {

class Boolean
{
protected:
	Timer timer;
	double calculationTime;

public:
	Boolean();
	virtual ~Boolean();
	virtual WorklistPtr boolean_iterative(Description description, unsigned long max_cardinality, WorklistPtr previous_worklist, float max_time);
	virtual double get_calculation_time();

protected:
	virtual void process(WorklistPtr& worklist, unsigned int card, float max_time, unsigned int max_card);
	virtual list<WorklistItem> h_iterative(WorklistItem& item, unsigned int max_card);
	virtual void minimize_finished(WorklistPtr& worklist);
	virtual unsigned int get_most_common_element(ScsPtr& scs);
	virtual bool check_superset(unsigned int l, HsPtr& hs, HsByCard& finished);
};

}

void expose_boolean();

#endif /* BOOLEAN_H_ */
