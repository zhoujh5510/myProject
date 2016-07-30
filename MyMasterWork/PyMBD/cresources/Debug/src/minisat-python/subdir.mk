################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
../src/minisat-python/MinisatPython.cpp 

OBJS += \
./src/minisat-python/MinisatPython.o 

CPP_DEPS += \
./src/minisat-python/MinisatPython.d 


# Each subdirectory must supply rules for building sources it contributes
src/minisat-python/%.o: ../src/minisat-python/%.cpp
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -D__STDC_LIMIT_MACROS -D__STDC_FORMAT_MACROS -I"/Users/tq/Documents/SpecVerify SVN/software/hitting_set/trunk/lib/minisat" -I/opt/local/include/ -I/opt/local/Library/Frameworks/Python.framework/Versions/2.6/include/python2.6 -O3 -g -Wall -c -fmessage-length=0 -fpic -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


