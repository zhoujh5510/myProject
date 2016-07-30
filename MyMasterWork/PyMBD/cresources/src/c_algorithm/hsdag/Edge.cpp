/*
 * Node.h
 *
 *  Created on: Jun 15, 2011
 *      Author: tq
 */
#include "Edge.h"
#include <iostream>
using std::cout;
using std::endl;

namespace hsdag
{

Edge::Edge(NodeId src, NodeId dst, EdgeLabel lbl) :
		src(src), dst(dst), label(lbl)
{

}

Edge::~Edge()
{

}

NodeId Edge::getDst() const
{
	return dst;
}

NodeId Edge::getSrc() const
{
	return src;
}

void Edge::setDst(NodeId dst)
{
	this->dst = dst;
}

int Edge::getLabel() const
{
	return label;
}

void Edge::setLabel(int label)
{
	this->label = label;
}

void Edge::setSrc(NodeId src)
{
	this->src = src;
}

}
