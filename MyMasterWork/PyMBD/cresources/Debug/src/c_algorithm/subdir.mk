################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
../src/c_algorithm/CppHittingSet.cpp \
../src/c_algorithm/Description.cpp \
../src/c_algorithm/DescriptionProxy.cpp \
../src/c_algorithm/Timer.cpp \
../src/c_algorithm/debug.cpp \
../src/c_algorithm/python_types.cpp \
../src/c_algorithm/types.cpp 

OBJS += \
./src/c_algorithm/CppHittingSet.o \
./src/c_algorithm/Description.o \
./src/c_algorithm/DescriptionProxy.o \
./src/c_algorithm/Timer.o \
./src/c_algorithm/debug.o \
./src/c_algorithm/python_types.o \
./src/c_algorithm/types.o 

CPP_DEPS += \
./src/c_algorithm/CppHittingSet.d \
./src/c_algorithm/Description.d \
./src/c_algorithm/DescriptionProxy.d \
./src/c_algorithm/Timer.d \
./src/c_algorithm/debug.d \
./src/c_algorithm/python_types.d \
./src/c_algorithm/types.d 


# Each subdirectory must supply rules for building sources it contributes
src/c_algorithm/%.o: ../src/c_algorithm/%.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -D__STDC_LIMIT_MACROS -D__STDC_FORMAT_MACROS -I"/Users/tq/Documents/SpecVerify SVN/software/hitting_set/trunk/lib/minisat" -I/opt/local/include/ -I/opt/local/Library/Frameworks/Python.framework/Versions/2.6/include/python2.6 -O3 -g -Wall -c -fmessage-length=0 -fpic -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


