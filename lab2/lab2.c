#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <omp.h>

int main(int argc, char **argv)
{
    const int default_count = 10000000;
    const int default_seed = 920214;
    const int default_target = 16;

    int threads = (argc > 1) ? atoi(argv[1]) : 1;
    int count = (argc > 2) ? atoi(argv[2]) : default_count;
    int target = (argc > 3) ? atoi(argv[3]) : default_target;
    int repeats = (argc > 4) ? atoi(argv[4]) : 1;
    const char *samples_path = (argc > 5) ? argv[5] : NULL;
    int repeat_offset = (argc > 6) ? atoi(argv[6]) : 0;

    if (threads <= 0)
        threads = 1;
    if (count <= 0)
        count = default_count;
    if (repeats <= 0)
        repeats = 1;

    int *array = malloc((size_t)count * sizeof(int));
    if (array == NULL)
    {
        perror("malloc");
        return 1;
    }

    srand(default_seed);
    for (int i = 0; i < count; ++i)
    {
        array[i] = rand();
    }
    array[count / 2] = target;

    omp_set_dynamic(0);
    omp_set_num_threads(threads);

    int actual_threads = 0;
#pragma omp parallel
    {
#pragma omp single
        actual_threads = omp_get_num_threads();
    }
    if (actual_threads != threads)
    {
        fprintf(stderr, "Requested %d threads, but OpenMP created %d.\n", threads, actual_threads);
        free(array);
        return 1;
    }

    int index = INT_MAX;
    double total_time = 0.0;
    double min_time = 1.0e100;
    double *sample_times = malloc((size_t)repeats * sizeof(double));
    if (sample_times == NULL)
    {
        perror("malloc");
        free(array);
        return 1;
    }

    for (int warmup = 0; warmup < 3; ++warmup)
    {
        int warmup_index = INT_MAX;
#pragma omp parallel for reduction(min : warmup_index)
        for (int i = 0; i < count; ++i)
        {
            if (array[i] == target && i < warmup_index)
            {
                warmup_index = i;
            }
        }
    }

    for (int repeat = 0; repeat < repeats; ++repeat)
    {
        index = INT_MAX;
        double start = omp_get_wtime();

#pragma omp parallel for reduction(min : index)
        for (int i = 0; i < count; ++i)
        {
            if (array[i] == target && i < index)
            {
                index = i;
            }
        }

        double elapsed = omp_get_wtime() - start;
        sample_times[repeat] = elapsed;
        total_time += elapsed;
        if (elapsed < min_time)
            min_time = elapsed;
    }

    if (samples_path != NULL)
    {
        FILE *samples_file = fopen(samples_path, "a");
        if (samples_file == NULL)
        {
            perror("fopen");
            free(sample_times);
            free(array);
            return 1;
        }
        for (int repeat = 0; repeat < repeats; ++repeat)
        {
            fprintf(samples_file, "%d,%d,%.10f\n", threads, repeat_offset + repeat + 1, sample_times[repeat]);
        }
        if (fclose(samples_file) != 0)
        {
            perror("fclose");
            free(sample_times);
            free(array);
            return 1;
        }
    }

    printf("threads=%d count=%d target=%d index=%d repeats=%d time=%.8f min=%.8f\n",
           threads,
           count,
           target,
           index == INT_MAX ? -1 : index,
           repeats,
           total_time / repeats,
           min_time);

    free(sample_times);
    free(array);
    return 0;
}