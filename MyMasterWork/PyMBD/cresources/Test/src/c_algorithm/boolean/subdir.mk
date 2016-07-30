################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
../src/c_algorithm/boolean/Boolean.cpp \
../src/c_algorithm/boolean/Worklist.cpp 

OBJS += \
./src/c_algorithm/boolean/Boolean.o \
./src/c_algorithm/boolean/Worklist.o 

CPP_DEPS += \
./src/c_algorithm/boolean/Boolean.d \
./src/c_algorithm/boolean/Worklist.d 


# Each subdirectory must supply rules for building sources it contributes
src/c_algorithm/boolean/%.o: ../src/c_algorithm/boolean/%.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -DBOOST_DATE_TIME_NO_LOCALE -I"/Users/tq/Documents/SpecVerify SVN/software/hitting_set/trunk/cresources/src" -I/opt/local/include/ -I/opt/local/Library/Frameworks/Python.framework/Versions/2.6/include/python2.6 -O0 -g3 -pg -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


