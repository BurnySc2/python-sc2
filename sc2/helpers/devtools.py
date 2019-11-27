import time
from contextlib import contextmanager


@contextmanager
def time_this(label):
    start = time.perf_counter_ns()
    try:
        yield
    finally:
        end = time.perf_counter_ns()
        print(f"TIME {label}: {(end-start)/1000000000} sec")


# Use like this
if __name__ == "__main__":
    with time_this("square rooting"):
        for n in range(10 ** 7):
            x = n ** 0.5


# returns:
# TIME square rooting: 2.307249782 sec