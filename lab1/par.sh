#!/bin/bash
REPEATS=100
N=10000000
PROCS_LIST="1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16"

export OMP_PLACES=threads
export OMP_PROC_BIND=TRUE

# Прогрев
for i in 1 2 3; do OMP_NUM_THREADS=4 ./new $N 0 > /dev/null; done

echo "p,mean,min" > time_vs_p.csv
for p in $PROCS_LIST; do
    times=""
    for i in $(seq 1 $REPEATS); do
        t=$(OMP_NUM_THREADS=$p ./new $N 0 | sed -n 's/.*Time=\([0-9.]*\).*/\1/p')
        times="$times $t"
    done
    stats=$(echo $times | awk '{
        s=0; min=1e9
        for(i=1;i<=NF;i++){ s+=$i; if($i<min) min=$i }
        printf "%.6f,%.6f", s/NF, min
    }')
    echo "$p,$stats" >> time_vs_p.csv
    echo "p=$p  $stats"
done

# Ускорение и эффективность по минимуму
echo "p,time,speedup,efficiency" > speedup.csv
t1=$(awk -F, '$1==1 {print $3}' time_vs_p.csv)
tail -n +2 time_vs_p.csv | while IFS=, read p mean min; do
    s=$(awk -v t1=$t1 -v t=$min 'BEGIN{printf "%.4f", t1/t}')
    e=$(awk -v s=$s -v p=$p 'BEGIN{printf "%.4f", s/p}')
    echo "$p,$min,$s,$e" >> speedup.csv
done

echo ""
echo "=== speedup.csv (по минимуму) ==="
cat speedup.csv