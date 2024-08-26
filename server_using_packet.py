from socket import *
from threading import *
import time
import struct
connection_socket_list = []

'''
 0  메세지인지(m),             파일이면(f)     닉네임(n)   친구(u)                   상태(s)
 1  1:1메세지 : p, 1:n메세지:n              중복체크(y/n)   요청(r) 수락거절(y/n)    온라인상태(o/f)
 2  파일이름전송:s 파일 수락:a 파일 거절:r 데이터:d 데이터전송끝:e 
 3
 
 4   크기 고정
 5
 6
 7
'''

HEADER_SIZE = 8

fmt = "=4si"
fmt_size = struct.calcsize(fmt)

def Another_Sock(MySock):
    return connection_socket_list[connection_socket_list.index(MySock) -1] 

def send(sock):
    '''
    while True:
        sendData = input('>')
        sock.send(sendData.encode('utf-8'))
'''
class ServerRecv(Thread):
    def __init__(self, sock):
        try:
            self.sock = sock
            self.data_list = []
            with open("User_data.txt",'r') as f:
                while True:
                    Data = f.readline()
                    if not Data:
                        break
                    Data = eval(Data)
                    print(Data)
                    self.data_list.append(Data)
                    
        except Exception as e:
            print(e)
        
    def Run(self):
       while True:
           try:
               recv_data_header = self.sock.recv(HEADER_SIZE)
               header = struct.unpack(fmt, recv_data_header)
               recvData = self.sock.recv(header[1])
               print(header)
               print(recvData)
           
               if header[0][0] == 109:
                   if header[0][1] == 112:
                       print('개인용 메세지', recvData.decode())
                       another_socket = Another_Sock(sock)
                       another_socket.send(recv_data_header+recvData)
                   
                   elif header[0][1] == 110:
                       print('1:n메세지 수신', recvData.decode())
               elif header[0][0] == 102:
                   another_socket = Another_Sock(sock)
                   another_socket.send(recv_data_header+recvData)
               
               elif header[0][0] == 76:
                   if header[0][1] == 65:
                       ID,PW = recvData.decode().split()
                       if ID in self.data_list:
                           DataPW, DataName = self.data_list[ID]
                           if PW == DataPW:
                               send_header = struct.pack(fmt,b'LS00', len(DataName.encode('utf-8')))
                               self.sock.send(send_header + DataName.encode('utf-8'))
                           else:
                               send_header = struct.pack(fmt,b'LF00',0)
                               self.sock.send(send_header)
                               
                       else:
                           send_header = struct.pack(fmt,b'LF00',0)
                           self.sock.send(send_header)
               
               elif header[0][0] == 65:
                   if header[0][1] == 85:
                       print('받기 완료')
                       ID,PW,NAME = recvData.decode().split()
                       Accept = False
                       print(ID)
                       print(PW)
                       print(NAME)
                       print()
                       #여기서 회원가입 아이디 비번 연결 성공 체크
                       if ID in self.data_list:
                           print('아이디 실패')
                           send_header = struct.pack(fmt,b'AFI0',0)
                           sock.send(send_header)
                       else:
                           print('1차 통과')
                           for i in self.data_list.keys():
                               if NAME == list(self.data_list.values())[i][1]:
                                   print("이름 딴거 해줭")
                                   Accept = True
                                   break
                               
                           if Accept == True:
                               send_header = struct.pack(fmt,b'AFN0',0)
                               sock.send(send_header)
                           else:
                               print("회원가입 성공")
                               User_data_list = {}
                               User_data_list[ID] = [PW, NAME]
                               with open("User_data.txt",'a') as f:
                                   f.write(repr(User_data_list) + "\n")
                                   print('저장 완료')
                               self.data_list.append(User_data_list)
                               send_header = struct.pack(fmt,b'AS00',0)
                               sock.send(send_header)
                               print('전송 완료')
                           
           except Exception as e:
               print(e) 
port = 8888
serverSock = socket(AF_INET, SOCK_STREAM)
serverSock.bind(('', port))
serverSock.listen(1)

print('%d번 포트로 접속 대기중...'%port)


while True:
    connectionSock, addr = serverSock.accept()
    connection_socket_list.append(connectionSock)
    print(str(addr), '에서 접속 완료')

    sender = Thread(target = send, args = (connectionSock, ))
    receiver = ServerRecv()

    sender.start()
    receiver.start()

