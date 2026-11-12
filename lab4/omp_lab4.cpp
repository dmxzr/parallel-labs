#include <omp.h>

#include <array>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <random>
#include <string>
#include <vector>

std::string openmp_version_string(int value) {
    switch (value) {
        case 202011: return "OpenMP 5.1 (accepted 2020-11)";
        case 201811: return "OpenMP 5.0 (accepted 2018-11)";
        case 201511: return "OpenMP 4.5 (accepted 2015-11)";
        case 201307: return "OpenMP 4.1 (accepted 2013-07)";
        case 201107: return "OpenMP 4.0 (accepted 2011-07)";
        case 200805: return "OpenMP 3.0 (accepted 2008-05)";
        case 200505: return "OpenMP 2.5 (accepted 2005-05)";
        case 200011: return "OpenMP 2.0 (accepted 2000-11)";
        default: return "Unknown OpenMP standard";
    }
}

std::string schedule_to_string(omp_sched_t kind) {
    switch (kind) {
        case omp_sched_static: return "static";
        case omp_sched_dynamic: return "dynamic";
        case omp_sched_guided: return "guided";
        case omp_sched_auto: return "auto";
        default: return "unknown";
    }
}

void print_task_1_to_6() {
    std::cout << "============================================================\n";
    std::cout << "Task 1: OpenMP standard version and adoption date\n";
    std::cout << "_OPENMP macro: " << _OPENMP << "\n";
    std::cout << "OpenMP version: " << openmp_version_string(_OPENMP) << "\n\n";

    std::cout << "Task 2: Number of processors and available threads\n";
    std::cout << "Number of available processors: " << omp_get_num_procs() << "\n";
    std::cout << "Maximum number of threads: " << omp_get_max_threads() << "\n\n";

    std::cout << "Task 3: dynamic option\n";
    omp_set_dynamic(1);
    std::cout << "omp_get_dynamic(): " << (omp_get_dynamic() ? "enabled" : "disabled") << "\n";
    std::cout << "Dynamic adjustment allows the runtime to vary the number of threads.\n\n";

    std::cout << "Task 4: Timer resolution\n";
    std::cout << "omp_get_wtick() = " << std::setprecision(10) << omp_get_wtick() << " seconds\n\n";

    std::cout << "Task 5: Nested parallel regions and active level configuration\n";
    std::cout << "omp_get_nested() = " << (omp_get_nested() ? "enabled" : "disabled") << "\n";
    std::cout << "omp_get_max_active_levels() = " << omp_get_max_active_levels() << "\n\n";

    std::cout << "Task 6: Current schedule settings\n";
    omp_sched_t kind;
    int modifier = 0;
    omp_get_schedule(&kind, &modifier);
    std::cout << "Current schedule kind: " << schedule_to_string(kind) << "\n";
    std::cout << "Current schedule chunk size: " << modifier << "\n\n";
}

void print_task_7() {
    std::cout << "============================================================\n";
    std::cout << "Task 7: Example with explicit locks\n";
    long long total = 0;
    omp_lock_t lock;
    omp_init_lock(&lock);

#pragma omp parallel
    {
        long long private_sum = 0;
        int thread_id = omp_get_thread_num();
        for (int i = 0; i < 100000; ++i) {
            private_sum += i + thread_id + 1;
        }

        omp_set_lock(&lock);
        total += private_sum;
        omp_unset_lock(&lock);
    }

    omp_destroy_lock(&lock);
    std::cout << "Shared total after lock-protected update: " << total << "\n";
    std::cout << "A lock is required here because several threads modify a shared resource.\n";
    std::cout << "Without a lock, the result is nondeterministic and may be corrupted.\n\n";
}

long long benchmark_schedule(const std::string& schedule_name, int chunk_size) {
    const long long n = 2'000'000;
    std::vector<long long> data(n);
    std::mt19937 gen(42);
    for (long long i = 0; i < n; ++i) {
        data[i] = static_cast<long long>((gen() % 1000) + 1);
    }

    long long result = 0;
    auto start = std::chrono::steady_clock::now();

    if (schedule_name == "static") {
#pragma omp parallel for schedule(static, chunk_size) reduction(+:result)
        for (long long i = 0; i < n; ++i) {
            long long value = data[i];
            for (int j = 0; j < 64; ++j) {
                value = (value * 1103515245 + 12345) % 2147483647;
            }
            result += value * (i % 17 + 1);
        }
    } else if (schedule_name == "dynamic") {
#pragma omp parallel for schedule(dynamic, chunk_size) reduction(+:result)
        for (long long i = 0; i < n; ++i) {
            long long value = data[i];
            for (int j = 0; j < 64; ++j) {
                value = (value * 1103515245 + 12345) % 2147483647;
            }
            result += value * (i % 17 + 1);
        }
    } else if (schedule_name == "guided") {
#pragma omp parallel for schedule(guided, chunk_size) reduction(+:result)
        for (long long i = 0; i < n; ++i) {
            long long value = data[i];
            for (int j = 0; j < 64; ++j) {
                value = (value * 1103515245 + 12345) % 2147483647;
            }
            result += value * (i % 17 + 1);
        }
    }

    auto finish = std::chrono::steady_clock::now();
    auto elapsed_ms = std::chrono::duration_cast<std::chrono::microseconds>(finish - start).count() / 1000.0;
    std::cout << std::left << std::setw(12) << schedule_name
              << " | chunk " << std::setw(3) << chunk_size
              << " | time = " << std::setw(10) << std::fixed << std::setprecision(3) << elapsed_ms << " ms"
              << " | sum = " << result << "\n";
    return result;
}

void print_task_8() {
    std::cout << "============================================================\n";
    std::cout << "Task 8: Comparison of different OpenMP schedules\n";
    std::cout << "Loop size: 2,000,000 iterations, additional work in each iteration\n\n";
    std::cout << std::left << std::setw(12) << "Schedule"
              << " | " << std::setw(8) << "chunk"
              << " | " << std::setw(16) << "time"
              << " | " << "result\n";
    std::cout << "------------------------------------------------------------\n";

    for (const auto& schedule_name : {"static", "dynamic", "guided"}) {
        for (int chunk : {1, 8, 64}) {
            benchmark_schedule(schedule_name, chunk);
        }
    }

    std::cout << "\nInterpretation:\n";
    std::cout << "- static: good for regular, balanced workloads; chunk size controls the block partitioning.\n";
    std::cout << "- dynamic: useful when iterations have different complexity; tasks are assigned on demand.\n";
    std::cout << "- guided: dynamically reduces the chunk size as execution proceeds, which is convenient for\n";
    std::cout << "  irregular workloads, but may add scheduling overhead.\n";
    std::cout << "- In a balanced synthetic example the difference may be small; in uneven workloads it becomes visible.\n\n";
}

int main() {
    print_task_1_to_6();
    print_task_7();
    print_task_8();

    std::cout << "============================================================\n";
    std::cout << "Conclusion\n";
    std::cout << "OpenMP provides flexible control over thread counts, schedules, timers and synchronization.\n";
    std::cout << "The correct choice of schedule depends on the type of workload and its regularity.\n";
    return 0;
}
