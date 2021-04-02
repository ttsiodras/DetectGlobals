"""
A utility class to allow an easy - and very importantly, stable - way
to use multiple cores for the execution of a loop.

Each core will execute one loop iteration.

There are very nice (syntactically speaking) libraries, like
concurrent.futures, that do this work - but sadly, every time I used them
I found out that there's the occasional weird "gets stuck" issue; some
mysterious race-condition triggered only on occasion? I don't know.
Whatever it is, my simple solution here (first implemented for the
TASTE's orchestrator) doesn't suffer from it; and works solidly across
multiple native Linux distros, chroots, Docker containers, etc.
"""
import sys
import time
import multiprocessing

from typing import List, Any  # NOQA


class MultiCoreLoop:
    def __init__(self, consumer):
        self.running_instances = 0
        self.res_queue = multiprocessing.Queue()  # type: Any
        self.list_of_processes = []  # type: List[Any]
        self.consumer = consumer

    def spawn(self, target, args):
        if self.running_instances >= multiprocessing.cpu_count():
            for result in self.res_queue.get():
                self.consumer(result)
            all_are_still_alive = True
            while all_are_still_alive:
                for idx_proc, proc in enumerate(
                        self.list_of_processes):
                    child_alive = proc.is_alive()
                    all_are_still_alive = \
                        all_are_still_alive and child_alive
                    if not child_alive:
                        del self.list_of_processes[idx_proc]
                        break
                else:
                    time.sleep(1)
            self.running_instances -= 1
        proc = multiprocessing.Process(target, args)
        self.list_of_processes.append(proc)
        proc.start()
        self.running_instances += 1

    def join(self):
        for proc in self.list_of_processes:
            proc.join()
            if proc.exitcode != 0:
                print("[x] Failure in one of the child processes...")
                sys.exit(1)
            for result in self.res_queue.get():
                self.consumer(result)
