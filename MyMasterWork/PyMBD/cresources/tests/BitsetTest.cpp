/*
 * BitsetTest.cpp
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

class BitsetTest : public CPPUNIT_NS::TestFixture
{
	 CPPUNIT_TEST_SUITE( BitsetTest );
//	 CPPUNIT_TEST( testSubset );
//	 CPPUNIT_TEST( testPadding );
	 CPPUNIT_TEST_SUITE_END();

public:
	 void testSubset();
	 void testPadding();
};

//CPPUNIT_TEST_SUITE_REGISTRATION( BitsetTest );

void BitsetTest::testSubset()
{
	dynamic_bitset<> set1(string("0101"));
	dynamic_bitset<> set2(string("100"));
	set2.push_back(0);
	CPPUNIT_ASSERT( set2.is_subset_of(set1) );
	CPPUNIT_ASSERT( set2.is_proper_subset_of(set1) );
	CPPUNIT_ASSERT( ! set1.is_subset_of(set2) );
	CPPUNIT_ASSERT( ! set1.is_proper_subset_of(set2) );
}

void BitsetTest::testPadding()
{

	Bs bs1(string("0111"));
	Bs bs2(string( "101"));
	pad(bs1, bs2);
	CPPUNIT_ASSERT_EQUAL( 4, (int) bs1.size() );
	CPPUNIT_ASSERT_EQUAL( 4, (int) bs2.size() );
	CPPUNIT_ASSERT_EQUAL( 7, (int) bs1.to_ulong() );
	CPPUNIT_ASSERT_EQUAL( 5, (int) bs2.to_ulong() );

}
