#define LAB3_BENCHMARK
#include "lab3.cpp"

#include <algorithm>
#include <cerrno>
#include <climits>
#include <random>

bool parse_positive_int(const char* value, int& result)
{
    char* end = nullptr;
    errno = 0;
    const long parsed = strtol(value, &end, 10);
    if (errno != 0 || end == value || *end != '\0' || parsed <= 0 || parsed > INT_MAX)
    {
        return false;
    }
    result = static_cast<int>(parsed);
    return true;
}

struct Configuration
{
    bool parallel;
    int threads;
};

struct Measurement
{
    double forward;
    double back;
    double max_error;
};

Measurement measure(
    const Configuration& configuration,
    const std::vector<double>& initial_A,
    const std::vector<double>& initial_b,
    const std::vector<double>& x_ref,
    std::vector<double>& A,
    std::vector<double>& b,
    std::vector<double>& x,
    int N)
{
    A = initial_A;
    b = initial_b;
    if (configuration.parallel)
    {
        omp_set_num_threads(configuration.threads);
    }

    auto start = std::chrono::steady_clock::now();
    if (configuration.parallel)
    {
        forward_elimination_parallel(A, b, N);
    }
    else
    {
        forward_elimination(A, b, N);
    }
    auto forward_end = std::chrono::steady_clock::now();

    back_substitution(A, b, x, N);
    auto end = std::chrono::steady_clock::now();

    double max_error = 0.0;
    if (!check_solution(x, x_ref, N, max_error))
    {
        fprintf(stderr, "Ошибка решения: threads=%d, max_error=%e\n", configuration.threads, max_error);
        std::exit(2);
    }

    return {
        std::chrono::duration<double>(forward_end - start).count(),
        std::chrono::duration<double>(end - forward_end).count(),
        max_error
    };
}

int main(int argc, char** argv)
{
    int N = 1000;
    int repeats = 7;
    if (argc > 3
        || (argc >= 2 && !parse_positive_int(argv[1], N))
        || (argc == 3 && !parse_positive_int(argv[2], repeats))
        || N > 46340)
    {
        fprintf(stderr, "Usage: %s [matrix_size (1..46340)] [repeats (positive integer)]\n", argv[0]);
        return 1;
    }

    omp_set_dynamic(0);

    const unsigned seed = 920215;
    srand(seed);

    const std::size_t matrix_size = static_cast<std::size_t>(N) * N;
    std::vector<double> initial_A(matrix_size);
    std::vector<double> initial_b(N);
    std::vector<double> x_ref(N);
    generate_matrix(initial_A, N);
    generate_rhs(initial_A, initial_b, x_ref, N);

    std::vector<double> A(matrix_size);
    std::vector<double> b(N);
    std::vector<double> x(N);

    std::vector<Configuration> configurations;
    configurations.push_back({false, 1});
    for (int threads = 1; threads <= 16; threads++)
    {
        configurations.push_back({true, threads});
    }

    for (const Configuration& configuration : configurations)
    {
        measure(configuration, initial_A, initial_b, x_ref, A, b, x, N);
    }

    printf("Тип,Потоки,Повтор,Прямой_ход_с,Обратный_ход_с,Общее_время_с,Макс_ошибка\n");
    std::mt19937 order_generator(seed);
    for (int repeat = 1; repeat <= repeats; repeat++)
    {
        std::shuffle(configurations.begin(), configurations.end(), order_generator);
        for (const Configuration& configuration : configurations)
        {
            Measurement sample = measure(configuration, initial_A, initial_b, x_ref, A, b, x, N);
            printf(
                "%s,%d,%d,%.12f,%.12f,%.12f,%.12e\n",
                configuration.parallel ? "parallel" : "serial",
                configuration.threads,
                repeat,
                sample.forward,
                sample.back,
                sample.forward + sample.back,
                sample.max_error);
        }
        if (repeat % 10 == 0 || repeat == repeats)
        {
            fprintf(stderr, "Завершено повторов: %d/%d\n", repeat, repeats);
        }
    }

    return 0;
}
