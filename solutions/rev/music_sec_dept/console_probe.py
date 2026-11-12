import socket, time, threading, sys
ctl = socket.create_connection(("127.0.0.1", 5555), timeout=5)
ctl.sendall(bytes([1]))  # start clock
print("clock started", flush=True)
time.sleep(2)

s = socket.create_connection(("127.0.0.1", 4562), timeout=10)
start = time.time()

def reader():
    while True:
        try:
            data = s.recv(4096)
        except Exception:
            break
        if not data:
            print(f"[{time.time()-start:6.2f}] EOF", flush=True)
            break
        print(f"[{time.time()-start:6.2f}] RECV {data!r}", flush=True)

t = threading.Thread(target=reader, daemon=True)
t.start()

time.sleep(5)  # let boot banner appear
cmds = ["CUE IKOW[g", "SYNC", "EQ music'_'", "KEY M4ch1n3_K3y!", "DECK", "EXPORT 9a3f", "RECALL"]
for c in cmds:
    print(f"[{time.time()-start:6.2f}] SEND {c!r}", flush=True)
    s.sendall((c + "\n").encode())
    time.sleep(12)
time.sleep(10)
print("DONE")
