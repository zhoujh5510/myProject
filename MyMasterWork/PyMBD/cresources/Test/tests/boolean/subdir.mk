################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
../tests/boolean/BooleanTest.cpp 

OBJS += \
./tests/boolean/BooleanTest.o 

CPP_DEPS += \
./tests/boolean/BooleanTest.d 


# Each subdirectory must supply rules for building sources it contributes
tests/boolean/%.o: ../tests/boolean/%.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -DBOOST_DATE_TIME_NO_LOCALE -I"/Users/tq/Documents/SpecVerify SVN/software/hitting_set/trunk/cresources/src" -I/opt/local/include/ -I/opt/local/Library/Frameworks/Python.framework/Versions/2.6/include/python2.6 -O0 -g3 -pg -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


