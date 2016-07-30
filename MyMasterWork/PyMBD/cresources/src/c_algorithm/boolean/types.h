/*
 * types.h
 *
 *  Created on: Aug 4, 2011
 *      Author: tq
 */

#ifndef BOOLEAN_TYPES_H_
#define BOOLEAN_TYPES_H_
#include <vector>
#include <list>

namespace boolean {

struct WorklistItem
{
	WorklistItem(HsPtr h, ScsPtr c): h(h), c(c) {}
	HsPtr h;
	ScsPtr c;
};

typedef std::vector<std::list<WorklistItem> > WorklistItemsByCard;
typedef std::vector<std::list<HsPtr> > HsByCard;

}

#endif /* BOOLEAN_TYPES_H_ */
