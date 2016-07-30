/*
 * HsDag.h
 *
 *  Created on: Jun 16, 2011
 *      Author: tq
 */

#ifndef HSDAG_H_
#define HSDAG_H_

#include "types.h"
#include "Graph.h"
#include "../Timer.h"
#include "../Description.h"
#include "../DescriptionProxy.h"
#include <boost/python.hpp>
using boost::python::object;
using boost::python::tuple;
using boost::python::class_;

namespace hsdag {

class HsDag {

protected:
	Timer timer;
	double calculationTime;
	int debugPruningStep;

public:

	HsDag();
	virtual ~HsDag();
	virtual GraphPtr hsdag_py(object oracle, long max_card, GraphPtr prev_tree, object max_time, bool prune, bool cache);
	virtual GraphPtr hsdag_cpp(Description* oracle, long max_card, GraphPtr prev_tree, double max_time, bool prune, bool cache);
	virtual ShsPtr hittingsets_from_tree(GraphPtr graph, tuple card);
	virtual double getCalculationTime();

protected:
	virtual GraphPtr hsdag(DescriptionProxy oracle, long max_card, GraphPtr prev_tree, double max_time, bool prune, bool cache);
	virtual NodeListPtr processNode(NodeId node, GraphPtr& graph, DescriptionProxy oracle, bool prune, bool cache, long max_card);
	virtual bool hIsSuperset(NodeId node, GraphPtr& graph);
	virtual void pruneTree(NodeId node, GraphPtr& graph);
	virtual void getDescendants(NodeId node, GraphPtr& graph, NodeSet& prunedNodes);
	virtual bool allParentsPruned(NodeId node, GraphPtr& graph, NodeSet& prunedNodes);

};

}


void expose_hsdag();

#endif /* HSDAG_H_ */
