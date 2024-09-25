from socket import *
from threading import *
import time
import sqlite3
import struct
import datetime
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
-R 요청                                   -S 검색                           -A 친구 신청된거 주세요         -I 알림왔어요
-L 요청 리스트  -Y 수락  -N 거절           -L 리스트  -R 신청                -S 주고 -R 받기                 -R 친구 신청 
-S 주고 -R 받기


DataBase
We
 -F 친구
 -P 신청 
 -B 차단
'''
HEADER_SIZE = 8

fmt = "=4si"
fmt_size = struct.calcsize(fmt)

class ServerRecv(Thread):
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.DBconnect = sqlite3.connect('Chatting.db')
        self.DBcursor = DBconnect.cursor()
        self.DBcursor.execute("SELECT * FROM sqlite_master WHERE type= 'table';")
        TableName = self.DBcursor.fetchall()
        
        if 'Friends' not in TableName or 'Users' not in TableName:
            self.DBcursor.execute("CREATE TABLE IF NOT EXISTS users (id primary key, \
                    password TEXT NOT NULL, \
                    name TEXT NOT NULL, \
                    socket TEXT);")
            self.DBcursor.commit()
            self.DBcursor.execute("CREATE TABLE IF NOT EXISTS friends (id TEXT NOT NULL, \
                        You TEXT NOT NULL, \
                        We_Friend TEXT NOT NULL);")
            self.DBcursor.commit()
            self.DBcursor.execute("CREATE TABLE IF NOT EXISTS chatting (id TEXT NOT NULL, \
                        You TEXT NOT NULL, \
                        chat TEXT NOT NULL, \
                        Date int NOT 0, \
                        Time int NOT 0);")
            self.DBcursor.commit()
        
    def run(self):
       while True:
           try:
               Date = datetime.datetime.now()
               self.Date = Date.year * 10000 + Date.month * 100 + Date.day
               self.Time = Date.hour * 100 + Date.minute;
               recv_data_header = self.sock.recv(HEADER_SIZE)
               header = struct.unpack(fmt, recv_data_header)
               recvData = self.sock.recv(header[1]).decode()
               print(header)
               print(recvData)
           
               if header[0][0] == 109:
                   if header[0][1] == 112:
                       print('개인용 메세지', recvData)
                       recvData = recvData.split(':')
                       self.DataBase.execute("SELECT * FROM users WHERE sock = '%s';", self.sock)
                       my_id = self.DataBase.fetchone()
                       
                       self.DataBase.execute("SELECT * FROM users WHERE name = '%s';"%recvData[0])
                       you_sock = self.DataBase.fetchone()
                       
                       self.DBcursor.execute("INSERT INTO chatting (id, You, chat, Date, Time) VALUES (?, ?, ?, ?, ?);", (my_id[0], you_sock[0], recvData[1], self.Date, self.Time))
                       
                       if my_sock[3] != '':
                           send_header = struct.pack(fmt,b'SF00', len(my_id[2]+":"+recvData[1].encode('utf-8')))
                           you_sock[4].send(send_header + (my_id[2]+":"+recvData[1]).encode('utf-8'))
                           
                   elif header[0][1] == 110:
                       print('1:n메세지 수신', recvData.decode())
                       
               elif header[0][0] == 102:
                   pass
               elif header[0][0] == 83:
                   if header[0][1] == 70:
                       #로그아웃
                       self.DataBase.execute("SELECT * FROM users WHERE socket = '%s';"%self.sock)
                       Imsi_id = self.DataBase.fetchone()
                       self.DataBase.execute("SELECT You FROM friends WHERE We_Friend = '%s' AND id = '%s';"%('F', Imsi_id[0]))
                       Imsi_ids = self.DataBase.fetchall()
                       
                       for i in Imsi_ids:
                           self.DataBase.execute("SELECT sock FROM users WHERE id = '%s';"%i)
                           Imsi_sock = self.DataBase.fetchone()
                           if Imsi_sock != '':
                               send_header = struct.pack(fmt,b'SF00', len(Imsi_id[2].encode('utf-8')))
                               Imsi_sock.send(send_header + Imsi_id[2].encode('utf-8'))
                       
                       self.DataBase.execute("UPDATE users SET socket = '%s' WEHRE socket = '%s';"%('', self.sock))
                       self.DBcursor.commit()
                        
               elif header[0][0] == 85:
                   if header[0][1] == 82:
                       if header[0][2] == 76:
                           if header[0][3] == 82:
                               #친구 요청리스트 주세요
                               self.DataBase.execute("SELECT id FROM users WHERE socket = '%s';"%self.sock)
                               Imsi_id = self.DataBase.fetchone()
                               self.DataBase.execute("SELECT * FROM friends WEHRE You = '&s' AND We_Friend = '%s';"%(Imsi_id, 'A'))
                               Imsi_friend = self.DataBase.fetchone()
                               send_header = struct.pack(fmt,b'URL0', len(Imsi_friend.encode('utf-8')))
                               self.sock.send(send_header + Imsi_friend.encode('utf-8'))
                       elif header[0][2] == 89:
                           #친구 신청 수락할래요
                           self.DataBase.execute("SELECT id FROM users WHERE socket = '%s';"%self.sock)
                           Imsi_id = self.DataBase.fetchone()
                           self.DataBase.execute("SELECT id FROM users WHERE name = '%s';"%recvData)
                           You_id = self.DataBase.fetchone()
                           self.DataBase.execute("UPDATE friends SET We_Friend = '%s' WHERE id = '%s' AND You = '%s' AND We_Friend = '%s';"%('F', You_id, Imsi_id, 'P'))
                           self.DBcursor.commit()
                           self.DataBase.excute("INSERT INTO friends (id, You, We_Friend) VALUES (?, ?, ?);", (Imsi_id, You_id, 'P'))
                           self.DBcursor.commit()
                       elif header[0][2] == 78:
                           #친구 신청 거절할래요
                           self.DataBase.execute("SELECT id FROM users WHERE socket = '%s';"%self.sock)
                           Imsi_id = self.DataBase.fetchone()
                           self.DataBase.execute("SELECT id FROM users WHERE name = '%s';"%recvData)
                           You_id = self.DataBase.fetchone()
                           self.DataBase.execute("DELETE FROM friends WHERE id = '%s' AND You = '%s' AND We_Friend = '%s';"%(Imsi_id, You_id, 'P'))
                           self.DBcursor.commit()
                   elif header[0][1] == 83:
                       if header[0][2] == 76:
                           if header[0][3] == 82:
                               #검색 리스트 주세요
                               if recvData != '':
                                   self.DataBase.execute("SELECT * FROM users WHERE name '%s';"%recvData)
                                   Imsi_name = self.DataBase.fetchall()
                               else:
                                   self.DataBase.execute("SELECT name FROM users LIMIT 25;")    
                                   Imsi_name = self.DataBase.fetchall()
                               send_header = struct.pack(fmt,b'USL0', len(Imsi_name.encode('utf-8')))
                               self.sock.send(send_header + Imsi_name.encode('utf-8'))
                       elif header[0][2] == 82:
                           #친구 신청 할래요
                           self.DataBase.execute("SELECT id FROM users WHERE socket = '%s';"%self.sock)
                           Imsi_id = self.DataBase.fetchone()
                           self.DataBase.execute("SELECT id FROM users WHERE name = '%s';"%recvData)
                           You_id = self.DataBase.fetchone()
                           self.DataBase.excute("INSERT INTO friends (id, You, We_Friend) VALUES (?, ?, ?);", (Imsi_id, You_id, 'P'))
                           self.DBcursor.commit()
               elif header[0][0] == 76:
                   if header[0][1] == 65:
                       print('진입완료')
                       ID,PW = recvData.split()
                       self.DataBase.execute("SELECT EXIST ( SELECT * FROM users WHERE id = '%s' AND password = '%s');"%(ID, PW))
                       
                       if self.DataBase.fetchone() == 1:
                           print('로그인 성공')
                           self.DataBase.execute("UPDATE users SET socket = :sock WHERE id = : ;", {self.sock, ID})
                           self.DBcursor.commit()
                           send_header = struct.pack(fmt,b'LS00', len(row[0].encode('utf-8')))
                           self.sock.send(send_header + row[0].encode('utf-8'))
                       else:
                           print('로그인 아이디 실패')
                           send_header = struct.pack(fmt,b'LF00',0)
                           self.sock.send(send_header)
               
               elif header[0][0] == 65:
                   if header[0][1] == 85:
                       print('받기 완료')
                   #여기서 회원가입 아이디 비번 연결 성공 체크
                       ID,PW,NAME = recvData.split()
                       self.DataBase.execute("SELECT EXISTS ( SELECT * FROM users WHERE id = '%s');"%ID)
                       if self.DataBase.fetchall() == 0:
                           print('1차 통과')
                           self.DataBase.execute("SELECT EXISTS (SELECT * FROM users WHERE name = '%s';"%NAME)
                           if self.DataBase.fetchall() == 0:
                               print("회원가입 성공")
                               self.DataBase.execute("INSERT INTO users (id, password, name) VALUES (?,?,?);", (ID, PW, NAME))
                               self.DB.commit()
                           
                               send_header = struct.pack(fmt,b'AS00',0)
                               self.sock.send(send_header)
                               print('전송 완료')
                           else:
                               print("이름 딴거 해줭")
                               send_header = struct.pack(fmt,b'AFN0',0)
                               self.sock.send(send_header)
                       else:
                           print('아이디 실패')
                           send_header = struct.pack(fmt,b'AFI0',0)
                           self.sock.send(send_header)
                           
           except Exception as e:
               print(e) 
port = 8080

serverSock = socket(AF_INET, SOCK_STREAM)
serverSock.bind(('', port))
serverSock.listen(1)

print('%d번 포트로 접속 대기중...'%port)


while True:
    connectionSock, addr = serverSock.accept()
    connection_socket_list.append(connectionSock)
    print(str(addr), '에서 접속 완료')

    receiver = ServerRecv(connectionSock)

    receiver.start()

