/*
 * Timer.cpp
 *
 *  Created on: Aug 2, 2011
 *      Author: tq
 */

#include "Timer.h"
using namespace boost::posix_time;

Timer::Timer()
{
	restart();
}

Timer::~Timer()
{
}

void Timer::restart()
{
	start = microsec_clock::local_time();
}

double Timer::elapsed()
{
	ptime end = microsec_clock::local_time();
	time_duration time = end - start;
	return (double) time.total_nanoseconds() / 1e9;
}


