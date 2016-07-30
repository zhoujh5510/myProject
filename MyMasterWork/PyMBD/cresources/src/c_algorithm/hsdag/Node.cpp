/*
 * Node.cpp
 *
 *  Created on: Jun 15, 2011
 *      Author: tq
 */

#include "Graph.h"
#include "Node.h"
#include "Edge.h"
#include <memory>
#include <iostream>
#include <sstream>
#include <algorithm>
#include <boost/dynamic_bitset.hpp>
#include "../debug.h"

using std::cout;
using std::endl;

namespace hsdag
{

Node::Node(NodeId id, Graph* g) : id(id), state(OPEN), level(0), graph(g)
{

}

Node::Node(NodeId id, Graph* g, State s, int level) : id(id), state(s), level(level), graph(g)
{

}

Node::~Node()
{
	// delete incoming edges
	for(EdgeList::iterator it = inEdges.begin(); it != inEdges.end();) {
		graph->getNode((*it)->getSrc())->deleteOutgoingEdgesTo(id);
		delete *it;
		it = inEdges.erase(it);
	}
	// delete outgoing edges
	for(EdgeList::iterator it = outEdges.begin(); it != outEdges.end();) {
		graph->getNode((*it)->getDst())->deleteIncomingEdgesFrom(id);
		delete *it;
		it = outEdges.erase(it);
	}
	if(graph && cs) {
		graph->getSetCache()[*cs].erase(id);
		if(graph->getSetCache()[*cs].empty()) {
			graph->getSetCache().erase(*cs);
		}
	}
	if(graph && !h->empty()) {
		graph->getHCache().erase(*h);
	}
}

NodeId Node::getId() const
{
	return id;
}

Graph* Node::getGraph() const
{
    return graph;
}

HsPtr Node::getH()
{
    return h;
}

int Node::getLevel() const
{
    return level;
}

State Node::getState() const
{
    return state;
}

void Node::setGraph(Graph* graph)
{
    this->graph = graph;
}

void Node::setH(HsPtr h)
{
	if(graph) {
		graph->getHCache()[*h] = id;
	}
    this->h = h;
}

void Node::setLevel(int level)
{
    this->level = level;
}

CsPtr Node::getCs()
{
	if(!cs) {
//		cout << "warning: accessing NULL cs" << endl;
	}
	return cs;
}

void Node::setCs(CsPtr cs)
{
	if(graph && this->cs) {
		graph->getSetCache()[*this->cs].erase(id);
		if(graph->getSetCache()[*this->cs].empty()) {
			graph->getSetCache().erase(*this->cs);
		}
	}
	this->cs = cs;
	if(graph && this->cs && !this->cs->empty()) {
		graph->getSetCache()[*this->cs].insert(id);
	}
}

void Node::setCs(Cs cs)
{
	setCs(CsPtr(new Cs(cs)));
}

void Node::setState(State state)
{
    this->state = state;
}

void Node::addChild(NodeId dst, EdgeLabel lbl)
{
	this->outEdges.push_back(new Edge(id, dst, lbl));
	graph->getNode(dst)->inEdges.push_back(new Edge(id, dst, lbl));
}

NodeListPtr Node::getChildren()
{
	NodeListPtr nodes(new NodeList());
	for(EdgeList::iterator it = outEdges.begin(); it != outEdges.end(); ++it) {
		nodes->push_back((*it)->getDst());
	}
	return nodes;
}

NodeListPtr Node::getIncidents()
{
	NodeListPtr nodes(new NodeList());
	for(EdgeList::iterator it = inEdges.begin(); it != inEdges.end(); ++it) {
		nodes->push_back((*it)->getSrc());
	}
	return nodes;
}

void Node::deleteIncomingEdgesFrom(NodeId node)
{
	for(EdgeList::iterator it = inEdges.begin(); it != inEdges.end();) {
		if((*it)->getSrc() == node) {
			delete *it;
			it = inEdges.erase(it);
		} else {
			++it;
		}
	}
}

void Node::deleteOutgoingEdgesTo(NodeId node)
{
	for(EdgeList::iterator it = outEdges.begin(); it != outEdges.end();) {
		if((*it)->getDst() == node) {
			delete *it;
			it = outEdges.erase(it);
		} else {
			++it;
		}
	}
}


void Node::deleteChildren()
{
	// delete largest possible subgraph
	for(EdgeList::iterator it = outEdges.begin(); it != outEdges.end();) {
		Node* dst_p = graph->getNode((*it)->getDst());
		dst_p->deleteIncomingEdgesFrom(this->id);
		if(dst_p->inEdges.size() == 0) {
			dst_p->deleteChildren();
			graph->removeNode(dst_p->getId());
		}
		delete *it;
		it = outEdges.erase(it);
	}
}

EdgeListPtr Node::getOutgoingEdges()
{
	EdgeListPtr edges(new EdgeList(outEdges));
	return edges;
}

std::string Node::getDotCode()
{
	std::string mark;
	std::stringstream code;
	if(state == OPEN) {
		mark = "";
	} else if(state == CLOSED) {
		mark = " &#10; &#10005; ";
	} else if(state == CHECKED) {
		mark = " &#10; &#10003; ";
	}

	if(this->getCs()) {
		code << "\"" << id << "\" [label=\"" << id << mark << "\\n" << *this->getCs() << "\"];" << std::endl;
	} else {
		code << "\"" << id << "\" [label=\"" << id << mark << "\"];" << std::endl;
	}
	for(EdgeList::iterator it = outEdges.begin(); it != outEdges.end(); ++it)
	{
		code << "\"" << (*it)->getSrc() << "\" -> \"" << (*it)->getDst() << "\" [label=\"" << (*it)->getLabel() << "\"];" << std::endl;
		code << graph->getNode((*it)->getDst())->getDotCode();
	}
	return code.str();
}

void Node::getAllChildren(std::set<NodeId>& children)
{
	if(children.count(id)) {
		return;
	}
	for(EdgeList::iterator it = outEdges.begin(); it != outEdges.end(); ++it) {
		graph->getNode((*it)->getDst())->getAllChildren(children);
	}
	children.insert(id);
}

}

