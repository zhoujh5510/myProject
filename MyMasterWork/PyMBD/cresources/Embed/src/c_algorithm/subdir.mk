################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
../src/c_algorithm/Oracle.cpp \
../src/c_algorithm/python_types.cpp \
../src/c_algorithm/types.cpp 

OBJS += \
./src/c_algorithm/Oracle.o \
./src/c_algorithm/python_types.o \
./src/c_algorithm/types.o 

CPP_DEPS += \
./src/c_algorithm/Oracle.d \
./src/c_algorithm/python_types.d \
./src/c_algorithm/types.d 


# Each subdirectory must supply rules for building sources it contributes
src/c_algorithm/%.o: ../src/c_algorithm/%.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -I/opt/local/Library/Frameworks/Python.framework/Versions/2.7/include/python2.7 -I/usr/local/include/ -I"/Users/tq/Documents/SpecVerify SVN/software/hitting_set/trunk/cresources/src" -I/opt/local/include -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


