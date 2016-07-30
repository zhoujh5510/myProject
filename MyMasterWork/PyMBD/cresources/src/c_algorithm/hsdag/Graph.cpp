/*
 * Graph.cpp
 *
 *  Created on: Jun 15, 2011
 *      Author: tq
 */

#include "Graph.h"
#include "Node.h"
#include "Edge.h"
#include <iostream>
#include <sstream>
#include <set>

namespace hsdag {

Graph::Graph() : nextNodeId(0), root(0)
{


}

Graph::~Graph()
{
	for(HashMapId2Node::iterator it = nodes.begin(); it != nodes.end(); ++it) {
		delete it->second;
	}
}


Node* Graph::getNode(NodeId id)
{
	HashMapId2Node::iterator el = nodes.find(id);
	if(el != nodes.end()) {
		return el->second;
	} else {
		std::cout << "ERROR: Node " << id << " not valid!" << std::endl;
		return NULL;
	}
}

bool Graph::validNode(NodeId id)
{
	return (nodes.find(id) != nodes.end());
}

NodeId Graph::createNode()
{
	Node* node = new Node(nextNodeId, this);
	nodes[node->getId()] = node;
	return nextNodeId++;
}

void Graph::removeNode(NodeId id)
{
	delete nodes[id];
	nodes.erase(id);
}

vector<RawNodeList>& Graph::getCheckedNodes()
{
	return checked_nodes;
}

void Graph::addCheckedNode(NodeId node)
{
	Hs::size_type len = getNode(node)->getH()->count();
	if (checked_nodes.size() < len+1) {
		checked_nodes.resize(len+1);
	}
	checked_nodes[len].push_back(getNode(node));
//	std::cout << "adding checked node with len= " << len << std::endl;
}

void Graph::setRoot(NodeId root)
{
	this->root = root;
}

NodeId Graph::getRoot()
{
	return this->root;
}

NodeList& Graph::getWorklist()
{
	return this->worklist;
}

HashMapBs2Node& Graph::getHCache()
{
	return this->h_cache;
}

HashMapBs2NodeList& Graph::getSetCache()
{
	return this->set_cache;
}

CsList& Graph::getCsCache()
{
	return this->cs_cache;
}

std::string Graph::getDotCode()
{
	std::stringstream code;
	code << "digraph G {" << std::endl;;
    code << getNode(root)->getDotCode();
	code << "}" << std::endl;
	return code.str();
}

int Graph::getNumNodes()
{
	std::set<NodeId> nodes;
	getNode(root)->getAllChildren(nodes);
	nodes.insert(root);
	return nodes.size();
}

int Graph::getNextNodeId()
{
	return nextNodeId;
}

}


list<int> checkedNodesKeys(vector<hsdag::RawNodeList>& checked_nodes)
{
	list<int> result;
	int i = 0;
	for(vector<hsdag::RawNodeList>::iterator it = checked_nodes.begin(); it != checked_nodes.end(); ++it, ++i) {
		if(!it->empty()) {
			result.push_back(i);
		}
	}
	return result;
}


