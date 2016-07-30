/*
 * Timer.h
 *
 *  Created on: Aug 2, 2011
 *      Author: tq
 */

#ifndef TIMER_H_
#define TIMER_H_
#include <boost/date_time.hpp>

class Timer
{
protected:
	boost::posix_time::ptime start;

public:
	Timer();
	virtual ~Timer();
	virtual void restart();
	virtual double elapsed();
};

#endif /* TIMER_H_ */
