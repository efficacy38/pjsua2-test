# If your application is in a file named myapp.cpp or myapp.c
# this is the line you will need to build the binary.
CC = g++
all: myapp

%.o: %.cpp
	$(CC) -o $@ -ggdb $< `pkg-config --cflags --libs libpjproject`
	chmod +x $@
	
clean:
	rm -f *.o
