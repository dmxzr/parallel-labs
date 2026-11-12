CXX = clang++
CXXFLAGS = -std=c++17 -O2 -Xclang -fopenmp -I/opt/homebrew/opt/libomp/include
LDFLAGS = -L/opt/homebrew/opt/libomp/lib -lomp
TARGET = dyn_chunk_bench
LAB = omp_lab4
CSV = dyn_chunk_results.csv
PNG = dyn_chunk_results.png

all: $(TARGET) $(LAB)

$(TARGET): dyn_chunk_bench.cpp
	$(CXX) $(CXXFLAGS) $< $(LDFLAGS) -o $@

# Основная программа лабораторной (задания 1-8), тоже пишет CSV
$(LAB): omp_lab4.cpp
	$(CXX) $(CXXFLAGS) $< $(LDFLAGS) -o $@

# Бенчмарк + CSV-таблица + график одной командой
run: $(TARGET)
	./$(TARGET) $(CSV) $(PNG)

# Перестроить график без повторного запуска бенчмарка
plot:
	python3 plot_chunk_results.py $(CSV) -o $(PNG)

clean:
	rm -f $(TARGET) $(LAB) $(CSV) $(PNG) results.csv

.PHONY: all run plot clean
