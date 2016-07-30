/*
 * Description.h
 *
 *  Created on: Jun 16, 2011
 *      Author: tq
 */

#ifndef DESCRIPTION_H_
#define DESCRIPTION_H_
#include "types.h"
#include "Timer.h"
#include <list>

class Description
{
protected:
	ScsPtr sets;
	Bs components;
	unsigned long int numChecks;
	unsigned long int numComps;
	float timeChecks;
	float timeComps;
	Timer timer;

public:
	Description(ScsPtr sets, bool sort=true);
	virtual ~Description();
	virtual CsPtr getFirstConflictSet();
	virtual CsPtr getConflictSet(HsPtr h);
	virtual bool checkConsistency(HsPtr h);
	virtual std::list<int> getComponents();
	virtual int getNumCalls();
	virtual int getCheckCalls();
	virtual int getCompCalls();
	virtual float getTotalTime();
	virtual float getCheckTime();
	virtual float getCompTime();
	virtual int getNumComponents();
	virtual ScsPtr getConflictSets();
	virtual int debug();
	static int SIZE;

};

void expose_description();

#endif /* DESCRIPTION_H_ */
