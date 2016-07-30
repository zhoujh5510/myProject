################################################################################
# Automatically-generated file. Do not edit!
################################################################################

-include ../makefile.init

RM := rm -rf

# All of the sources participating in the build are defined here
-include sources.mk
-include subdir.mk
-include tests/subdir.mk
-include tests/hsdag/subdir.mk
-include tests/boolean/subdir.mk
-include src/c_algorithm/subdir.mk
-include src/c_algorithm/hsdag/subdir.mk
-include src/c_algorithm/build/temp.macosx-10.6-x86_64-2.7/subdir.mk
-include src/c_algorithm/build/temp.macosx-10.6-x86_64-2.7/hsdag/subdir.mk
-include src/c_algorithm/build/temp.macosx-10.6-x86_64-2.7/boolean/subdir.mk
-include src/c_algorithm/build/temp.linux-i686-2.7-pydebug/subdir.mk
-include src/c_algorithm/build/temp.linux-i686-2.7-pydebug/hsdag/subdir.mk
-include src/c_algorithm/build/temp.linux-i686-2.7/subdir.mk
-include src/c_algorithm/build/temp.linux-i686-2.7/hsdag/subdir.mk
-include src/c_algorithm/build/temp.linux-i686-2.6/subdir.mk
-include src/c_algorithm/build/temp.linux-i686-2.6/hsdag/subdir.mk
-include src/c_algorithm/build/temp.linux-i686-2.6/boolean/subdir.mk
-include src/c_algorithm/boolean/subdir.mk
-include objects.mk

ifneq ($(MAKECMDGOALS),clean)
ifneq ($(strip $(C++_DEPS)),)
-include $(C++_DEPS)
endif
ifneq ($(strip $(C_DEPS)),)
-include $(C_DEPS)
endif
ifneq ($(strip $(CC_DEPS)),)
-include $(CC_DEPS)
endif
ifneq ($(strip $(CPP_DEPS)),)
-include $(CPP_DEPS)
endif
ifneq ($(strip $(CXX_DEPS)),)
-include $(CXX_DEPS)
endif
ifneq ($(strip $(C_UPPER_DEPS)),)
-include $(C_UPPER_DEPS)
endif
endif

-include ../makefile.defs

# Add inputs and outputs from these tool invocations to the build variables 

# All Target
all: RunTests

# Tool invocations
RunTests: $(OBJS) $(USER_OBJS)
	@echo 'Building target: $@'
	@echo 'Invoking: MacOS X C++ Linker'
	g++ -L/opt/local/lib -framework python -pg -o "RunTests" $(OBJS) $(USER_OBJS) $(LIBS)
	@echo 'Finished building target: $@'
	@echo ' '

# Other Targets
clean:
	-$(RM) $(C++_DEPS)$(OBJS)$(C_DEPS)$(CC_DEPS)$(CPP_DEPS)$(EXECUTABLES)$(CXX_DEPS)$(C_UPPER_DEPS) RunTests
	-@echo ' '

.PHONY: all clean dependents
.SECONDARY:

-include ../makefile.targets
