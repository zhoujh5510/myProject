1.BFSD.cpp文件是自己实现的算法,在该算法中会用到picosat solver.该算法利用枚举树按层次遍历优先的策略求解基于模型的诊断问题.
2.文件夹内包含了PicoSAT solver相关的文件.
3.可以调用的API可以在'picosat.h'文件中查看.
4.编译的步骤是先执行./configure 和 make.  然后执行g++ -c BFSD.cpp picosat.c 最后执行g++ -o picosat.o BFSD.o -o BFSD
5.执行./BFSD "文件名" "极小诊断长度".
