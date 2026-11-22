# Лабораторная работа № 5. Технология MPI. Введение

`lab5.cpp` — исходный пример из задания. В `mpi_lab5.cpp` данные распределяются блоками через `MPI_Scatterv`. Замер охватывает поиск и редукцию после распределения. Программа OpenMP собирается из `origin/lab1:lab1/new.c`.

Для запуска на macOS нужны Apple Clang, Open MPI, libomp, Python с matplotlib и Typst.

~~~sh
cd lab5
make check
make run MPI_FLAGS=--oversubscribe
make report
~~~

Исполняемые файлы хранятся в системном временном каталоге. `make plot` строит графики из сохранённых замеров. Результаты OpenMP с Linux используются для сравнения с повторным запуском OpenMP на Mac в отчёте.
