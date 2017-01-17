from multiprocessing import Process, Value, Array, Queue
import ch_test

if __name__ == '__main__':
    num = Value('d', 0.0)
    softpl = Array('i', range(10))

    p = Process(target=ch_test.ch.run, args=(num, arr))
    p.start()
