CFLAGS = -O

OBJS = trans.o

PROGRAM = trans

$(PROGRAM): $(OBJS)
	cc $(CFLAGS) $(OBJS) -o $(PROGRAM)

trans.o: /usr/include/stdio.h /usr/include/strings.h

clean:
	/bin/rm -f $(OBJS) $(PROGRAM)
