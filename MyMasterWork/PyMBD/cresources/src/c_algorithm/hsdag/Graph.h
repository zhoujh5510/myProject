/*
 * Graph.h
 *
 *  Created on: Jun 15, 2011
 *      Author: tq
 */

#ifndef GRAPH_H_
#define GRAPH_H_

#include <set>
#include <vector>
#include <boost/shared_ptr.hpp>
#include "Node.h"
#include "../types.h"
#include "types.h"

using std::set;
using std::vector;
using std::list;

namespace hsdag
{

class Graph
{
public:
	Graph();
	~Graph();

	Node* getNode(NodeId id);
	bool validNode(NodeId id);
	NodeId createNode();
	void removeNode(NodeId id);

	void addCheckedNode(NodeId node);
	vector<RawNodeList>& getCheckedNodes();
	void setRoot(NodeId root);
	NodeId getRoot();
	NodeList& getWorklist();
	HashMapBs2Node& getHCache();
	HashMapBs2NodeList& getSetCache();
	CsList& getCsCache();
	std::string getDotCode();
	int getNumNodes();
	int getNextNodeId();

protected:
	NodeId nextNodeId;
	HashMapId2Node nodes;
	NodeId root;
	vector<RawNodeList> checked_nodes;
	NodeList worklist;
	HashMapBs2Node h_cache;
	HashMapBs2NodeList set_cache;
	CsList cs_cache;

};


}
list<int> checkedNodesKeys(vector<hsdag::RawNodeList>& checked_nodes);

#endif /* GRAPH_H_ */
