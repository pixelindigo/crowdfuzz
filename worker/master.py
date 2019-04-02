class Master:

    def next_task(self):
        """Return start, end indices and number of iterations to fuzz each sequence"""
        raise NotImplementedException()

    def task_completed(self, index):
        raise NotImplementedException()

    def submit_crash(self, index, signal, reason, instruction,
            offset, path, log, testcase=None):
        raise NotImplementedException()
