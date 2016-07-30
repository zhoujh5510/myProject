/*
 * HsDag.cpp
 *
 *  Created on: Jun 16, 2011
 *      Author: tq
 */
#include <iostream>
#include <algorithm>
#include <fstream>
#include <sstream>
#include "HsDag.h"
#include "Graph.h"
#include "Edge.h"
#include "../debug.h"
#include "../python_types.h"
#include <boost/python/extract.hpp>
using namespace boost::python;
using std::cout;
using std::endl;

void expose_hsdag()
{

	class_<hsdag::Graph>("Graph")
		.add_property("checked_nodes", make_function(&hsdag::Graph::getCheckedNodes, return_internal_reference<>()))
		.add_property("next_node_id", &hsdag::Graph::getNextNodeId)
		.def("get_num_nodes", &hsdag::Graph::getNumNodes);

	class_<hsdag::Node>("Node", no_init)
		.add_property("h", &hsdag::Node::getH);

	class_<hsdag::Edge>("Edge", init<hsdag::NodeId, hsdag::NodeId, EdgeLabel>());

	class_<hsdag::RawNodeList>("NodeList")
		.def("__iter__", iterator<hsdag::RawNodeList, return_internal_reference<> >())
		.def("__len__", &hsdag::RawNodeList::size);

	hsdag::RawNodeList& (vector<hsdag::RawNodeList>::*at_function)(vector<hsdag::RawNodeList>::size_type) = &vector<hsdag::RawNodeList>::at;

	class_<vector<hsdag::RawNodeList> >("CheckedNodesDictEmulation")
		.def("__iter__", iterator<vector<hsdag::RawNodeList>, return_internal_reference<> >())
		.def("__len__", &vector<hsdag::RawNodeList>::size)
		.def("keys", &checkedNodesKeys)
		.def("__getitem__", make_function(at_function, return_internal_reference<>()));

	class_<hsdag::HsDag>("HsDag")
			.def("hsdag", &hsdag::HsDag::hsdag_py)
			.def("hsdag_cpp", &hsdag::HsDag::hsdag_cpp)
			.def("hsdag_py", &hsdag::HsDag::hsdag_py)
			.def("hittingsets_from_tree", &hsdag::HsDag::hittingsets_from_tree)
			.def("get_calculation_time", &hsdag::HsDag::getCalculationTime);

	register_ptr_to_python<hsdag::GraphPtr>();
}

