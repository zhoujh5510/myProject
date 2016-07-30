#include <iostream>
#include "hsdag/Edge.h"
#include "hsdag/Node.h"
#include "hsdag/Graph.h"
#include "hsdag/HsDag.h"
#include "boolean/Boolean.h"
#include "types.h"
#include "python_types.h"
#include "Description.h"
#include <boost/python.hpp>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>

using namespace boost::python;

void setProblemSize(int size) {
//	std::cout << "setting problem size to " << size << std::endl;
	Description::SIZE = size;
}

BOOST_PYTHON_MODULE(_c_algorithm)
{

	register_types();
	expose_description();
	expose_hsdag();
	expose_boolean();

	scope().attr("set_problem_size") = make_function(&setProblemSize);
}



