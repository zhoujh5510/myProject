/*
 * debug.h
 *
 *  Created on: Jul 21, 2011
 *      Author: tq
 */

#ifndef DEBUG_H_
#define DEBUG_H_

#include "types.h"
#include "hsdag/types.h"
#include "boolean/Worklist.h"

void debug(hsdag::HashMapBs2NodeList& set_cache);
void debug(hsdag::NodeList& node_list);
void debug(hsdag::NodeSet& node_list);
void debug(boolean::Worklist& worklist);
void debug_setformat(Cs& cs);

#endif /* DEBUG_H_ */
