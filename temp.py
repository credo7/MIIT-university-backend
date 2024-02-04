from threading import Thread
import time

def background_task(print_value):
    while True:
        if print_value == 0:
            print(print_value)

def calc_func():
    sum = 0
    for i in range(100000000):
        sum += i

def main():
    start = time.time()
    first_thread = Thread(target=background_task, args=("first",), daemon=True)
    first_thread.start()
    calc_func()
    print(time.time() - start)


if __name__ == '__main__':
    main()