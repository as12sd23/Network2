import socket
import threading

IP = 'localhost'
Port = 9000

def Send(client_sock):
    while True:
        data = bytes(input().encode())
        client_sock.send(data)
        
def Recv(client_sock):
    while True:
        data = client_sock.recv(1024).decode()
        print(data)

if __name__ == '__main__':
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.connect((IP, Port))

    Data_Send = threading.Thread(target = Send, args = (client_sock))
    Data_Send.start()
    
    Data_Recv = threading.Thread(target = Recv, args = (client_sock))
    Data_Recv.start()