/*
 * DescriptionTest.cpp
 *
 *  Created on: Jun 16, 2011
 *      Author: tq
 */

#include <cppunit/extensions/HelperMacros.h>
#include <iostream>
#include <algorithm>
#include "c_algorithm/hsdag/Node.h"
#include "c_algorithm/Description.h"
#include "c_algorithm/python_types.h"

using std::cout;
using std::endl;

class DescriptionTest : public CPPUNIT_NS::TestFixture
{
	 CPPUNIT_TEST_SUITE( DescriptionTest );
//	 CPPUNIT_TEST( testShouldReturnConflictSets );
	 CPPUNIT_TEST_SUITE_END();

public:
	 void testShouldReturnConflictSets();
};

//CPPUNIT_TEST_SUITE_REGISTRATION( DescriptionTest );

void DescriptionTest::testShouldReturnConflictSets()
{
	Description::SIZE = 5;
	ScsPtr scs(new Scs());
	CsPtr cs1(new Cs(std::string("01001")));
	CsPtr cs2(new Cs(std::string("00100")));
	scs->push_back(cs1);
	scs->push_back(cs2);
	Description o(scs, false);
	CsPtr got1 = o.getConflictSet(HsPtr(new Hs()));
	CsPtr got2 = o.getConflictSet(HsPtr(new Hs(std::string("1"))));
	Cs expected1(std::string("01001"));
	Cs expected2(std::string("00100"));
	CPPUNIT_ASSERT(*got1 == expected1);
	CPPUNIT_ASSERT(*got2 == expected2);
}

