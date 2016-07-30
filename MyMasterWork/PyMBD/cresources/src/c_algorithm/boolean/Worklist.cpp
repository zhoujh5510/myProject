/*
 * Worklist.cpp
 *
 *  Created on: Aug 4, 2011
 *      Author: tq
 */

#include "Worklist.h"
#include "../Description.h"
#include <algorithm>
using std::list;

namespace boolean {

Worklist::Worklist(ScsPtr initialConflictSets)
{
	list<WorklistItem> initialTodo;
	WorklistItem all(HsPtr(new Hs(Description::SIZE)), initialConflictSets);
	initialTodo.push_back(all);
	todo.push_back(initialTodo);
}

Worklist::~Worklist()
{

}

bool Worklist::hasTodo(unsigned int cardinality)
{
	return todo.size() > cardinality && !todo[cardinality].empty();
}

WorklistItem Worklist::getNextTodo(unsigned int cardinality)
{
	WorklistItem nextTodo = todo[cardinality].front();
	todo[cardinality].pop_front();
	return nextTodo;
}

void Worklist::addFinished(WorklistItem item)
{
	unsigned int card = item.h->count();
	// dear future me: if you change something about
	// the indexing here, think 10 times about it!
	// FINISHED is off by one
	if(card > finished.size()) {
		finished.resize(card, list<HsPtr>());
	}
	finished[card-1].push_back(item.h);
}

void Worklist::addTodo(WorklistItem item)
{
	unsigned int card = item.h->count();
	// dear future me: if you change something about
	// the indexing here, think 10 times about it!
	if(card >= todo.size()) {
		todo.resize(card+1, list<WorklistItem>());
	}
	todo[card].push_back(item);
}

ShsPtr Worklist::getHittingSets(unsigned long min_card, unsigned long max_card)
{
	ShsPtr shs = ShsPtr(new Shs());
	if(min_card < 1) {
		min_card = 1;
	}
	if(min_card > finished.size()) {
		return shs;
	}
	size_t max = std::min((unsigned long)finished.size(), max_card);
	for(size_t card = min_card-1; card <= max-1; ++card) {
		for(std::list<HsPtr>::iterator hs = finished[card].begin(); hs != finished[card].end(); ++hs) {
			shs->push_back(**hs);
		}
	}
	return shs;
}

unsigned int Worklist::getMaxCardInTodo()
{
	return todo.size()-1;
}

HsByCard& Worklist::getFinished()
{
	return finished;
}

}
