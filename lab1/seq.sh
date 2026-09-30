#!/bin/bash
REPEATS=1000
export OMP_NUM_THREADS=1

N_LIST="1000000 5000000 10000000 50000000 100000000"

echo "N,time" > time_vs_n.csv
for n in $N_LIST; do
    times=""
    for i in $(seq 1 $REPEATS); do
        t=$(./old $n 0 | sed -n 's/.*Time=\([0-9.]*\).*/\1/p')
        times="$times $t"
    done
    avg=$(echo $times | awk '{s=0; for(i=1;i<=NF;i++) s+=$i; printf "%.6f", s/NF}')
    echo "$n,$avg" >> time_vs_n.csv
    echo "N=$n  time=$avg"
done

echo ""
echo "N,comparisons" > cmp_vs_n.csv
for n in $N_LIST; do
    c=$(./old $n 1 | sed -n 's/.*Comparisons=\([0-9]*\).*/\1/p')
    echo "$n,$c" >> cmp_vs_n.csv
    echo "N=$n  comparisons=$c"
done