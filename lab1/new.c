#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

int main(int argc, char** argv)
{
    int count = 10000000;     ///< Number of array elements
    const int threads = 1;         ///< Number of parallel threads to use
    const int random_seed = 920215; ///< RNG seed

    int do_count = 0; // флаг


    if (argc > 1) count = atoi(argv[1]);
    if (argc > 2) do_count = atoi(argv[2]);


    int* array = 0;                 ///< The array we need to find the max in
    int  max   = -1;                ///< The maximal element

    long long  comparisons = 0; 

    /* Initialize the RNG */
    unsigned int seed = random_seed;

    /* Determine the OpenMP support */
    printf("OpenMP: %d;\n======\n", _OPENMP);

    /* Generate the random array */
    array = (int*)malloc(count*sizeof(int));
    for(int i=0; i<count; i++) { array[i] = rand_r(&seed); }

    double t1 = omp_get_wtime();

    /* Find the maximal element */
    #pragma omp parallel shared(array, count, do_count) reduction(max: max) reduction(+: comparisons) default(none)
    {
        #pragma omp for
        for(int i=0; i<count; i++)
        {

            if(do_count) {
                #pragma omp atomic 
                comparisons++;
            }

            if(array[i] > max) { max = array[i]; };
        }
        //printf("-- My lmax is: %d;\n", max);
    }

    double t2 = omp_get_wtime();

    printf("N=%d; threads=%d; Max=%d; Time=%.6f; Comparisons=%lld\n", 
        count, omp_get_max_threads(), max, t2 - t1, comparisons);
    

    free(array);
    //printf("======\nMax is: %d;\n", max);
    return(0);
}