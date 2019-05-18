from scapy.all import raw
import random
import struct
import time

class Worker:

    def __init__(self, master, target):
        self.master = master
        self.target = target
        self.crashes = {}

    def run(self):
        while True:
            start, end, iterations = self.master.next_task()
            if start is None:
                time.sleep(1)
                continue
            for task in range(start, end):
                print('processing task', task)
                self.target.start()
                seq = self.target.sequence(task)
                print(seq)
                for _ in range(iterations):
                    testcase = []
                    for msg in seq:
                        testcase.append(raw(msg))
                        self.target.send(testcase[-1])
                    if not self.target.is_running():
                        if self.target.is_crashed():
                            print("Server crashed after", testcase)
                            signature = (self.target.crash_signal,
                                    self.target.crash_offset,
                                    self.target.crash_reason,
                                    self.target.crash_path)
                            if signature not in self.crashes:
                                self.crashes[signature] = self.target.crash_log
                                self.master.submit_crash(task,
                                        self.target.crash_signal,
                                        self.target.crash_reason,
                                        self.target.crash_ip,
                                        self.target.crash_offset,
                                        self.target.crash_path,
                                        self.target.crash_log,
                                        testcase)
                        self.target.stop()
                        # let OS cleanup resources
                        print("Restarting server after", testcase)
                        self.target.start()
                self.target.stop()
                self.master.task_completed(task)
        self.target.stop()
        print("completed")
