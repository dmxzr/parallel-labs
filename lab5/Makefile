MPICXX = mpicxx
MPIEXEC = mpirun
MPI_FLAGS =
MPI_CXXFLAGS = -std=c++17 -O2 -Wall
CC = clang
OMP_PREFIX = /opt/homebrew/opt/libomp
OMPFLAGS = -Xpreprocessor -fopenmp -I$(OMP_PREFIX)/include
OMPLIBS = -L$(OMP_PREFIX)/lib -lomp
LAB1_REF = origin/lab1
BUILD ?= $(shell python3 -B -c 'from benchmark import default_build_dir; print(default_build_dir())')
BUILD := $(abspath $(BUILD))
export LAB5_BUILD_DIR := $(BUILD)

all: $(BUILD)/mpi_lab5 $(BUILD)/omp_lab1

$(BUILD):
	mkdir -m 700 -p "$@"

$(BUILD)/lab5_original: lab5.cpp | $(BUILD)
	$(MPICXX) $(MPI_CXXFLAGS) $< -o "$@"

$(BUILD)/mpi_lab5: mpi_lab5.cpp | $(BUILD)
	$(MPICXX) $(MPI_CXXFLAGS) $< -o "$@"

$(BUILD)/omp_lab1: | $(BUILD)
	git show "$(LAB1_REF):lab1/new.c" > "$(BUILD)/lab1.c"
	$(CC) -O2 -Wall $(OMPFLAGS) "$(BUILD)/lab1.c" $(OMPLIBS) -o "$@"

check-original: $(BUILD)/lab5_original
	"$(BUILD)/lab5_original"
	$(MPIEXEC) $(MPI_FLAGS) -n 3 "$(BUILD)/lab5_original"

check: check-original $(BUILD)/mpi_lab5
	"$(BUILD)/mpi_lab5"
	$(MPIEXEC) $(MPI_FLAGS) -n 3 "$(BUILD)/mpi_lab5"

omp: $(BUILD)/omp_lab1
	python3 benchmark.py omp
	python3 plot.py

mpi: $(BUILD)/mpi_lab5
	python3 benchmark.py mpi --launcher "$(MPIEXEC) $(MPI_FLAGS)"
	python3 plot.py

run: all
	python3 benchmark.py omp
	python3 benchmark.py mpi --launcher "$(MPIEXEC) $(MPI_FLAGS)"
	python3 plot.py

plot:
	python3 plot.py

report:
	typst compile report.typ report.pdf

.PHONY: all check-original check omp mpi run plot report
