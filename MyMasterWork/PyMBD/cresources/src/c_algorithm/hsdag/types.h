/*
 * types.h
 *
 *  Created on: Aug 4, 2011
 *      Author: tq
 */

#ifndef HSDAG_TYPES_H_
#define HSDAG_TYPES_H_
#include <boost/shared_ptr.hpp>
#include <boost/dynamic_bitset.hpp>
#include <unordered_map>
#include <list>
#include <set>
#include "../types.h"

namespace hsdag {

class Node;
class Edge;
class Graph;

typedef unsigned long int NodeId;

typedef boost::shared_ptr<Graph> GraphPtr;
typedef std::list<NodeId> NodeList;
typedef std::set<NodeId> NodeSet;
typedef std::list<Node*> RawNodeList;
typedef boost::shared_ptr<NodeList> NodeListPtr;
typedef std::list<Edge*> EdgeList;
typedef boost::shared_ptr<EdgeList> EdgeListPtr;

typedef std::unordered_map<NodeId, Node*> HashMapId2Node;

typedef std::unordered_map<Bs, NodeId> HashMapBs2Node;
typedef std::unordered_map<Bs, NodeSet> HashMapBs2NodeList;

}

#endif /* HSDAG_TYPES_H_ */
