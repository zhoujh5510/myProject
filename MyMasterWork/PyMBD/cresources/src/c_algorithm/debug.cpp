/*
 * debug.cpp
 *
 *  Created on: Jul 21, 2011
 *      Author: tq
 */

#include "debug.h"
#include "types.h"
#include <iostream>

using namespace hsdag;
using namespace std;
using namespace boolean;

void debug(HashMapBs2NodeList& set_cache)
{
	string separator("");
	cout << "set_cache:" << endl;
	for(HashMapBs2NodeList::iterator it = set_cache.begin(); it != set_cache.end(); ++it) {
		cout << it->first << ": ";
		debug(it->second);
	}
	cout << "----------" << endl;
}

void debug(NodeList& node_list)
{
	string separator = "";
	for(NodeList::iterator nl_it = node_list.begin(); nl_it != node_list.end(); ++nl_it) {
		cout << separator << *nl_it;
		separator = ", ";
	}
	cout << endl;
}

void debug(NodeSet& node_list)
{
	string separator = "";
	for(NodeSet::iterator nl_it = node_list.begin(); nl_it != node_list.end(); ++nl_it) {
		cout << separator << *nl_it;
		separator = ", ";
	}
	cout << endl;
}

void debug_setformat(Cs& cs) {
	Cs::size_type i = cs.find_first();
	cout << "{";
	string separator = "";
	while(i != cs.npos) {
		cout << separator << i;
		separator = ",";
		i = cs.find_next(i);
	}
	cout << "}";
}

void debug(boolean::Worklist& worklist)
{
	cout << "===============" << endl;
	std::string sep1 = "";
	for(std::vector<std::list<WorklistItem> >::iterator i1 = worklist.todo.begin(); i1 != worklist.todo.end(); ++i1) {
//		cout << "[" << i1-worklist.todo.begin() << "] ";
		cout << sep1;
		for(std::list<WorklistItem>::iterator i2 = i1->begin(); i2 != i1->end(); ++i2) {
			if(i2->h->count() > 0) {
				debug_setformat(*i2->h);
			}
			cout << " H( ";
			std::string separator = "";
			for(Scs::iterator i3 = i2->c->begin(); i3 != i2->c->end(); ++i3) {
				cout << separator;
				debug_setformat(**i3);
				separator = " + ";
			}
			cout << " ) ";
//			cout << endl;
		}
//		if(i1->empty()) {
//			cout << endl;
//		}
		sep1 = " + ";
	}
	cout << endl;
	std::string separator = "";
	for(std::vector<std::list<HsPtr> >::iterator i1 = worklist.finished.begin(); i1 != worklist.finished.end(); ++i1) {
		cout << "[" << i1-worklist.finished.begin() << "] HS: ";
		for(std::list<HsPtr>::iterator i2 = i1->begin(); i2 != i1->end(); ++i2) {
			cout << separator;
			debug_setformat(**i2);
			separator = ", ";
		}
		cout << endl;
	}
	cout << "===============" << endl;
}
