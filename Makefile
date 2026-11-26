CXX      := g++
CXXFLAGS := -std=c++17 -O2 -Wall -Wextra -Isrc/cpp/include
TARGET   := aed1_runner
SRCS     := $(wildcard src/cpp/src/*.cpp)
OBJS     := $(SRCS:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

run: $(TARGET)
	./$(TARGET) all data/processed results/csv

clean:
	rm -f $(OBJS) $(TARGET) $(TARGET).exe

.PHONY: all run clean