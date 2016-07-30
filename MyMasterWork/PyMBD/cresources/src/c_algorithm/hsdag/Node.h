/*
 * Node.h
 *
 *  Created on: Jun 15, 2011
 *      Author: tq
 */

#ifndef NODE_H_
#define NODE_H_
#include <list>
#include <set>
#include "../types.h"
#include "types.h"

using std::list;

namespace hsdag {

class Edge;
class Graph;

enum State { OPEN, CLOSED, CHECKED };

class Node {

protected:

	NodeId id;
	EdgeList inEdges;
	EdgeList outEdges;
	State state;
	int level;
	HsPtr h;
	CsPtr cs;
	Graph* graph;

public:
	Node(NodeId id, Graph* g);
	Node(NodeId id, Graph* g, State s, int level);
	~Node();
	NodeId getId() const;
	Graph *getGraph() const;
	HsPtr getH();
	int getLevel() const;
	State getState() const;
	void setGraph(Graph *graph);
	void setH(HsPtr h);
	void setLevel(int level);
	void setState(State state);
	void addChild(NodeId dst, EdgeLabel lbl);
	NodeListPtr getChildren();
	NodeListPtr getIncidents();
	void deleteIncomingEdgesFrom(NodeId node);
	void deleteOutgoingEdgesTo(NodeId node);
	void deleteChildren();
    CsPtr getCs();
    void setCs(Cs cs);
    void setCs(CsPtr cs);
    EdgeListPtr getOutgoingEdges();
    std::string getDotCode();
    void getAllChildren(std::set<NodeId>& children);
};

}


#endif /* NODE_H_ */
