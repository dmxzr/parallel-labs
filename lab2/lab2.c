#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <omp.h>

int main(void)
{
    const int count = 10000000;
    const int random_seed = 920214;
    const int target = 16;

    int *array = malloc((size_t)count * sizeof(int));
    if (array == NULL)
    {

        return 1;
    }

    srand(random_seed);
    for (int i = 0; i < count; ++i)
    {
        array[i] = rand();
    }

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

    double end_time = omp_get_wtime() - start;

    if (index == INT_MAX)
    {
        printf("Value %d not found\n", target);
    }
    else
    {
        printf("Found value %d at index %d\n", target, index);
    }

    printf("Time: %.6f s\n", end_time);

    free(array);
    return 0;
}