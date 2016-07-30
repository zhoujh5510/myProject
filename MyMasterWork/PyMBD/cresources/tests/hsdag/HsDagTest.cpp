/*
 * HsDagTest.cpp
 *
 *  Created on: Jun 16, 2011
 *      Author: tq
 */

#include <cppunit/extensions/HelperMacros.h>
#include <iostream>
#include "c_algorithm/hsdag/HsDag.h"
#include "c_algorithm/Description.h"
#include "c_algorithm/DescriptionProxy.h"
#include "c_algorithm/debug.h"
#include "c_algorithm/python_types.h"
#include "c_algorithm/hsdag/Node.h"
#include "c_algorithm/hsdag/Edge.h"

using std::cout;
using std::endl;
using std::string;

namespace hsdag {

class HsDagTest : public CPPUNIT_NS::TestFixture
{
	 CPPUNIT_TEST_SUITE( HsDagTest );
//	 CPPUNIT_TEST( testPruning );
//	 CPPUNIT_TEST( testRegressionError1 );
//	 CPPUNIT_TEST( testRegressionError2 );
//	 CPPUNIT_TEST( testRegressionError3 );
	 CPPUNIT_TEST( testMemoryPerformance );

	 CPPUNIT_TEST_SUITE_END();

public:
	 void testPruning();
	 void testRegressionError1();
	 void testRegressionError2();
	 void testRegressionError3();
	 void testMemoryPerformance();

};

CPPUNIT_TEST_SUITE_REGISTRATION( HsDagTest );

void HsDagTest::testPruning()
{
	Description::SIZE = 12;
	ScsPtr scs(new Scs());
//	cout << sizeof(Node) << "/" << sizeof(Edge) << endl;
//	scs->push_back(CsPtr(new Cs(string("0011"))));
//	scs->push_back(CsPtr(new Cs(string("0110"))));
//	scs->push_back(CsPtr(new Cs(string("0101"))));
//	scs->push_back(CsPtr(new Cs(string("1010"))));
//	scs->push_back(CsPtr(new Cs(string("0010"))));
//	frozenset([frozenset([8, 10, 2, 5, 7]), frozenset([8, 1, 11, 9, 7]), frozenset([1])])
	scs->push_back(CsPtr(new Cs(string("010110100100"))));
	scs->push_back(CsPtr(new Cs(string("101110000010"))));
	scs->push_back(CsPtr(new Cs(string("000000000010"))));
	Description o(scs);
	GraphPtr out = HsDag().hsdag_cpp(&o, 9999, GraphPtr(), 0.0, true, true);
}

void HsDagTest::testRegressionError1()
{
	Description::SIZE = 4;
	ScsPtr scs(new Scs());
	scs->push_back(CsPtr(new Cs(string("1101"))));
	scs->push_back(CsPtr(new Cs(string("0111"))));
	scs->push_back(CsPtr(new Cs(string("1110"))));
	scs->push_back(CsPtr(new Cs(string("0010"))));
	Description o(scs);
	GraphPtr out = HsDag().hsdag_cpp(&o, 9999, GraphPtr(), 0.0, true, true);
}

void HsDagTest::testRegressionError2()
{
	Description::SIZE = 6;
	ScsPtr scs(new Scs());
	scs->push_back(CsPtr(new Cs(string("011011"))));
	scs->push_back(CsPtr(new Cs(string("101001"))));
	scs->push_back(CsPtr(new Cs(string("001100"))));
	scs->push_back(CsPtr(new Cs(string("001010"))));
	scs->push_back(CsPtr(new Cs(string("000100"))));
	scs->push_back(CsPtr(new Cs(string("000011"))));
//	scs->push_back(CsPtr(new Cs(string(""))));
	Description o(scs, true);
	GraphPtr out = HsDag().hsdag_cpp(&o, 9999, GraphPtr(), 0.0, true, true);
//	cout << sizeof(Node) << endl;
//	cout << sizeof(Edge) << endl;
}

void HsDagTest::testRegressionError3()
{
	Description::SIZE = 15;
	ScsPtr scs(new Scs());
	scs->push_back(CsPtr(new Cs(string("010100001010110"))));
	scs->push_back(CsPtr(new Cs(string("100110101111101"))));
	scs->push_back(CsPtr(new Cs(string("011000010010110"))));
	scs->push_back(CsPtr(new Cs(string("100110000011010"))));
	scs->push_back(CsPtr(new Cs(string("101101101101100"))));
	scs->push_back(CsPtr(new Cs(string("111101000110110"))));
	scs->push_back(CsPtr(new Cs(string("110010111010111"))));
	scs->push_back(CsPtr(new Cs(string("101001110011001"))));
	scs->push_back(CsPtr(new Cs(string("101101000101010"))));
	scs->push_back(CsPtr(new Cs(string("001110110011010"))));
	scs->push_back(CsPtr(new Cs(string("001101011100001"))));
	scs->push_back(CsPtr(new Cs(string("010001000011000"))));
	scs->push_back(CsPtr(new Cs(string("000011010101101"))));
	scs->push_back(CsPtr(new Cs(string("110001011110000"))));
	scs->push_back(CsPtr(new Cs(string("011101001111100"))));
	scs->push_back(CsPtr(new Cs(string("111001100110100"))));
	scs->push_back(CsPtr(new Cs(string("010101010110110"))));
	scs->push_back(CsPtr(new Cs(string("000000001010110"))));
	Description o(scs, true);
	GraphPtr out = HsDag().hsdag_cpp(&o, 9999, GraphPtr(), 0.0, true, true);
}

void HsDagTest::testMemoryPerformance()
{
	Description::SIZE = 40;
	ScsPtr scs(new Scs());
	scs->push_back(CsPtr(new Cs(string("0000000100000001000000010000000100000001"))));
	scs->push_back(CsPtr(new Cs(string("0010000000100000001000000010000000100000"))));
	scs->push_back(CsPtr(new Cs(string("0000100000001000000010000000100000001000"))));
	scs->push_back(CsPtr(new Cs(string("0100000001000000010000000100000001000000"))));
	scs->push_back(CsPtr(new Cs(string("0000001000000010000000100000001000000010"))));
	scs->push_back(CsPtr(new Cs(string("0001000000010000000100000001000000010000"))));
	scs->push_back(CsPtr(new Cs(string("0000010000000100000001000000010000000100"))));
	scs->push_back(CsPtr(new Cs(string("1000000010000000100000001000000010000000"))));
	Description o(scs, true);
	GraphPtr out = HsDag().hsdag_cpp(&o, 9999, GraphPtr(), 0.0, true, true);
}


}