namespace hsdag {

HsDag::HsDag() : debugPruningStep(0)
{
}


HsDag::~HsDag()
{
}

GraphPtr HsDag::hsdag_py(object oracle, long max_card, GraphPtr prev_graph, object max_time, bool prune, bool cache)
{
	DescriptionProxy o(&oracle);
	double max_time_d = 0;
	if (max_time) {
		max_time_d = extract<double>(max_time);
	}
	return hsdag(o, max_card, prev_graph, max_time_d, prune, cache);
}

GraphPtr HsDag::hsdag_cpp(Description* oracle, long max_card, GraphPtr prev_graph, double max_time, bool prune, bool cache)
{
	DescriptionProxy o(oracle);
	return hsdag(o, max_card, prev_graph, max_time, prune, cache);
}

GraphPtr HsDag::hsdag(DescriptionProxy oracle, long max_card, GraphPtr prev_graph, double max_time, bool prune, bool cache)
{
//	Description::SIZE = oracle.getNumComponents();
	GraphPtr g;
	timer.restart();
	if(prev_graph) {
		g = prev_graph;
	} else {
		g = GraphPtr(new Graph());
		CsPtr first = oracle.getFirstConflictSet();
		if(first->empty()) {
			return g;
		}
		NodeId root = g->createNode();
		g->setRoot(root);
		g->getNode(root)->setCs(first);
		g->getNode(root)->setH(HsPtr(new Hs(Description::SIZE)));
		g->getWorklist().push_back(root);
	}

	while(!g->getWorklist().empty()) {
		NodeId node = g->getWorklist().front();
		if (!g->validNode(node)) {
			g->getWorklist().pop_front();
			continue;
		}
		if (max_time > 0 and timer.elapsed() > max_time) {
			break;
		}
		g->getWorklist().pop_front();

		if(g->getNode(node)->getState() == OPEN) {
			NodeListPtr new_nodes = processNode(node, g, oracle, prune, cache, max_card);
			g->getWorklist().insert(g->getWorklist().end(), new_nodes->begin(), new_nodes->end());
		}
	}
	calculationTime = timer.elapsed();
//	g->printDotCode();
	return g;
}

NodeListPtr HsDag::processNode(NodeId node, GraphPtr& g, DescriptionProxy oracle, bool prune, bool cache, long max_card)
{
	NodeListPtr result(new NodeList());

	if(g->getNode(node)->getLevel() >= 2) {
		if(hIsSuperset(node, g)) {
			g->getNode(node)->setState(CLOSED);
			g->getNode(node)->setH(HsPtr(new Hs())); // we don't need any h for such nodes
			return result;
		}
	}

	CsPtr sigma;
	HsPtr h = g->getNode(node)->getH();


	if(oracle.checkConsistency(h)) {
		g->getNode(node)->setState(CHECKED);
		g->addCheckedNode(node);
		return result;
	}

	if (g->getNode(node)->getLevel() > 0 && g->getNode(node)->getLevel() >= max_card) {
		return result;
	}

	if (cache) {
		for(CsList::iterator it = g->getCsCache().begin(); it != g->getCsCache().end(); ++it) {
			if(!(*it)->intersects(*h)) {
				sigma = *it;
				//cout << "Cache hit!" << endl;
				break;
			}
		}
	}


	if(!sigma || !sigma->size()) {
		sigma = oracle.getConflictSet(h);

		if(!sigma || !sigma->size()) {
			cout << "ERROR: oracle seems inconsistent: node's h is not consistent, but also no new conflict set returned";
			return result;
		}
	}

	g->getNode(node)->setCs(sigma);

	if(cache) {
		g->getCsCache().insert(sigma);
		//cout << "adding something to cache..." << endl;
	}

	if(prune) {
		pruneTree(node, g);
	}

	// node may have been pruned away
	if(!g->validNode(node)) {
		return result;
	}

	size_t s = sigma->find_first();
	while(s != sigma->npos) {
		HsPtr new_h(new Hs(*g->getNode(node)->getH())); // important! make a copy!
		new_h->resize(std::max(new_h->size(), s+1));
		new_h->set(s, true);

		if(g->getHCache().count(*new_h) > 0) {
			NodeId target = g->getHCache()[*new_h];
			g->getNode(node)->addChild(target, s);
		} else {
			NodeId n = g->createNode();
			g->getNode(n)->setLevel(g->getNode(node)->getLevel()+1);
			g->getNode(n)->setH(new_h);
			g->getNode(node)->addChild(n, s);
			result->push_back(n);
		}

		s = sigma->find_next(s);
	}
	g->getNode(node)->setH(HsPtr(new Hs())); // we don't need any h for unchecked nodes
	return result;
}

bool HsDag::hIsSuperset(NodeId node, GraphPtr& g)
{
	Node* node_p = g->getNode(node);
	Hs::size_type level = node_p->getH()->count();
	for(Hs::size_type i = 1; i < std::min(level, g->getCheckedNodes().size()); i++) {
		RawNodeList nl = g->getCheckedNodes()[i];
		for(RawNodeList::iterator it = nl.begin(); it != nl.end(); ++it) {
			Node* n = *it;
			if(n) {
				if(n->getH()->is_subset_of(*node_p->getH())) {
					return true;
				}
			}
		}
	}
	return false;
}

void HsDag::pruneTree(NodeId node, GraphPtr& g)
{
	CsPtr sigma = g->getNode(node)->getCs();
	vector<Cs> allSets = vector<Cs>();
	allSets.reserve(g->getSetCache().size());

	// get a list of all node's conflict sets because setCache will change during pruning
	for(HashMapBs2NodeList::iterator i = g->getSetCache().begin(); i != g->getSetCache().end(); ++i) {
		allSets.push_back(i->first);
	}

	for(vector<Cs>::iterator it = allSets.begin(); it != allSets.end(); ++it) {
		Cs s_prime = *it;

		if(sigma->is_proper_subset_of(s_prime)) {
			// we found nodes where at least one outgoing edge can be deleted

			NodeSet nl(g->getSetCache()[*it]); // makes a COPY to circumvent iterate-while-modify problem
			for(NodeSet::iterator nl_it = nl.begin(); nl_it != nl.end(); ++nl_it) {
				NodeId n_prime = *nl_it;
				if(!g->validNode(n_prime)) {
					cout << "ERROR: found invalid node " << n_prime << " in set cache (2) for cs " << s_prime << endl;
					debug(g->getSetCache());
					continue;
				}

				// update the node's CS to the subset
				Node* n_prime_p = g->getNode(n_prime);
				n_prime_p->setCs(sigma);

				EdgeListPtr neighbors = n_prime_p->getOutgoingEdges();
				for(EdgeList::iterator it_e = neighbors->begin(); it_e != neighbors->end(); ++it_e) {

					if(!sigma->test((*it_e)->getLabel())) {
						// this edge's component is no longer in the CS of the node, so delete the edge (and the largest
						// possible subgraph below)

						NodeId child = (*it_e)->getDst();
						if(!g->validNode(child)) {
							cout << "ERROR: found invalid node " << child << "in child list of node " << n_prime << endl;
							continue;
						}
						if(g->getNode(child)->getIncidents()->size() > 1) {
							// do not prune if this node has another parent
							continue;
						}

						// find all descendants of the node being currently pruned, except those who have another ancestor
						// which is not being pruned
						NodeSet prunedNodes;
						prunedNodes.insert(child);
						getDescendants(child, g, prunedNodes);

//						std::ofstream file;
//						std::stringstream filename;
//						filename << "greiner-c-debug_pruning_" << debugPruningStep << ".dot";
//						file.open(filename.str().c_str());
//						file << g->getDotCode();
//						file.close();
//						cout << "wrote to " << filename.str() << endl;
//						debugPruningStep++;

						for(NodeSet::iterator it = prunedNodes.begin(); it != prunedNodes.end(); ++it) {
							if(g->validNode(*it)) {
								g->removeNode(*it);
							}
						}
						n_prime_p->deleteOutgoingEdgesTo(child);
						g->removeNode(child);
					}
				}
			}
		}
	}

}

void HsDag::getDescendants(NodeId node, GraphPtr& g, NodeSet& prunedNodes)
{
	if(prunedNodes.count(node) || allParentsPruned(node, g, prunedNodes)) {
		prunedNodes.insert(node);
		NodeListPtr children = g->getNode(node)->getChildren();
		for(NodeList::iterator it = children->begin(); it != children->end(); ++it) {
			getDescendants(*it, g, prunedNodes);
		}
	}
}

bool HsDag::allParentsPruned(NodeId node, GraphPtr& g, NodeSet& prunedNodes)
{
	NodeListPtr parents = g->getNode(node)->getIncidents();
	bool allPruned = true;
	for(NodeList::iterator it = parents->begin(); it != parents->end(); ++it) {
		if(prunedNodes.count(*it) == 0) {
			allPruned = false;
			break;
		}
	}
	return allPruned;
}

ShsPtr HsDag::hittingsets_from_tree(GraphPtr graph, tuple card)
{
	ShsPtr shs(new Shs());
	unsigned long int min_card = extract<unsigned long int>(card.attr("__getitem__")(0));
	unsigned long int max_card = extract<unsigned long int>(card.attr("__getitem__")(1));

	vector<RawNodeList> nodes = graph->getCheckedNodes();
	if(!nodes.empty()) {
		for(unsigned long int c = min_card; c < std::min((unsigned long)nodes.size()-1, max_card)+1; ++c) {
			for(RawNodeList::iterator it = nodes[c].begin(); it != nodes[c].end(); ++it) {
				shs->push_back(*(*it)->getH());
			}
		}
	}
	return shs;
}

double HsDag::getCalculationTime()
{
	return calculationTime;
}


}
