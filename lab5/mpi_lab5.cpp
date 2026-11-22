#include <mpi.h>

#include <cerrno>
#include <climits>
#include <cstdio>
#include <cstdlib>
#include <vector>

static const unsigned int random_seed = 920215;
static const int warmups = 3;

static bool read_positive(const char* text, int& value) {
    char* end = nullptr;
    errno = 0;
    const long number = strtol(text, &end, 10);
    if (errno || end == text || *end || number < 1 || number > INT_MAX)
        return false;
    value = (int)number;
    return true;
}

static int find_max(const std::vector<int>& array, int count) {
    int maximum = INT_MIN;
    for (int i = 0; i < count; ++i) {
        if (array[i] > maximum) maximum = array[i];
    }
    return maximum;
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank = -1;
    int size = -1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int count = 10;
    int repeats = 1;
    const bool benchmark = argc == 3;
    if (argc > 3 || (argc > 1 && !read_positive(argv[1], count))
                 || (benchmark && !read_positive(argv[2], repeats))) {
        if (rank == 0) fprintf(stderr, "Usage: %s [N [repeats]]\n", argv[0]);
        MPI_Finalize();
        return 1;
    }

    const auto block_start = [count, size](int process) {
        return static_cast<int>(1LL * process * count / size);
    };
    const int start = block_start(rank);
    const int end = block_start(rank + 1);
    const int local_count = end - start;

    std::vector<int> array(rank == 0 ? count : 0);
    std::vector<int> local_array(rank == 0 ? 0 : local_count);
    std::vector<int> send_counts(rank == 0 ? size : 0);
    std::vector<int> offsets(rank == 0 ? size : 0);
    int expected = INT_MIN;
    if (rank == 0) {
        for (int process = 0; process < size; ++process) {
            offsets[process] = block_start(process);
            send_counts[process] = block_start(process + 1) - offsets[process];
        }
        unsigned int seed = random_seed;
        for (int& value : array) value = rand_r(&seed);
        expected = find_max(array, count);
        if (benchmark) printf("p,N,repeat,max,time_s\n");
    }

    const auto& search_array = rank == 0 ? array : local_array;
    void* receive_buffer = rank == 0 ? MPI_IN_PLACE : local_array.data();

    for (int r = benchmark ? -warmups : 0; r < repeats; ++r) {
        MPI_Scatterv(array.data(), send_counts.data(), offsets.data(), MPI_INT,
                     receive_buffer, local_count, MPI_INT, 0, MPI_COMM_WORLD);
        MPI_Barrier(MPI_COMM_WORLD);
        const double t_start = MPI_Wtime();

        const int local_max = find_max(search_array, local_count);
        int maximum = INT_MIN;
        MPI_Reduce(&local_max, &maximum, 1, MPI_INT, MPI_MAX, 0, MPI_COMM_WORLD);
        const double elapsed = MPI_Wtime() - t_start;

        if (rank == 0 && maximum != expected) {
            fprintf(stderr, "Incorrect maximum: expected %d, got %d\n", expected, maximum);
            MPI_Abort(MPI_COMM_WORLD, 2);
        }

        if (!benchmark) {
            printf("Rank %d: [%d, %d), local max = %d\n", rank, start, end, local_max);
            if (rank == 0)
                printf("N=%d; processes=%d; Max=%d; Serial max=%d\n", count, size, maximum, expected);
        } else if (r >= 0) {
            double time;
            MPI_Reduce(&elapsed, &time, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
            if (rank == 0)
                printf("%d,%d,%d,%d,%.9f\n", size, count, r + 1, maximum, time);
        }
    }

    MPI_Finalize();
    return 0;
}
