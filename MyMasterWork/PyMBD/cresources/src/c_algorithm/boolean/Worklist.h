/*
 * Worklist.h
 *
 *  Created on: Aug 4, 2011
 *      Author: tq
 */

#ifndef WORKLIST_H_
#define WORKLIST_H_
#include "../types.h"
#include "types.h"
#include <boost/shared_ptr.hpp>
#include <list>
using std::vector;
using std::list;
using boost::shared_ptr;

namespace boolean {

class Worklist
{
public:
	/**
	 * a vector containing lists of WorklistItems by cardinality of its hitting set, e.g.
	 * todo[0] contains all undone WorklistItems with |h| = 0
	 */
	WorklistItemsByCard todo;
	/**
	 * a vector containing lists of results (hitting sets) by their cardinality. as there is
	 * no HS with cardinality 0, the list indexes are off by one, e.g.
	 * finished[0] contains all hitting sets with |HS| = 1
	 * finished[1] contains all hitting sets with |HS| = 2
	 */
	HsByCard finished;

public:
	Worklist(ScsPtr initialConflictSets);
	virtual ~Worklist();
	virtual bool hasTodo(unsigned int cardinality);
	virtual WorklistItem getNextTodo(unsigned int cardinality);
	virtual void addFinished(WorklistItem item);
	virtual HsByCard& getFinished();
	virtual void addTodo(WorklistItem item);
	virtual ShsPtr getHittingSets(unsigned long min_card, unsigned long max_card);
	virtual unsigned int getMaxCardInTodo();

};

typedef shared_ptr<Worklist> WorklistPtr;

}

#endif /* WORKLIST_H_ */
