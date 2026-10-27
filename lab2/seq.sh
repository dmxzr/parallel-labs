#!/bin/bash
REPEATS=100
export OMP_NUM_THREADS=1

N_LIST="1000000 5000000 10000000 50000000"

echo "n,avg_time_s" > time_vs_n.csv
for n in $N_LIST; do
    times=""
    for i in $(seq 1 $REPEATS); do
        t=$(./lab2 1 "$n" 16 | sed -n 's/.*time=\([0-9.]*\).*/\1/p')
        times="$times $t"
    done
    avg=$(echo "$times" | awk '{s=0; for(i=1;i<=NF;i++) s+=$i; printf "%.6f", s/NF}')
    echo "$n,$avg" >> time_vs_n.csv
    echo "n=$n avg_time=$avg"
done
