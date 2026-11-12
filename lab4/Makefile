CXX = clang++
CXXFLAGS = -std=c++17 -O2 -Xclang -fopenmp -I/opt/homebrew/opt/libomp/include
LDFLAGS = -L/opt/homebrew/opt/libomp/lib -lomp
TARGET = omp_lab4

all: $(TARGET)

$(TARGET): omp_lab4.cpp
	$(CXX) $(CXXFLAGS) $< $(LDFLAGS) -o $@

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET)

.PHONY: all run clean
