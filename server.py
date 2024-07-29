import socket
import threading

def handle(groupIP):
    while True:
        for conn in groupIP:
            msg = "메세지 왔음"
            conn.send(bytes(msg.encode()))

def Recv(conn):
    while True:
        data = conn.recv(1024).decode()
        print(data)

if __name__ == '__main__':
    port = 9000
    SendIP = ""
    
    serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSock.bind((SendIP, port))
    serverSock.listen(10)
    
    groupIP = []
    count = 0
    print('클라이언트 접속 대기 중')
    
    while True:
        conn, addr = serverSock.accept()
        count += 1
        print('클라이어트 접속 완료 :', addr)
        print(count)
        groupIP.append(conn)
        for i in groupIP:
            print(i)
            print("-----------------------------------")
        if count > 1:
            send = threading.Thread(target = handle(), args = (groupIP,))
            send.start()
        
        if count > 1:
            recv = threading.Thread(target = Recv(), args = (conn))
            recv.start()