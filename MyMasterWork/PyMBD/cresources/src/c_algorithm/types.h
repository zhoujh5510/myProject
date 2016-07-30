/*
 * Component.h
 *
 *  Created on: Jun 15, 2011
 *      Author: tq
 */

#ifndef TYPES_H_
#define TYPES_H_
#include <vector>
#include <list>
#include <set>
#include <algorithm>
#include <boost/shared_ptr.hpp>
#include <boost/dynamic_bitset.hpp>
#include <unordered_map>

typedef int Component;
typedef boost::dynamic_bitset<unsigned long, std::allocator<unsigned long> > Bs;
typedef boost::shared_ptr<Bs> BsPtr;
typedef Bs Cs;
typedef boost::shared_ptr<Cs> CsPtr;
typedef std::vector<CsPtr> Scs;
typedef boost::shared_ptr<Scs> ScsPtr;
typedef Bs Hs;
typedef boost::shared_ptr<Hs> HsPtr;
typedef std::vector<Hs> Shs;
typedef boost::shared_ptr<Shs> ShsPtr;
typedef int EdgeLabel;
typedef std::set<CsPtr> CsList;
bool scs_equal(const Scs& cs1, const Scs& cs2);
void pad(Bs& bs1, Bs& bs2);
typedef std::unordered_map<std::string, std::string> HashMapStrStr;

namespace std 
{
   template <>
   struct hash<Bs> : public unary_function<Bs, size_t>
   {
       size_t operator()(const Bs& v) const
       {
    	   vector<Bs::size_type> blocks(v.num_blocks());
           size_t result = 37;
           boost::to_block_range(v, blocks.begin());
           for(vector<Bs::size_type>::iterator it = blocks.begin(); it != blocks.end(); ++it) {
        	   result *= 31;
        	   result += *it;
           }
           return result;
       }
   };
}

bool compare_length(const CsPtr& first, const CsPtr& second);

#endif /* TYPES_H_ */
