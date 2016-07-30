#!/usr/bin/env python
 
from distutils.core import setup
from distutils.extension import Extension
from glob import glob

# stolen from http://www.mail-archive.com/distutils-sig@python.org/msg05262.html
# by Andreas Kloeckner
def hack_distutils(debug=False, fast_link=True):
    # hack distutils.sysconfig to eliminate debug flags
    # stolen from mpi4py

    def remove_prefixes(optlist, bad_prefixes):
        for bad_prefix in bad_prefixes:
            for i, flag in enumerate(optlist):
                if flag.startswith(bad_prefix):
                    optlist.pop(i)
                    break
        return optlist

    import sys
    if not sys.platform.lower().startswith("win"):
        from distutils import sysconfig

        cvars = sysconfig.get_config_vars()
        cflags = cvars.get('OPT')
        if cflags:
            cflags = remove_prefixes(cflags.split(),
                    ['-g', '-O', '-Wstrict-prototypes', '-DNDEBUG'])
            if debug:
                cflags.append("-g")
            else:
                cflags.append("-O3")
                cflags.append("-DNDEBUG")
            cvars['OPT'] = str.join(' ', cflags)
            cvars["CFLAGS"] = cvars["BASECFLAGS"] + " " + cvars["OPT"]
       
        if fast_link:
            for varname in ["LDSHARED", "BLDSHARED"]:
                ldsharedflags = cvars.get(varname)
                if ldsharedflags:
                    ldsharedflags = remove_prefixes(ldsharedflags.split(),
                            ['-Wl,-O'])
                    cvars[varname] = str.join(' ', ldsharedflags)

#from distutils import sysconfig
#print sysconfig.get_config_vars()['OPT']
            
hack_distutils()
                    
setup(
    name="cpp_hittingset",
    version='0.0.1',
    description='C++ Hitting Set Algorithms',
    author='Thomas Quaritsch',
    author_email='quaritsch@ist.tugraz.at',
    ext_modules=[
        Extension("_c_algorithm", glob("*.cpp") + glob("*/*.cpp"),
		include_dirs=["/opt/local/include", "/usr/include"],
		library_dirs = ["/opt/local/lib/", "/usr/lib"],
        libraries = ["boost_python"], 
        language="c++")
    ]
)

