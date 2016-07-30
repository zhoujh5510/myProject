/*
 * typesTest.cpp
 *
 *  Created on: Jun 16, 2011
 *      Author: tq
 */

#include <cppunit/extensions/HelperMacros.h>
#include <iostream>
#include <algorithm>
#include <boost/dynamic_bitset.hpp>
#include "c_algorithm/types.h"

using boost::dynamic_bitset;
using std::string;
using std::cout;
using std::endl;

class typesTest : public CPPUNIT_NS::TestFixture
{
	 CPPUNIT_TEST_SUITE( typesTest );
//	 CPPUNIT_TEST( testScsEqual );
	 CPPUNIT_TEST_SUITE_END();

public:
	 void testScsEqual();
};

//CPPUNIT_TEST_SUITE_REGISTRATION( typesTest );

void typesTest::testScsEqual()
{
	CsPtr set1(new Cs(string("1001")));
	CsPtr set2(new Cs(string("1000")));
	Scs scs1;
	Scs scs2;
	scs1.push_back(set1);
	scs2.push_back(set1);
	CPPUNIT_ASSERT( scs_equal(scs1, scs2) );
	scs2.push_back(set2);
	CPPUNIT_ASSERT( ! scs_equal(scs1, scs2) );
	scs1.clear();
	scs1.push_back(set2);
	scs1.push_back(set1);
	CPPUNIT_ASSERT( scs_equal(scs1, scs2) );
}
