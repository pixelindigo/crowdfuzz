from master import Master


class LocalMaster(Master):

    def __init__(self, messages, depth, iterations):
        self.messages = messages
        self.depth = depth
        self.iterations = iterations
        self.next_sequence = 0
        self.last_sequence = int(str(self.messages - 1) * self.depth, self.messages)

    def next_task(self):
        """Return start, end indices and number of iterations to fuzz each sequence"""
        start = self.next_sequence
        end = start + 3
        if end > self.last_sequence:
            end = self.last_sequence
        if start >= self.last_sequence:
            return None, None, None
        self.next_sequence = end
        return start, end, self.iterations

    def task_completed(self, index):
        print('Seq', index, 'completed')

    def submit_crash(self, index, signal, reason, instruction,
            offset, path, log, testcase=None):
        print('Crashed at', index, testcase)
        print(f'{path}: {instruction:x} [{offset:x}]')
        print(log)
