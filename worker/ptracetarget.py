from proto import proto
from target import Target
from ptrace.debugger import PtraceDebugger, ProcessExit, ProcessSignal
from ptrace.debugger.child import createChild
from ptrace.debugger.memory_mapping import readProcessMappings
import socket
import signal

class PtraceTarget(Target):

    def __init__(self, cmd, env=None):
        super().__init__(proto['base'], proto['messages'])
        self.pid = None
        self.cmd = cmd
        self.env = env

    def start(self, addr):
        if self.is_running():
            return
        self.pid = createChild(self.cmd, False, self.env)
        self.dbg = PtraceDebugger()
        self.process = self.dbg.addProcess(self.pid, True)
        self.process.cont()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', 55555))
        self.addr = addr

    def stop(self):
        self.dbg.quit()
        self.pid = None

    def send(self, data):
        self.sock.sendto(data, self.addr)

    def recv(self, max_bytes):
        data, addr = self.sock.recvfrom(max_bytes)
        return data

    def is_running(self):
        if self.pid is None:
            return False
        self.event = self.dbg.waitProcessEvent(self.pid, blocking=False)
        #if self.event != None and (self.event.signum == signal.SIGCHLD or self.event.signum == signal.SIGINT):
        #    self.process.cont()
        #    self.event = None
        return self.event == None

    def is_crashed(self):
        if isinstance(self.event, ProcessExit):
            return False
        if isinstance(self.event, ProcessSignal):
            ip = self.process.getInstrPointer()
            self.crash_ip = ip
            self.crash_offset = None
            self.crash_path = None
            for start, end, _, offset, path in self._read_maps():
                if ip >= start and ip <= end:
                    self.crash_offset = ip - start + offset
                    self.crash_path = path
                    break

            self.crash_log = ''
            self.event.display(log=self._collect_crash_info)
            self.crash_signal = self.event.name
            self.crash_reason = self.event.reason.__class__.__name__
            return True

        return False
    
    def _collect_crash_info(self, info):
        self.crash_log += info + '\n'
    
    def _read_maps(self):
        res = []
        with open(f'/proc/{self.pid}/maps') as maps:
            for line in maps:
                line = line.split()
                start, end = line[0].split('-')
                perm = line[1]
                offset = line[2]
                path = line[5] if len(line) > 5 else ''
                res.append((int(start, 16), int(end, 16),
                    perm,
                    int(offset, 16),
                    path))
        return res
