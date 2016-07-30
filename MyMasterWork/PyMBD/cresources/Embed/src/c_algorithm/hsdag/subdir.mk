################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
../src/c_algorithm/hsdag/Edge.cpp \
../src/c_algorithm/hsdag/Graph.cpp \
../src/c_algorithm/hsdag/HsDag.cpp \
../src/c_algorithm/hsdag/Node.cpp 

OBJS += \
./src/c_algorithm/hsdag/Edge.o \
./src/c_algorithm/hsdag/Graph.o \
./src/c_algorithm/hsdag/HsDag.o \
./src/c_algorithm/hsdag/Node.o 

CPP_DEPS += \
./src/c_algorithm/hsdag/Edge.d \
./src/c_algorithm/hsdag/Graph.d \
./src/c_algorithm/hsdag/HsDag.d \
./src/c_algorithm/hsdag/Node.d 


# Each subdirectory must supply rules for building sources it contributes
src/c_algorithm/hsdag/%.o: ../src/c_algorithm/hsdag/%.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -I/opt/local/Library/Frameworks/Python.framework/Versions/2.7/include/python2.7 -I/usr/local/include/ -I"/Users/tq/Documents/SpecVerify SVN/software/hitting_set/trunk/cresources/src" -I/opt/local/include -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


