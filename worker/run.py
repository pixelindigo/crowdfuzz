from api import RemoteMaster
from local import LocalMaster
from worker import Worker
from testtarget import TestTarget
from ptracetarget import PtraceTarget
import time
import os

if __name__ == '__main__':
    master_uri = os.environ.get('MASTER_URI', None)

    if master_uri is None:
        master = LocalMaster(4, 3, 100)
    else:
        print("Listening for ", master_uri)
        master = RemoteMaster(master_uri)

    w = Worker(master, PtraceTarget())
    start = time.time()
    w.run()
    end = time.time()
    print('Completed in', end - start, 'sec')
