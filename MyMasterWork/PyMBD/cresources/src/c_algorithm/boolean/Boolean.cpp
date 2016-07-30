/*
 * Boolean.cpp
 *
 *  Created on: Aug 4, 2011
 *      Author: tq
 */

#include "Boolean.h"
#include "../debug.h"
#include <boost/python/extract.hpp>
#include <algorithm>
using namespace boost::python;

void expose_boolean() {

	class_<boolean::Worklist>("Worklist", no_init)
		.def("get_hitting_sets", &boolean::Worklist::getHittingSets);

	class_<boolean::Boolean>("Boolean")
		.def("boolean_iterative", &boolean::Boolean::boolean_iterative)
		.def("get_calculation_time", &boolean::Boolean::get_calculation_time);

	register_ptr_to_python<boolean::WorklistPtr>();

}

namespace boolean {

Boolean::Boolean()
{

}

Boolean::~Boolean()
{

}

WorklistPtr Boolean::boolean_iterative(Description description, unsigned long max_card, WorklistPtr previous_worklist, float max_time)
{
	WorklistPtr w;
	timer.restart();
	if(previous_worklist) {
		w = previous_worklist;
	} else {
		ScsPtr scs = description.getConflictSets();
		w = WorklistPtr(new Worklist(scs));
	}

	unsigned int card = 0;
	while(card <= w->getMaxCardInTodo()) {
		process(w, card, max_time, max_card);
		card++;
		if(card > max_card) {
			break;
		}
	}

//	debug(*w);
	minimize_finished(w);
//	debug(*w);
	calculationTime = timer.elapsed();
	return w;
}

void Boolean::process(WorklistPtr& w, unsigned int card, float max_time, unsigned int max_card)
{
	while(w->hasTodo(card)) {
		if(max_time > 0 && timer.elapsed() > max_time) {
			break;
		}
		WorklistItem item = w->getNextTodo(card);
		std::list<WorklistItem> result = h_iterative(item, max_card);
		for(std::list<WorklistItem>::iterator it = result.begin(); it != result.end(); ++it) {
			if(it->c->size() == 0) {
				w->addFinished(*it);
			} else {
				w->addTodo(*it);
			}
		}
//		debug(*w);
	}
}

std::list<WorklistItem> Boolean::h_iterative(WorklistItem& item, unsigned int max_card)
{
	std::list<WorklistItem> result;

	// Rule 1: H(F) = T
	if(item.c->size() == 0 || (item.c->size() == 1 && item.c->front()->count() == 0)) {
//		std::cout << "executing rule 1" << std::endl;
		result.push_back(WorklistItem(item.h, ScsPtr(new Scs())));
		return result;
	}

    // OPTIMIZATION: at level max_card stop after rule (1)
    // Thomas Quaritsch, 2012-02-03
	if(item.h->count() >= max_card) {
	    return result;
	}

	// Rule 2: H(/e) = e
	if(item.c->size() == 1 && item.c->front()->count() == 1) {
//		std::cout << "executing rule 2" << std::endl;
		item.h->set(item.c->front()->find_first());
		result.push_back(WorklistItem(item.h, ScsPtr(new Scs())));
		return result;
	}
	

	// Rule 3: H(/eC) = e + H(C)
	if(item.c->size() == 1 && item.c->front()->count() > 1) {
//		std::cout << "executing rule 3" << std::endl;
		unsigned int e = item.c->front()->find_first();
		ScsPtr c(new Scs());
		c->push_back(CsPtr(new Cs(*item.c->front())));
		c->front()->reset(e);
		HsPtr h(new Hs(*item.h));
		h->set(e);
		result.push_back(WorklistItem(h, ScsPtr(new Scs())));
		result.push_back(WorklistItem(item.h, c));
		return result;
	}

	// Rule 4: H(/e + C) = e H(C1) with C1 = {all c in C such that /e not in c}
	// NOTE: this rule has been modified from the original algorithm description where the result
	// of this rule was e H(C). This reduces the number of non-minimal hitting sets
	for(Scs::iterator cs = item.c->begin(); cs != item.c->end(); ++cs) {
		if((*cs)->count() == 1) {
//			std::cout << "executing rule 4" << std::endl;
			unsigned int e = (*cs)->find_first();
			ScsPtr c1(new Scs());
			for(Scs::iterator i = item.c->begin(); i != item.c->end(); ++i) {
				if(!(*i)->test(e)) {
					c1->push_back(*i);
				}
			}
			item.h->set(e);
			result.push_back(WorklistItem(item.h, c1));
			return result;
		}
	}

	// Rule 5: H(C) = e H(C1) + H(C2) where
    // C1 = {all c in C such that /e not in c} (i.e. all conflict sets not containing /e), and
    // C2 = {all c such that (c U /e in C) OR (c in C and /e not in c)}, (i.e. all conflict sets
    //       with /e removed and all conflict sets not containing /e (=C1))
//	std::cout << "executing rule 5" << std::endl;
	unsigned int e = get_most_common_element(item.c);
	ScsPtr c1(new Scs());
	ScsPtr c2(new Scs());
	for(Scs::iterator i = item.c->begin(); i != item.c->end(); ++i) {
		if(!(*i)->test(e)) {
			c1->push_back(CsPtr(new Cs(**i)));
			c2->push_back(CsPtr(new Cs(**i)));
		} else {
    		CsPtr c = CsPtr(new Cs(**i));
    		c->reset(e);
    		bool found = false;
    		for(Scs::iterator i2 = c2->begin(); i2 != c2->end(); ++i2) {
    			if(**i2 == *c) {
    				found = true;
    				break;
    			}
    		}
    		if(!found) {
    			c2->push_back(c);
    		}
	    }
	}
	HsPtr h(new Hs(*item.h));
	h->set(e);
	result.push_back(WorklistItem(h, c1));
	result.push_back(WorklistItem(item.h, c2));
	return result;

}

void Boolean::minimize_finished(WorklistPtr& w)
{
	HsByCard& finished = w->getFinished();
	for(unsigned int l = 1; l < finished.size(); ++l) {
		std::list<HsPtr>& finished_l = finished[l];
		for(std::list<HsPtr>::iterator hs = finished_l.begin(); hs != finished_l.end();) {
			if(check_superset(l, *hs, finished)) {
//				std::cout << "erasing ";
//				debug_setformat(**hs);
//				std::cout << std::endl;
				hs = finished_l.erase(hs);
			} else {
				hs++;
			}
		}
	}
}

bool Boolean::check_superset(unsigned int l, HsPtr& hs, HsByCard& finished)
{
	for(unsigned int i = 0; i < l; i++) {
		std::list<HsPtr>& finished_i = finished[i];
		for(std::list<HsPtr>::iterator other = finished_i.begin(); other != finished_i.end(); ++other) {
//			std::cout << "is ";
//			debug_setformat(**other);
//			std::cout << " subset of ";
//			debug_setformat(*hs);
//			std::cout << "?";
			if((*other)->is_subset_of(*hs)) {
//				std::cout << "yes" << std::endl;
				return true;
			} else {
//				std::cout << "no" << std::endl;
			}
		}
	}
	return false;
}

// TODO: implement check_subset which does the check the other way around (i.e. for a
// given HS, checks if any set with greater cardinality is a superset, i.o.w. if the
// HS is a subset.

unsigned int Boolean::get_most_common_element(ScsPtr& scs)
{
	vector<unsigned int> count(scs->front()->size(), 0);
	for(Scs::iterator it = scs->begin(); it != scs->end(); ++it) {
		size_t c = (*it)->find_first();
		while(c != (*it)->npos) {
			count[c]++;
			c = (*it)->find_next(c);
		}
	}
	return max_element(count.begin(), count.end()) - count.begin();
}

double Boolean::get_calculation_time()
{
	return calculationTime;
}

}
