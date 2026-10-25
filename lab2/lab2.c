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

    if (threads <= 0)
    {
        threads = 1;
    }
    if (count <= 0)
    {
        count = default_count;
    }

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

    omp_set_dynamic(0);
    omp_set_num_threads(threads);

    int index = INT_MAX;
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

    printf("threads=%d count=%d target=%d index=%d time=%.6f\n",
           threads, count, target,
           index == INT_MAX ? -1 : index,
           elapsed);

    free(array);
    return 0;
}