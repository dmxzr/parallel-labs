#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <omp.h>

int main(int argc, char **argv)
{
    const int default_count = 10000000;
    const int random_seed = 920214;
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

    srand(random_seed);
    for (int i = 0; i < count; ++i)
        array[i] = rand();
    array[count / 2] = target;

    omp_set_dynamic(0);
    omp_set_num_threads(threads);

    FILE *samples_file = NULL;
    if (samples_path != NULL)
    {
        samples_file = fopen(samples_path, "a");
        if (samples_file == NULL)
        {
            perror("fopen");
            free(array);
            return 1;
        }
    }

    int index = INT_MAX;
    for (int warmup = 0; warmup < 3; ++warmup)
    {
        index = INT_MAX;
#pragma omp parallel for reduction(min : index)
        for (int i = 0; i < count; ++i)
        {
            if (array[i] == target && i < index)
                index = i;
        }
    }

    double total_time = 0.0;
    double min_time = 1.0e100;
    for (int repeat = 0; repeat < repeats; ++repeat)
    {
        index = INT_MAX;
        double start = omp_get_wtime();

#pragma omp parallel for reduction(min : index)
        for (int i = 0; i < count; ++i)
        {
            if (array[i] == target && i < index)
                index = i;
        }

        double elapsed = omp_get_wtime() - start;
        total_time += elapsed;
        if (elapsed < min_time)
            min_time = elapsed;

        if (samples_file != NULL &&
            fprintf(samples_file, "%d,%d,%.10f\n", threads,
                    repeat_offset + repeat + 1, elapsed) < 0)
        {
            perror("fprintf");
            fclose(samples_file);
            free(array);
            return 1;
        }
    }

    if (samples_file != NULL && fclose(samples_file) != 0)
    {
        perror("fclose");
        free(array);
        return 1;
    }

    printf("threads=%d count=%d target=%d index=%d repeats=%d time=%.8f min=%.8f\n",
           threads, count, target, index == INT_MAX ? -1 : index, repeats,
           total_time / repeats, min_time);

    free(array);
    return 0;
}
