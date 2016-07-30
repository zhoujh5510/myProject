/*
 * GraphTest.cpp
 *
 *  Created on: Jun 16, 2011
 *      Author: tq
 */

#include <cppunit/extensions/HelperMacros.h>
#include <iostream>
#include "c_algorithm/hsdag/Node.h"

using std::cout;
using std::endl;

namespace hsdag {

class GraphTest : public CPPUNIT_NS::TestFixture
{
	 CPPUNIT_TEST_SUITE( GraphTest );
//	 CPPUNIT_TEST( testAddChildShouldAddOutgoingEdge);
//	 CPPUNIT_TEST( testAddChildShouldAddIncomingEdgeOnParent );
//	 CPPUNIT_TEST( testShouldDeleteSubtree );
//	 CPPUNIT_TEST( testShouldDeleteSubgraph );
	 CPPUNIT_TEST_SUITE_END();

public:
	 void testAddChildShouldAddOutgoingEdge();
	 void testAddChildShouldAddIncomingEdgeOnParent();
	 void testShouldDeleteSubtree();
	 void testShouldDeleteSubgraph();
};

//CPPUNIT_TEST_SUITE_REGISTRATION( GraphTest );

void GraphTest::testAddChildShouldAddOutgoingEdge()
{
//	Node *n1 = new Node();
//	Node *n2 = new Node();
//	n1->addChild(n2, 5);
//	NodeListPtr out = n1->getChildren();
//	CPPUNIT_ASSERT_EQUAL(1, (int) out->size());
//	n1->deleteChildren();
//	delete n1;
}

void GraphTest::testAddChildShouldAddIncomingEdgeOnParent()
{

//	Node *n1 = new Node();
//	Node *n2 = new Node();
//	n1->addChild(n2, 5);
//	NodeListPtr in = n2->getIndicents();
//	CPPUNIT_ASSERT_EQUAL(1, (int) in->size());
//	n1->deleteChildren();
//	delete n1;
}

void GraphTest::testShouldDeleteSubtree()
{
//	Node *n1 = new Node();
//	Node *n2 = new Node();
//	Node *n3 = new Node();
//	Node *n4 = new Node();
//	n1->addChild(n2, 1);
//	n1->addChild(n3, 2);
//	n3->addChild(n4, 3);
//	n1->deleteChildren();
//	delete n1;
}

void GraphTest::testShouldDeleteSubgraph()
{
//	Node *n1 = new Node(OPEN, 1);
//	Node *n2 = new Node(OPEN, 2);
//	Node *n3 = new Node(OPEN, 3);
//	Node *n4 = new Node(OPEN, 4);
//	Node *n5 = new Node(OPEN, 5);
//	n1->addChild(n2, 1);
//	n1->addChild(n3, 2);
//	n3->addChild(n4, 3);
//	n2->addChild(n4, 4);
//	n3->addChild(n5, 5);
//
//	// deletes n3 and n5, and edges 1->3, 3->4, 3->5
//	n3->deleteChildren();
//	delete n3;
//
//	CPPUNIT_ASSERT_EQUAL(1, (int) n1->getChildren()->size());
//	CPPUNIT_ASSERT_EQUAL(1, (int) n2->getChildren()->size());
//
//	// deletes n1, n2, and n4 and edges 1->2, 2->4
//	n1->deleteChildren();
//	delete n1;
}

}
