from target import Target
import subprocess
import socket
import signal

class TestTarget(Target):

    def start(self):
        self.p = subprocess.Popen(["./server"], stdout=subprocess.PIPE)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addr = ('127.0.0.1', 31337)
    
    def stop(self):
        self.p.kill()

    def send(self, data):
        self.sock.sendto(b'\xff\xff\xff\xff' + data, self.addr)

    def is_running(self):
        return self.p.poll() == -signal.SIGSEGV
