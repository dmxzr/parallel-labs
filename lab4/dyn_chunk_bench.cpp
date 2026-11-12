// dyn_chunk_bench: определение целесообразного размера chunk для schedule(dynamic).
// Потоков — максимум (omp_get_max_threads()), ядро то же, что в omp_lab4.cpp.
// Sweep: chunk = 1..N/threads (степени двойки) + static как ориентир.
//
// Автоматизация: программа пишет результаты в CSV-таблицу и сама строит график,
// вызывая plot_chunk_results.py (python3) после завершения замеров:
//   ./dyn_chunk_bench [results.csv [results.png]]
// или одной командой: make run
//
// Замеры: REPS повторов на конфигурацию, в CSV пишутся min и median (мс).

#include <omp.h>

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

static const long long N = 2'000'000;
static const int REPS = 10;

static long long kernel(const std::vector<long long>& data, long long i) {
    long long v = data[i];
    for (int j = 0; j < 64; ++j)
        v = (v * 1103515245 + 12345) % 2147483647;
    return v * (i % 17 + 1);
}

// Возвращает время одного прогона в мс; sum — контрольная сумма.
// Планировщик выбирается через omp_set_schedule() + schedule(runtime):
// это работает одинаково на clang/libomp и gcc/libgomp.
static double run_once(const std::vector<long long>& data, omp_sched_t kind,
                       long long chunk, long long& sum) {
    long long result = 0;
    omp_set_schedule(kind, (int)chunk);
    auto start = std::chrono::steady_clock::now();
#pragma omp parallel for schedule(runtime) reduction(+ : result)
    for (long long i = 0; i < N; ++i) result += kernel(data, i);
    auto finish = std::chrono::steady_clock::now();
    sum = result;
    return std::chrono::duration_cast<std::chrono::microseconds>(finish - start).count() / 1000.0;
}

int main(int argc, char** argv) {
    const std::string csv_path = (argc > 1) ? argv[1] : "dyn_chunk_results.csv";
    const std::string png_path = (argc > 2) ? argv[2] : "dyn_chunk_results.png";

    std::vector<long long> data(N);
    unsigned long long seed = 42;
    for (long long i = 0; i < N; ++i) {
        seed = seed * 6364136223846793005ULL + 1442695040888963407ULL;
        data[i] = (long long)((seed >> 33) % 1000) + 1;
    }

    const int threads = omp_get_max_threads();
    printf("threads = %d, N = %lld, reps = %d\n", threads, N, REPS);

    std::vector<long long> chunks = {1, 2, 4, 8, 16, 32, 64, 128, 256, 512,
                                     1024, 2048, 4096, 8192, 16384, 32768,
                                     65536, 131072, 262144};
    chunks.push_back(N / threads);  // весь цикл одним блоком на поток

    struct Row { std::string kind; long long chunk; double mn, med; long long sum; };
    std::vector<Row> rows;

    for (omp_sched_t kind : {omp_sched_static, omp_sched_dynamic}) {
        const std::string name = (kind == omp_sched_static) ? "static" : "dynamic";
        for (long long chunk : chunks) {
            std::vector<double> times;
            long long sum = 0;
            for (int r = 0; r < REPS; ++r)
                times.push_back(run_once(data, kind, chunk, sum));
            std::sort(times.begin(), times.end());
            rows.push_back({name, chunk, times.front(), times[times.size() / 2], sum});
        }
    }

    // ── 1. Таблица в консоль ──
    printf("\n%-8s | %8s | %9s | %9s | %s\n", "kind", "chunk", "min, ms", "med, ms", "sum");
    printf("---------+----------+-----------+-----------+-------------------\n");
    for (const Row& r : rows)
        printf("%-8s | %8lld | %9.3f | %9.3f | %lld\n",
               r.kind.c_str(), r.chunk, r.mn, r.med, r.sum);

    // ── 2. CSV-таблица на диск ──
    FILE* f = fopen(csv_path.c_str(), "w");
    if (!f) {
        printf("\nWarning: cannot open %s for writing, CSV not saved.\n", csv_path.c_str());
        return 1;
    }
    fprintf(f, "# threads = %d, N = %lld, reps = %d\n", threads, N, REPS);
    fprintf(f, "kind,chunk,min_ms,median_ms,sum\n");
    for (const Row& r : rows)
        fprintf(f, "%s,%lld,%.3f,%.3f,%lld\n", r.kind.c_str(), r.chunk, r.mn, r.med, r.sum);
    fclose(f);
    printf("\nCSV table written to %s\n", csv_path.c_str());

    // ── 3. Автоматическое построение графика ──
    std::string cmd = "python3 plot_chunk_results.py " + csv_path + " -o " + png_path;
    int rc = std::system(cmd.c_str());
    if (rc == 0) {
        printf("Chart written to %s\n", png_path.c_str());
    } else {
        printf("Chart was NOT built (need python3 + matplotlib).\n"
               "Run manually:  %s\n", cmd.c_str());
    }
    return 0;
}
