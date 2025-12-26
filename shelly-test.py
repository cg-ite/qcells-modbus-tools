import socket
import json

def udp_client(host='192.168.1.24', port=2220):
    request = {
    'jsonrpc': '2.0',
    'method': 'EM.GetStatus',
    'params': {'id': 1},
    'id': 1
    }
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.sendto(json.dumps(request).encode(), (host, port))
        data, _ = s.recvfrom(4096)
        print('Antwort:', json.loads(data.decode()))

if __name__ == '__main__':
# In zwei Terminals starten:
# 1. udp_server()
    udp_client()