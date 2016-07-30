/*
 * Test.cpp
 *
 *  Created on: Jun 16, 2011
 *      Author: tq
 */

#include <cppunit/CompilerOutputter.h>
#include <cppunit/extensions/TestFactoryRegistry.h>
#include <cppunit/TestResult.h>
#include <cppunit/TestResultCollector.h>
#include <cppunit/TestRunner.h>
#include <cppunit/BriefTestProgressListener.h>

int main (int argc, char* argv[])
{
    CPPUNIT_NS :: TestResult testresult;
    CPPUNIT_NS :: TestResultCollector collectedresults;
    testresult.addListener (&collectedresults);
    CPPUNIT_NS :: BriefTestProgressListener progress;
    testresult.addListener (&progress);
    CPPUNIT_NS :: TestRunner testrunner;
    testrunner.addTest (CPPUNIT_NS :: TestFactoryRegistry :: getRegistry ().makeTest ());
    testrunner.run (testresult);
    CPPUNIT_NS :: CompilerOutputter compileroutputter (&collectedresults, std::cerr);
    compileroutputter.write ();
    return collectedresults.wasSuccessful () ? 0 : 1;
}
