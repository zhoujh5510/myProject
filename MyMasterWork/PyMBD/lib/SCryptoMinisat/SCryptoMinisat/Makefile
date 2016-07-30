CC=g++
CRYPTOMINISATBASE=../cryptominisat-2.5.1
OUTPUT=SCryptoMinisat

all: clean cryptominisat
	$(CC) -O3 -o $(OUTPUT) Main.C $(CRYPTOMINISATBASE)/Solver/*.cpp \
	-I $(CRYPTOMINISATBASE)/Solver \
	-I $(CRYPTOMINISATBASE)/mtl \
	-I $(CRYPTOMINISATBASE)/MTRand

cryptominisat:
	(cd $(CRYPTOMINISATBASE); ./configure)

clean:
	rm -f $(OUTPUT)
