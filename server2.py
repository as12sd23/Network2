from socket import *
from threading import *
import time
import sqlite3
import struct
import datetime
import os
import json
import sys
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
    def __init__(self, sock, addr):
        super().__init__()
        self.sock = sock
        A = {}
        A = {'a' : "asdf", 'b' : 'basdf'}
        self.CloseCount = 0
        self.addr = addr
        self.DBconnect = sqlite3.connect(
            './Chatting8.db', check_same_thread=False)
        self.DBcursor = self.DBconnect.cursor()
        self.DBcursor.execute(
            "SELECT * FROM sqlite_master WHERE type= 'table';")
        TableName = self.DBcursor.fetchall()

        if 'Friends' not in TableName or 'Users' not in TableName:
            self.DBcursor.execute("CREATE TABLE IF NOT EXISTS users (\
                    id varchar(30), \
                    password varchar(21), \
                    name varchar(30), \
                    family varchar(30), \
                    fd varchar(30), \
                    proto varchar(30), \
                    IP varchar(30), \
                    Port varchar(30));")
            self.DBconnect.commit()
            self.DBcursor.execute("CREATE TABLE IF NOT EXISTS friends (id varchar(30), \
                        You varchar(30), \
                        We_Friend varchar(3));")
            self.DBconnect.commit()
            self.DBcursor.execute("CREATE TABLE IF NOT EXISTS chatting (id varchar(30), \
                        You varchar(30), \
                        chat varchar(250), \
                        Date int, \
                        Time int);")
            self.DBconnect.commit()
            
        self.DBcursor.execute("SELECT * FROM users")
        A = self.DBcursor.fetchall()
        

    def run(self):
        while True:
            try:
                Date = datetime.datetime.now()
                self.Date = Date.year * 10000 + Date.month * 100 + Date.day
                self.Time = Date.hour * 100 + Date.minute
                recv_data_header = self.sock.recv(HEADER_SIZE)
                header = struct.unpack(fmt, recv_data_header)
                recvData = self.sock.recv(header[1]).decode()
                print(header)
                print("recvData : " + recvData)
                self.CloseCount = 0

                if header[0][0] == 109:
                    if header[0][1] == 112:
                        
                        sql = f"SELECT name FROM users WHERE \
                        fd = '{self.sock.fileno()}' AND \
                        family = '{self.sock.family}' AND \
                        proto = '{self.sock.proto}' AND \
                        IP = '{self.sock.getpeername()[0]}' AND \
                        Port = '{self.sock.getpeername()[1]}';"
                        self.DBcursor.execute(sql)
                        MyName = self.DBcursor.fetchall()
                        
                        print('개인용 메세지', recvData)
                        recvData = recvData.split(':')
                        sql = f"SELECT (family, IP, Port) FROM users WHERE name = '{recvData[0]}';"
                        self.DBcursor.execute(sql)
                        Imsi_socket_data = self.DBcursor.fetchall()
                        
                        if (Imsi_socket_data[0] == '2'):
                            Imsi_socket = socket(AF_INET, SOCK_STREAM)
                            Imsi_socket.bind(Imsi_socket_data[1], Imsi_socket_data[2])
                            
                            Send_Data = MyName + ":" + recvData
                            send_header = struct.pack(fmt, b'SF00', len(Send_Data.encode('utf-8')))
                            print(send_header)
                            Imsi_socket.send(send_header + Send_Data.encode('utf-8'))

                        self.DBcursor.execute(
                            "SELECT * FROM users WHERE name = '%s';" % recvData[0])
                        you_sock = self.DBcursor.fetchall()

                        self.DBcursor.execute("INSERT INTO chatting (id, You, chat, Date, Time) VALUES (?, ?, ?, ?, ?);", (
                            my_id[0], you_sock[0], recvData[1], self.Date, self.Time))
                        self.DBconnect.commit()
                        
                        
                        
                        if my_sock[3] != '':
                            send_header = struct.pack(fmt, b'SF00', len(
                                my_id[2]+":"+recvData[1].encode('utf-8')))
                            
                            print(send_header)
                            you_sock[4].send(
                                send_header + (my_id[2]+":"+recvData[1]).encode('utf-8'))

                    elif header[0][1] == 110:
                        print('1:n메세지 수신', recvData.decode())

                elif header[0][0] == 102:
                    pass

                elif header[0][0] == 85:
                    if header[0][1] == 85:
                        if header[0][2] == 85:
                            #친구 검색할래요
                            print(recvData)
                            sql = f"SELECT id FROM users WHERE \
                                fd = '{self.sock.fileno()}' AND \
                                family = '{self.sock.family}' AND \
                                proto = '{self.sock.proto}' AND \
                                IP = '{self.sock.getpeername()[0]}' AND \
                                Port = '{self.sock.getpeername()[1]}';"
                                
                            self.DBcursor.execute(sql)
                            My_ID = self.DBcursor.fetchall()
                            sql = f"SELECT id FROM users WHERE name = '{recvData}';"
                            self.DBcursor.execute(sql)
                            Imsi = self.DBcursor.fetchall()
                            
                            '''
                            차단확인용
                            for ID in Imsi:
                                sql = f"SELECT We_friends FROM friends WHERE ME = '{ID[2]}' AND YOU = '{My_ID}' AND We_friends != 'B';"
                                self.DBcursor.execute(sql)
                                if self.DBcursor.fetchall() != '':
                             '''     
                            
                            
                            send_header = struct.pack(fmt, b'UUU0', len(json.dumps(Imsi).encode('utf-8')))
                            print(send_header)
                            self.sock.send(send_header + json.dumps(Imsi).encode('utf-8'))
                        else:
                            # 친구 리스트 주세요
                            sql = f"SELECT id FROM users WHERE \
                                    fd = '{self.sock.fileno()}' AND \
                                    proto = '{self.sock.proto}' AND \
                                    family = '{self.sock.family}' AND \
                                    IP = '{self.sock.getpeername()[0]}' AND \
                                    Port = '{self.sock.getpeername()[1]}';"
                            self.DBcursor.execute(sql)
                            Imsi_id = self.DBcursor.fetchall()
                            
                            sql = f"SELECT You FROM friends WHERE id = '{Imsi_id}' AND We_Friend = 'F';"
                            print(sql)
                            self.DBcursor.execute(sql)
                            Friends = self.DBcursor.fetchall()
                            
                            Imsi_Name = []
                            for i in Friends:
                                sql = f"SELECT name FROM users WHERE id = '{i}';"
                                self.DBcursor.execute(sql)
                                Imsi = self.DBcursor.fetchall()
                                Imsi_Name.append(Imsi)
                        
                                
                            My_Friends_Name = json.dumps(Imsi_Name)
                            send_header = struct.pack(
                                    fmt, b'UU00', len(str(Imsi_Name).encode('utf-8')))
                            print (len(str(Imsi_Name).encode('utf-8')))
                            print(send_header)
                            self.sock.send(send_header + json.dumps(My_Friends_Name).encode('utf-8'))
                                
                    elif header[0][1] == 82:
                        if header[0][2] == 76:
                            if header[0][3] == 82:
                                # 친구 요청리스트 주세요
                                sql = f"SELECT id FROM users WHERE \
                                        fd = '{self.sock.fileno()}' AND \
                                        proto = '{self.sock.proto}' AND \
                                        family = '{self.sock.family}' AND \
                                        IP = '{self.sock.getpeername()[0]}' AND \
                                        Port = '{self.sock.getpeername()[1]}';"
                                self.DBcursor.execute(sql)
                                Imsi_id = self.DBcursor.fetchall()
                                
                                sql = f"SELECT * FROM friends WEHRE You = '{Imsi_id}' AND We_Friend = 'A';"
                                self.DBcursor.execute(sql)
                                Imsi_friend = self.DBcursor.fetchall()
                                
                                send_header = struct.pack(
                                    fmt, b'URL0', len(Imsi_friend.encode('utf-8')))
                                print(len(Imsi_friend.encode('utf-8')))
                                print(send_header)
                                self.sock.send(
                                    send_header + Imsi_friend.encode('utf-8'))
                        elif header[0][2] == 89:
                            # 친구 신청 수락할래요
                            sql = f"SELECT id FROM users WHERE \
                                    fd = '{self.sock.fileno()}' AND \
                                    proto = '{self.sock.proto}' AND \
                                    family = '{self.sock.family}' AND \
                                    IP = '{self.sock.getpeername()[0]}' AND \
                                    Port = '{self.sock.getpeername()[1]}';"
                            self.DBcursor.execute(sql)
                            Imsi_id = self.DBcursor.fetchall()
                            
                            sql = f"SELECT id FROM WHERE name = 'recvData';"
                            self.DBcursor.execute(sql)
                            You_id = self.DBcursor.fetchall()
                            
                            sql = f"UPDATE friends SET We_Friend = 'F' WHERE id = '{You_id}' AND You = '{Imsi_id}' AND We_Friend != 'Z';"
                            self.DBcursor.execute(sql)
                            self.DBconnect.commit()
                            
                            sql = f"INSERT INTO friends (id, You, We_Friend) VALUES ({Imsi_id}, {You_id}, 'P');"
                            self.DBcursor.execute(sql)
                            self.DBconnect.commit()
                            
                        elif header[0][2] == 78:
                            # 친구 신청 거절할래요
                            sql = f"SELECT id FROM users WHERE \
                                    fd = '{self.sock.fileno()}' AND \
                                    proto = '{self.sock.proto}' AND \
                                    family = '{self.sock.family}' AND \
                                    IP = '{self.sock.getpeername()[0]}' AND \
                                    Port = '{self.sock.getpeername()[1]}';"
                            self.DBcursor.execute(sql)
                            Imsi_id = self.DBcursor.fetchall()
                            
                            sql = f"SELECT id FROM users WHERE name = '{recvData}';"
                            self.DBcursor.execute(sql)
                            You_id = self.DBcursor.fetchall()
                            
                            sql = f"UPDATE friends SET We_Friend = 'Z' WHERE You = '{Imsi_id}' AND id = '{You_id}';"
                            self.DBcursor.execute(sql)
                            self.DBconnect.commit()
                            
                    elif header[0][1] == 83:
                        if header[0][2] == 76:
                            if header[0][3] == 82:
                                # 검색 리스트 주세요
                                if recvData != '':
                                    sql = f"SELECT name FROM users WHERE name = '{recvData}';"
                                    self.DBcursor.execute(sql)
                                    Imsi_name = self.DBcursor.fetchall()
                                else:
                                    self.DBcursor.execute(
                                        "SELECT name FROM users LIMIT 50;")
                                    Imsi_name = self.DBcursor.fetchall()
                                
                                send_header = struct.pack(
                                    fmt, b'USL0', len(json.dumps(Imsi_name).encode('utf-8')))
                                print(len(Imsi_name.encode('utf-8')))
                                print(send_header)
                                self.sock.send(
                                    send_header + json.dumps(Imsi_name).encode('utf-8'))
                        elif header[0][2] == 82:
                            # 친구 신청 할래요
                            sql = f"SELECT id FROM users WHERE \
                                    fd = '{self.sock.fileno()}' AND \
                                    proto = '{self.sock.proto}' AND \
                                    family = '{self.sock.family}' AND \
                                    IP = '{self.sock.getpeername()[0]}' AND \
                                    Port = '{self.sock.getpeername()[1]}';"
                            self.DBcursor.execute(sql)
                            Imsi_id = self.DBcursor.fetchall()
                            
                            sql = f"SELECT id FROM users WHERE name = '{recvData}';"
                            self.DBcursor.execute(sql)
                            You_id = self.DBcursor.fetchall()
                            
                            sql = f"INSERT INTO friends (id, You, We_Friend) VALUES ({Imsi_id}, {You_id}, 'P');"
                            self.DBcursor.excute(sql)
                            self.DBconnect.commit()
                            
                elif header[0][0] == 76:
                    if header[0][1] == 65:
                        print('진입완료')
                        ID, PW = recvData.split()
                        
                        self.DBcursor.execute("SELECT * FROM users WHERE id = '%s';" %ID)
                        DB_id = self.DBcursor.fetchone()
                        print(DB_id)
                        print(ID)
                        print(PW)
                        if not DB_id:
                            print('로그인 아이디 실패')
                            send_header = struct.pack(fmt, b'LF00', 0)
                            self.sock.send(send_header)
                        elif PW == DB_id[1]:
                            print('로그인 성공')
                            self.DBcursor.execute("SELECT * FROM users WHERE id = '%s';"%ID)
                            ABC = self.DBcursor.fetchall()
                            
                            sql = f"UPDATE users SET \
                                family = '{self.sock.family}' AND \
                                fd = '{self.sock.fileno()}' AND \
                                proto = '{self.sock.proto}' AND \
                                IP = '{str(self.sock.getpeername()[0])}' AND \
                                Port = '{str(self.sock.getpeername()[1])}';"
                            print(sql)
                            self.DBcursor.execute(sql)
                            self.DBconnect.commit()
                            
                            send_header = struct.pack(
                                fmt, b'LS00', len((DB_id[0]+"#"+DB_id[2]).encode('utf-8')))
                            print(len((DB_id[0]+"#"+DB_id[2]).encode('utf-8')))
                            print(send_header)
                            self.sock.send(
                                send_header + (DB_id[0]+"#"+DB_id[2]).encode('utf-8'))

                elif header[0][0] == 65:
                    if header[0][1] == 85:
                        print('받기 완료')
                    # 여기서 회원가입 아이디 비번 연결 성공 체크
                        ID, PW, NAME = recvData.split()
                        sql = f"SELECT id FROM users WHERE id LIKE '{ID}';"
                        self.DBcursor.execute(sql)
                        
                        if not self.DBcursor.fetchall():
                            print('1차 통과')
                            sql = f"SELECT name FROM users WHERE name = '{NAME}';"
                            self.DBcursor.execute(sql)
                            if not self.DBcursor.fetchall():
                                print("회원가입 성공")
                                sql = f"INSERT INTO users (id, password, name) VALUES ('{ID}', '{PW}', '{NAME}');"
                                self.DBcursor.execute(sql)
                                self.DBconnect.commit()
                                
                                send_header = struct.pack(fmt, b'AS00', 0)
                                
                                self.sock.send(send_header)
                                print('전송 완료')
                            else:
                                print("이름 딴거 해줭")
                                send_header = struct.pack(fmt, b'AFN0', 0)
                                self.sock.send(send_header)
                        else:
                            print('아이디 실패')
                            send_header = struct.pack(fmt, b'AFI0', 0)
                            self.sock.send(send_header)

            except ConnectionResetError:
                print("들어오지는거 맞지?")
                self.sock.close()
                
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(f'file name: {str(fname)}')
                print(f'error type: {str(exc_type)}')
                print(f'error msg: {str(e)}')
                print(f'line number: {str(exc_tb.tb_lineno)}')

port = 8080

serverSock = socket(AF_INET, SOCK_STREAM)
serverSock.bind(('', port))
serverSock.listen(1)

print('%d번 포트로 접속 대기중...' % port)


while True:
    connectionSock, addr = serverSock.accept()
    connection_socket_list.append(connectionSock)
    print(str(addr), '에서 접속 완료')
    print(connectionSock)
    print(connectionSock.family)
    print(connectionSock.fileno())
    print(connectionSock.proto)
    print()
    print(connectionSock.getpeername()[0])
    print(connectionSock.getpeername()[1])
    print()
    print(connectionSock.getsockname()[0])
    print(connectionSock.getsockname()[1])
    receiver = ServerRecv(connectionSock, addr)

    receiver.start()
