from socket import *
from threading import *
import time
import sqlite3
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
'''
U 친구
-R 요청                                   -S 검색                           -A 친구 신청된거 주세요
-L 요청 리스트  -Y 수락  -N 거절           -L 리스트  -R 신청                 -S 주고 -R 받기
-S 주고 -R 받기

'''
HEADER_SIZE = 8

fmt = "=4si"
fmt_size = struct.calcsize(fmt)

class ServerRecv(Thread):
    def __init__(self, sock, DataBase, DB):
        super().__init__()
        self.sock = sock
        self.DataBase = DataBase
        self.DB = DB
        
    def run(self):
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
                   
               elif header[0][0] == 85:
                   if header[0][1] == 82:
                       if header[0][2] == 76:
                           if header[0][3] == 82:
                               #친구 요청리스트 주세요
                       elif header[0][2] == 89:
                           #친구 신청 수락할래요
                       elif header[0][2] == 78:
                           #친구 신청 거절할래요
                   elif header[0][1] == 83:
                       if header[0][2] == 76:
                           if header[0][3] == 82:
                               #검색 리스트 주세요
                       elif header[0][2] == 82:
                           #친구 신청 할래요
               
               elif header[0][0] == 76:
                   if header[0][1] == 65:
                       print('진입완료')
                       ID,PW = recvData.decode().split()
                       select_Login = 'SELECT * FROM users WHERE id = ?'
                       self.DataBase.execute(select_Login, ('ID', ))
                       row = self.DataBase.fetchone()
                       
                       if row:
                           if PW == row[2]:
                               print('로그인 성공')
                               send_header = struct.pack(fmt,b'LS00', len(row[0].encode('utf-8')))
                               self.sock.send(send_header + row[0].encode('utf-8'))
                           else:
                               print('로그인 비밀번호 실패')
                               send_header = struct.pack(fmt,b'LF00',0)
                               self.sock.send(send_header)
                               
                       else:
                           print('로그인 아이디 실패')
                           send_header = struct.pack(fmt,b'LF00',0)
                           self.sock.send(send_header)
               
               elif header[0][0] == 65:
                   if header[0][1] == 85:
                       print('받기 완료')
                       ID,PW,NAME = recvData.decode().split()
                       Accept = False
                       select_ID = 'SELECT id FROM users'
                       self.DataBase.execute(select_ID)
                       ids = self.DataBase.fetchall()
                       #여기서 회원가입 아이디 비번 연결 성공 체크
                       for i in ids:
                           if i[1] == ID:
                               Accept = True
                               print('아이디 실패')
                               send_header = struct.pack(fmt,b'AFI0',0)
                               self.sock.send(send_header)
                       
                       if Accept == False:
                           print('1차 통과')
                           select_query = 'SELECT name FROM users'
                           
                           self.DataBase.execute(select_query)
                           names = self.DataBase.fetchall()
                           
                           for i in names:
                               if NAME == i[0]:
                                   print("이름 딴거 해줭")
                                   Accept = True
                                   break
                                   
                           if Accept == True:
                               send_header = struct.pack(fmt,b'AFN0',0)
                               self.sock.send(send_header)
                           else:
                               print("회원가입 성공")
                               
                               Insert_query = '''
                               INSERT INTO users (name, id, password)
                               VALUES (?, ?, ?)
                               '''
                               data = (ID, NAME, PW)
                               self.DataBase.execute(Insert_query, data)
                               self.DB.commit()
                               
                               send_header = struct.pack(fmt,b'AS00',0)
                               self.sock.send(send_header)
                               print('전송 완료')
                           
           except Exception as e:
               print(e) 
port = 8888
conn = sqlite3.connect('example.db')
cursor = conn.cursor()

serverSock = socket(AF_INET, SOCK_STREAM)
serverSock.bind(('', port))
serverSock.listen(1)

print('%d번 포트로 접속 대기중...'%port)


while True:
    connectionSock, addr = serverSock.accept()
    connection_socket_list.append(connectionSock, cursor, conn)
    print(str(addr), '에서 접속 완료')

    receiver = ServerRecv(connectionSock)

    receiver.start()

