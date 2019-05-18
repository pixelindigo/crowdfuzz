from boofuzz import *
from proto import HLSession, HLSocketConnection

def main():
    with open('steam.cert', 'rb') as f:
        steam_cert = f.read()
    session = HLSession(
        steam_cert=steam_cert,
        target=Target(
            connection=HLSocketConnection("127.0.0.1", 27015, bind=('127.0.0.1', 17973))
            #connection=HLSocketConnection("192.168.56.101", 27015, bind=('192.168.56.1', 17973))
        ),sleep_time=0.1
    )

    s_initialize("new")
    s_static("\x01")
    s_string(b'\x01\x01\x01\x00\x00\x00\x00', size=7)

    s_initialize("nop")
    s_static(b'\x01')
    s_string(b'\x01\x01\x01\x01\x01\x01\x01', size=7)

    session.connect(s_get("nop"))
    #session.connect(s_get("steamchallenge"), s_get("connect"), callback=process_challenge)

    session.fuzz()


if __name__ == "__main__":
    main()
