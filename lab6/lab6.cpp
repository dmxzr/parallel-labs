#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <mpi.h>

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

void prepare_data(std::vector<double>& A, std::vector<double>& b, std::vector<double>& x_ref, int N, unsigned seed)
{
    srand(seed);
    A.resize(N * N);
    b.resize(N);
    x_ref.resize(N);
    generate_matrix(A, N);
    generate_rhs(A, b, x_ref, N);
}

void scatter_data(std::vector<double>& A, std::vector<double>& b, std::vector<double>& local_A, std::vector<double>& local_b, int N, int rows_per_proc)
{
    local_A.resize(rows_per_proc * N);
    local_b.resize(rows_per_proc);

    MPI_Scatter(A.data(), rows_per_proc * N, MPI_DOUBLE, local_A.data(), rows_per_proc * N, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Scatter(b.data(), rows_per_proc, MPI_DOUBLE, local_b.data(), rows_per_proc, MPI_DOUBLE, 0, MPI_COMM_WORLD);
}

void gather_data(std::vector<double>& local_A, std::vector<double>& local_b, std::vector<double>& A, std::vector<double>& b, int N, int rank, int rows_per_proc)
{
    if (rank == 0) { A.resize(N * N); b.resize(N); }

    MPI_Gather(local_A.data(), rows_per_proc * N, MPI_DOUBLE, A.data(), rows_per_proc * N, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Gather(local_b.data(), rows_per_proc, MPI_DOUBLE, b.data(), rows_per_proc, MPI_DOUBLE, 0, MPI_COMM_WORLD);
}

void forward_elimination_mpi(std::vector<double>& local_A, std::vector<double>& local_b, int N, int rank, int rows_per_proc)
{
    std::vector<double> pivot_row(N);

    for (int k = 0; k < N; k++)
    {
        int owner = k / rows_per_proc;
        int local_k = k % rows_per_proc;

        if (rank == owner)
        {
            for (int j = 0; j < N; j++) { pivot_row[j] = local_A[local_k * N + j]; }
        }

        MPI_Bcast(pivot_row.data(), N, MPI_DOUBLE, owner, MPI_COMM_WORLD);

        double pivot_b = 0.0;
        if (rank == owner) { pivot_b = local_b[local_k]; }
        MPI_Bcast(&pivot_b, 1, MPI_DOUBLE, owner, MPI_COMM_WORLD);

        for (int i = 0; i < rows_per_proc; i++)
        {
            int global_i = rank * rows_per_proc + i;
            if (global_i > k)
            {
                double factor = local_A[i * N + k] / pivot_row[k];
                for (int j = k; j < N; j++)
                {
                    local_A[i * N + j] -= factor * pivot_row[j];
                }
                local_b[i] -= factor * pivot_b;
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

double solve_forward_timed(std::vector<double>& local_A, std::vector<double>& local_b, int N, int rank, int rows_per_proc)
{
    MPI_Barrier(MPI_COMM_WORLD);
    double t0 = MPI_Wtime();

    forward_elimination_mpi(local_A, local_b, N, rank, rows_per_proc);

    MPI_Barrier(MPI_COMM_WORLD);
    return MPI_Wtime() - t0;
}

void report_result(const std::vector<double>& x, const std::vector<double>& x_ref, int N, int size, double t_forward, double t_back)
{
    double max_err = 0.0;
    bool ok = check_solution(x, x_ref, N, max_err);

    printf("  N = %d; processes = %d;\n", N, size);
    printf("  forward time = %.4f s;\n", t_forward);
    printf("  back    time = %.4f s;\n", t_back);
    printf("  total   time = %.4f s;\n", t_forward + t_back);
    printf("  max error = %e;\n", max_err);
    printf("  result: %s.\n", ok ? "OK" : "FAILED");
}

int main(int argc, char** argv)
{
    MPI_Init(&argc, &argv);

    int rank = 0;
    int size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    // Параметры
    int N = 3000;
    if (argc > 1) { N = atoi(argv[1]); }
    if (N < 1) { N = 1; }

    const unsigned seed = 920215;

    // Требование: N должно делиться нацело на число процессов
    if (N % size != 0)
    {
        if (rank == 0) { printf("Error: N (%d) must be divisible by processes (%d).\n", N, size); }
        MPI_Finalize();
        return 1;
    }

    int rows_per_proc = N / size;

    std::vector<double> A, b, x_ref;              // Полные данные (только на мастере)
    std::vector<double> local_A, local_b;         // Локальные куски строк

    // 1. Мастер готовит данные
    if (rank == 0) { prepare_data(A, b, x_ref, N, seed); }

    // 2. Раздача строк по процессам
    scatter_data(A, b, local_A, local_b, N, rows_per_proc);

    // 3. Прямой ход (параллельный) с замером времени
    double t_forward = solve_forward_timed(local_A, local_b, N, rank, rows_per_proc);

    // 4. Сбор результата обратно на мастер
    gather_data(local_A, local_b, A, b, N, rank, rows_per_proc);

    // 5. Обратный ход и проверка (последовательно, только мастер)
    if (rank == 0)
    {
        std::vector<double> x(N);

        double t1 = MPI_Wtime();
        back_substitution(A, b, x, N);
        double t_back = MPI_Wtime() - t1;

        report_result(x, x_ref, N, size, t_forward, t_back);
    }

    MPI_Finalize();
    return 0;
}