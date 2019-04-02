from master import Master
import base64
import requests


class RemoteMaster(Master):

    def __init__(self, uri):
        self.uri = uri

    def next_task(self):
        """Return start, end indices and number of iterations to fuzz each sequence"""
        try:
            r = requests.get(self.uri + '/api/task/next')
        except:
            return None, None, None
        if r.status_code != 200:
            return None, None, None
        r = r.json()
        if r['status'] != "OK":
            print(r['status'])
            return None, None, None
        return r['task']['start'], r['task']['end'], r['task']['iterations']

    def task_completed(self, index):
        r = requests.post(self.uri + f'/api/task/{index}/completed')

    def submit_crash(self, index, signal, reason, instruction,
            offset, path, log, testcase=None):
        requests.post(self.uri + '/api/crash/submit', json={
            'index': index,
            'signal': signal,
            'reason': reason,
            'instruction': hex(instruction) if instruction else None,
            'offset': hex(offset) if offset else None,
            'path': path,
            'log': log,
            'testcase': [base64.b64encode(x).decode('utf8') for x in testcase]
            })
