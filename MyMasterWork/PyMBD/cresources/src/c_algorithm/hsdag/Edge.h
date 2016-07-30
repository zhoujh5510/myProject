/*
 * Edge.h
 *
 *  Created on: Jun 15, 2011
 *      Author: tq
 */

#ifndef EDGE_H_
#define EDGE_H_
#include "Node.h"
#include "types.h"

namespace hsdag
{

class Edge
{

protected:

	NodeId src;
	NodeId dst;
	EdgeLabel label;

public:
	Edge(NodeId src, NodeId dst, EdgeLabel label);
	~Edge();
	NodeId getDst() const;
	NodeId getSrc() const;
	void setDst(NodeId dst);
	void setSrc(NodeId src);
	EdgeLabel getLabel() const;
    void setLabel(EdgeLabel label);

};

}

#endif /* EDGE_H_ */
