#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <algorithm>
#include <vector>
#include <chrono>
#include <omp.h>

void generate_matrix(std::vector<double>& A, int N)
{
    for (int i = 0; i < N; i++)
    {
        double off_sum = 0.0;
        for (int j = 0; j < N; j++)
        {
            if (i != j)
            {
                double v = (double)(rand() % 100) / 10.0;
                A[i * N + j] = v;
                off_sum += fabs(v);
            }
        }
        A[i * N + i] = off_sum + 1.0 + (double)(rand() % 100) / 10.0;
    }
}

void generate_rhs(const std::vector<double>& A, std::vector<double>& b, std::vector<double>& x_ref, int N)
{
    for (int i = 0; i < N; i++) { x_ref[i] = (double)(rand() % 100) / 10.0; }

    for (int i = 0; i < N; i++)
    {
        double s = 0.0;
        for (int j = 0; j < N; j++) { s += A[i * N + j] * x_ref[j]; }
        b[i] = s;
    }
}

constexpr int block_size = 64;

void factorize_panel(std::vector<double>& A, std::vector<double>& b, int N, int first, int end)
{
    for (int k = first; k < end; k++)
    {
        const double pivot = A[k * N + k];
        for (int i = k + 1; i < end; i++)
        {
            const double factor = A[i * N + k] / pivot;
            for (int j = k; j < N; j++)
            {
                A[i * N + j] -= factor * A[k * N + j];
            }
            b[i] -= factor * b[k];
        }
    }
}

void update_row(std::vector<double>& A, std::vector<double>& b, int N, int row, int first, int end)
{
    for (int k = first; k < end; k++)
    {
        const double factor = A[row * N + k] / A[k * N + k];
        for (int j = k; j < N; j++)
        {
            A[row * N + j] -= factor * A[k * N + j];
        }
        b[row] -= factor * b[k];
    }
}

void forward_elimination(std::vector<double>& A, std::vector<double>& b, int N)
{
    for (int first = 0; first < N; first += block_size)
    {
        const int end = std::min(first + block_size, N);
        factorize_panel(A, b, N, first, end);
        for (int i = end; i < N; i++)
        {
            update_row(A, b, N, i, first, end);
        }
    }
}

void forward_elimination_parallel(std::vector<double>& A, std::vector<double>& b, int N)
{
#pragma omp parallel
    {
        for (int first = 0; first < N; first += block_size)
        {
            const int end = std::min(first + block_size, N);

#pragma omp single
            factorize_panel(A, b, N, first, end);

#pragma omp for schedule(static)
            for (int i = end; i < N; i++)
            {
                update_row(A, b, N, i, first, end);
            }
        }
    }
}

void back_substitution(const std::vector<double>& A, const std::vector<double>& b, std::vector<double>& x, int N)
{
    for (int i = N - 1; i >= 0; i--)
    {
        double s = b[i];
        for (int j = i + 1; j < N; j++) { s -= A[i * N + j] * x[j]; }
        x[i] = s / A[i * N + i];
    }
}

bool check_solution(const std::vector<double>& x, const std::vector<double>& x_ref, int N, double& max_err)
{
    const double tolerance = 1e-6;

    max_err = 0.0;
    for (int i = 0; i < N; i++)
    {
        double err = fabs(x[i] - x_ref[i]);
        if (err > max_err) { max_err = err; }
    }

    return (max_err < tolerance);
}

void solve_and_time(std::vector<double>& A, std::vector<double>& b, std::vector<double>& x, int N, bool parallel, double& t_forward, double& t_back)
{
    auto t0 = std::chrono::high_resolution_clock::now();

    if (parallel) { forward_elimination_parallel(A, b, N); }
    else          { forward_elimination(A, b, N);          }

    auto t1 = std::chrono::high_resolution_clock::now();

    back_substitution(A, b, x, N);

    auto t2 = std::chrono::high_resolution_clock::now();

    t_forward = std::chrono::duration<double>(t1 - t0).count();
    t_back    = std::chrono::duration<double>(t2 - t1).count();
}

bool report_result(const std::vector<double>& x, const std::vector<double>& x_ref, int N, int threads, double t_forward, double t_back)
{
    double max_err = 0.0;
    bool ok = check_solution(x, x_ref, N, max_err);

    printf("  N = %d; threads = %d;\n", N, threads);
    printf("  forward time = %.9f s;\n", t_forward);
    printf("  back    time = %.9f s;\n", t_back);
    printf("  total   time = %.9f s;\n", t_forward + t_back);
    printf("  max error = %e;\n", max_err);
    printf("  result: %s.\n", ok ? "OK" : "FAILED");
    return ok;
}

#ifndef LAB3_BENCHMARK
int main()
{
    constexpr int N = 3000;
    const int threads = omp_get_max_threads();
    omp_set_dynamic(0);
    omp_set_num_threads(threads);

    const unsigned seed = 920215;
    srand(seed);

    std::vector<double> A(static_cast<std::size_t>(N) * N);
    std::vector<double> b(N);
    std::vector<double> x(N);
    std::vector<double> x_ref(N);

    generate_matrix(A, N);
    generate_rhs(A, b, x_ref, N);

    double t_forward = 0.0;
    double t_back = 0.0;
    solve_and_time(A, b, x, N, true, t_forward, t_back);

    return report_result(x, x_ref, N, threads, t_forward, t_back) ? 0 : 1;
}
#endif
