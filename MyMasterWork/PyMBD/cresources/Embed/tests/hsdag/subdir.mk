################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
../tests/hsdag/GraphTest.cpp \
../tests/hsdag/HsDagTest.cpp 

OBJS += \
./tests/hsdag/GraphTest.o \
./tests/hsdag/HsDagTest.o 

CPP_DEPS += \
./tests/hsdag/GraphTest.d \
./tests/hsdag/HsDagTest.d 


# Each subdirectory must supply rules for building sources it contributes
tests/hsdag/%.o: ../tests/hsdag/%.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -I/opt/local/Library/Frameworks/Python.framework/Versions/2.7/include/python2.7 -I/usr/local/include/ -I"/Users/tq/Documents/SpecVerify SVN/software/hitting_set/trunk/cresources/src" -I/opt/local/include -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


