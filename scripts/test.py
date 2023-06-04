from memory_profiler import profile
import tqdm


def my_func():
    a = [1] * (10 ** 6)
    b = [2] * (2 * 10 ** 7)
    # del b
    b = None
    return a

@profile
def generator():
  for i in range(10):
    yield my_func()

if __name__ == '__main__':
    for res in generator():
      res = None