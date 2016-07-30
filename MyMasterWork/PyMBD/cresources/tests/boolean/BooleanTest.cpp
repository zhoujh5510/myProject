/*
 * BooleanTest.cpp
 *
 *  Created on: Jun 16, 2011
 *      Author: tq
 */

#include <cppunit/extensions/HelperMacros.h>
#include <iostream>
#include "c_algorithm/boolean/Boolean.h"
#include "c_algorithm/Description.h"
#include "c_algorithm/DescriptionProxy.h"
#include "c_algorithm/debug.h"
#include "c_algorithm/python_types.h"
#include "c_algorithm/hsdag/Node.h"
#include "c_algorithm/hsdag/Edge.h"

using std::cout;
using std::endl;
using std::string;

namespace boolean {

class BooleanTest : public CPPUNIT_NS::TestFixture
{
	 CPPUNIT_TEST_SUITE( BooleanTest );
//	 CPPUNIT_TEST( testSimpleExample );
	 CPPUNIT_TEST( testPerformance );

	 CPPUNIT_TEST_SUITE_END();

public:
	 void testSimpleExample();
	 void testPerformance();

};

//CPPUNIT_TEST_SUITE_REGISTRATION( BooleanTest );

void BooleanTest::testSimpleExample()
{
	Description::SIZE = 3;
	ScsPtr scs(new Scs());
	scs->push_back(CsPtr(new Cs(string("011"))));
	scs->push_back(CsPtr(new Cs(string("110"))));
	Description o(scs);
 	WorklistPtr w = Boolean().boolean_iterative(o, 10, WorklistPtr(), 0.0);
	ShsPtr found = w->getHittingSets(1, 10);
	for(Shs::iterator it = found->begin(); it != found->end(); ++it) {
		cout << "HS: " << *it << endl;
	}

}

void BooleanTest::testPerformance()
{
	Description::SIZE = 30;
	ScsPtr scs(new Scs());
	scs->push_back(CsPtr(new Cs(string("001000000010000000100000001000"))));
	scs->push_back(CsPtr(new Cs(string("000000100000001000000010000000"))));
	scs->push_back(CsPtr(new Cs(string("000100000001000000010000000100"))));
	scs->push_back(CsPtr(new Cs(string("010000000100000001000000010000"))));
	scs->push_back(CsPtr(new Cs(string("000001000000010000000100000001"))));
	scs->push_back(CsPtr(new Cs(string("000000010000000100000001000000"))));
	scs->push_back(CsPtr(new Cs(string("100000001000000010000000100000"))));
	scs->push_back(CsPtr(new Cs(string("000010000000100000001000000010"))));
	Description o(scs);
 	WorklistPtr w = Boolean().boolean_iterative(o, 9999, WorklistPtr(), 0.0);
	ShsPtr found = w->getHittingSets(1, 10);
}

}

