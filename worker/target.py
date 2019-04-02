from scapy.all import fuzz
from utils import to_base

class Target:
    def __init__(self, base, packets):
        self.base = base
        self.packets = packets

    def sequence(self, index):
        return [self.base / fuzz(self.packets[int(x)])
                for x in to_base(index, len(self.packets))]

    def start(self):
        raise NotImplementedException()
    
    def stop(self):
        raise NotImplementedException()

    def send(self, data):
        raise NotImplementedException()

    def recv(self, size):
        raise NotImplementedException()

    def is_running(self):
        raise NotImplementedException()
