from socket import *
from threading import *
import time
import struct
import os
import sys
from PyQt5.QtWidgets import*
from PyQt5 import uic
from PyQt5.QtCore import *
import json


FILE_READ_DATA = 1024
HEADER_SIZE = 8    
fmt = '=4si'
fmt_size = struct.calcsize(fmt)
RECV_FILE_PATH = 'C:/Users/c403/Desktop/aaaa/python/저장 폴더'

form_class = uic.loadUiType('test.ui')[0]
login_form_class = uic.loadUiType('client.ui')[0]
Accession_form_class = uic.loadUiType('Accession.ui')[0]
Friend_form_class = uic.loadUiType('Friend.ui')[0]

#메인 윈도우 클래스
class WindowClass(QMainWindow, form_class):
    def __init__(self, sock):
        super().__init__()
        self.setupUi(self)
        self.sock = sock
        
        self.hide()
        self.Login = Login_Windowclass(self.sock)
        self.Login.exec()
        self.show()
        
        print("누가 범인이냐")
        self.Chatting_Send_Button.clicked.connect(self.Chatting_Send)
        self.Chatting.returnPressed.connect(self.Chatting_Send)
        self.File_Send_Button.clicked.connect(self.File_Send)
        self.Friend_Button.clicked.connect(self.FriendWindows_Create_Button)
        print("말하면 안혼낸다")
        self.receive = Receive(self.sock)
        self.receive.Chatting_Signal.connect(self.Chatting_Slot)
        self.receive.File_Sending_Signal.connect(self.File_Sending_Slot)
        self.receive.File_End_Signal.connect(self.File_End_Slot)
        self.receive.start()
        
        
        
        struct_header = struct.pack(fmt, b'UU00', 0)
        self.sock.send(struct_header)
        
    
    def closeEvent(self, event):
        send_data_header = struct.pack(fmt,b'SF00', 0)
        self.sock.send(send_data_header)
    
    def File_Send(self):
        file_path = QFileDialog.getOpenFileName(self,'Open file','./')
        
        file_name = os.path.basename(file_path[0]).encode('utf-8')
        filesize = os.path.getsize(file_path[0])
        file_path = file_path[0].replace('/','\\')
        
        send_data_header = struct.pack(fmt,b'fps0', len(file_name))
        self.sock.send(send_data_header + file_name)
        
        
        with open(file_path, 'rb') as f:
            while True:
                print('#', end= '')
                data = f.read(FILE_READ_DATA)
                filesize = filesize - FILE_READ_DATA
                
                if not data:
                    break
                
                if filesize <= 0:
                    send_data_header = struct.pack(fmt, b'fpe0', len(data))
                else:
                    send_data_header = struct.pack(fmt, b'fpd0', len(data))
                self.sock.send(send_data_header + data)
                time.sleep(1)
            self.Chatting_list.appendPlainText('파일 전송 완료')
            
    def FriendWindows_Create_Button(self):
        print("너 왜 작동함?")
        self.Friend = FriendWindowClass(self.sock)
        self.Friend.show()
        app.exec_()
        
    def Chatting_Send(self):
        print("너도 작동하냐?")
        sendData=self.Chatting.text()
        if sendData != '':
            self.Chatting_list.appendPlainText('나 : ' + sendData)
            send_data_header = struct.pack(fmt,b'mp00',len(sendData.encode('utf-8')))
            self.sock.send(send_data_header + sendData.encode('utf-8'))
            self.Chatting.clear()


    @pyqtSlot(str)
    def Chatting_Slot(self,chat):
        self.Chatting_list.appendPlainText('상대방 : ' + chat)
    
    @pyqtSlot(str)
    def File_Sending_Slot(self,chat):
        self.Chatting_list.appendPlainText(chat)
    
    @pyqtSlot(str)
    def File_End_Slot(self,chat):
        self.Chatting_list.appendPlainText(chat)

class Receive(QThread):
    Chatting_Signal = pyqtSignal(str)
    File_Sending_Signal = pyqtSignal(str)
    File_End_Signal = pyqtSignal(str)
    
    def __init__(self,sock):
        super().__init__()
        self.RECV_FILE_NAME =''
        self.sock = sock
        self.AllData=b''
        
        
    def run(self):
        while True:
            try:
                recv_data_header = self.sock.recv(HEADER_SIZE)
                header = struct.unpack(fmt,recv_data_header)
                recvData = self.sock.recv(header[1].decode())
                
                if header[0][0] == 85:
                    if header[0][1] == 85:
                        self.Friends_Name = json.loads(recvData)
                        for i in self.Friends_Name:
                            Friend_List.append(self.Friends_Name[i])
                elif header[0][0] == 109:
                    if header[0][1] == 112:
                        self.Chatting_Signal.emit(recvData.decode())
                elif header[0][0]==102:
                    if header[0][1] == 112:
                        if header[0][2] == 115:
                            self.RECV_FILE_NAME = recvData.decode()
                        elif header[0][2] == 100:
                            self.File_Sending_Signal.emit('파일 전송 중')
                            self.AllData += recvData
                        elif header[0][2]==101:
                            self.AllData += recvData
                            with open(RECV_FILE_PATH + '/' + self.RECV_FILE_NAME, 'wb')as f:
                                f.write(self.AllData)
                            
                            self.AllData =b''
                            self.File_End_Signal.emit('파일 전송 완료')
                elif header[0][0] == 85:
                    if header[0][1] == 82:
                        if header[0][2] == 76:
                            #요청 리스트 주는거
                            print(recvData.decode())
                    elif header[0][1] == 83:
                        if header[0][2] == 76:
                            # 검색 리스트 주는거
                            pass
                    elif header[0][1] == 65:
                        if header[0][2] == 76:
                            # 친구 신청 리스트 주는거
                            pass
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(f'file name: {str(fname)}')
                print(f'error type: {str(exc_type)}')
                print(f'error msg: {str(e)}')
                print(f'line number: {str(exc_tb.tb_lineno)}')
'''
U 친구
-R 요청                                   -S 검색                           -A 친구 신청된거 주세요
-L 요청 리스트  -Y 수락  -N 거절           -L 리스트  -R 신청


'''
#친구검색창
class FriendWindowClass(QDialog,QWidget,Friend_form_class):
    def __init__(self, sock):
        super().__init__()
        self.setupUi(self)
        self.sock = sock
        self.Friend_Name_Button.clicked.connect(self.User_Button)
        self.Friend_Search_Button.clicked.connect(self.User_Search_List)
        self.Friend_Accept_Button.clicked.connect(self.User_Accept_List)
        self.Friend_List.itemClicked.connect(self.Friend_ListView)
        self.Friend_State = False
        self.Friend_List_Save = []
    def User_Search_List(self):
        #U 
        #-r 찾기
        self.Friend_Name_Edit.clear()
        send_data_header = struct.pack(fmt , b'USL0',0)
        self.sock.send(send_data_header)
        self.Friend_State = False
        
    def User_Accept_List(self):
        self.Friend_Name_Edit.clear()
        send_data_header = struct.pack(fmt , b'URL0', 0)
        self.sock.send(send_data_header)
        self.Friend_State = True
        
    def User_Button(self):
        Send_NickName = self.Friend_Name_Edit.text()
        if Send_NickName != '':
            if self.Friend_State == False:
                send_data_header = struct.pack(fmt , b'USL0',len(Send_NickName.encode('utf-8')))
                self.sock.send(send_data_header + Send_NickName.encode('utf-8'))
            else:
                pass
            
    def Friend_ListView(self):
        friend = self.Friend_List.currentItem()
        if self.Friend_State == False:
            friend_event = QMessageBox.question(self,'알림','해당 친구에게 추가 요청을 합니다',
                                 QMessageBox.Yes | QMessageBox.No)
            
            if friend_event == QMessageBox.Yes:
                self.sock.send(send_data_header+friend.encode('utf-8'))
        else:
            friend_event = QMessageBox.question(self,'알림','친구 수락 거절',
                                 QMessageBox.Yes | QMessageBox.No)
            
            if friend_event == QMessageBox.Yes:
                send_data_header = struct.pack(fmt,b'URY0',len(friend.encode('utf-8')))#친구 요청 보냄
                self.sock.send(send_data_header + friend.encode('utf-8'))
            elif friend_event == QMessageBox.No:
                send_data_header = struct.pack(fmt,b'URN0',len(friend.encode('utf-8')))#친구 요청 보냄
                self.sock.send(send_data_header+friend.encode('utf-8'))
#회원가입 윈도우 클래스
class AccessionWindowClass(QDialog,QWidget,Accession_form_class):
    def __init__(self,sock):
        super().__init__()
        self.setupUi(self)
        self.sock = sock
        self.Accession_Button.clicked.connect(self.AccessionFunction)
        self.Receive = Accession_Receive(self.sock)
        self.Receive.ASignal.connect(self.Signal)
        self.Receive.start()
        self.send_Data = b''
    
    def AccessionFunction(self):
        ID_Data = self.ID_Edit.text()
        PW_Data = self.PW_Edit.text()
        NAME_Data = self.NAME_Edit.text()
        
        self.send_Data = ID_Data + ' ' + PW_Data + ' ' + NAME_Data
        
        if ID_Data != '' and PW_Data != '' and NAME_Data != '':
            send_data_header = struct.pack(fmt, b'AU00', len(self.send_Data.encode('utf-8')))
            self.sock.send(send_data_header + self.send_Data.encode('utf-8'))
        
    @pyqtSlot(int)
    def Signal(self, AAA):
            
        if AAA == 0:
            QMessageBox.about(self, '알림', '회원가입 성공')
            self.close()
        elif AAA == 1:
            QMessageBox.about(self, '알림', '아이디 중복')
        elif AAA == 2:
            QMessageBox.about(self, '알림', '닉네임 중복')
        else:
            QMessageBox.about(self, '알림', 'Error')
        
class Accession_Receive(QThread):
    ASignal = pyqtSignal(int)
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        
    def run(self):
        while True:
            try:
                print('진입됨')
                recv_data_header = self.sock.recv(HEADER_SIZE)
                header = struct.unpack(fmt,recv_data_header)
                recvData=self.sock.recv(header[1])
                print(recvData)
                
                if header[0][0] == 65:
                    print('받기 완료')
                    if header[0][1] == 83:
                        self.ASignal.emit(0)
                    elif header[0][1] == 70:
                        if header[0][2] == 73:
                            #아이디 중복
                            self.ASignal.emit(1)
                        elif header[0][2] == 78:
                            #닉네임 중복
                            self.ASignal.emit(2)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(f'file name: {str(fname)}')
                print(f'error type: {str(exc_type)}')
                print(f'error msg: {str(e)}')
                print(f'line number: {str(exc_tb.tb_lineno)}')

#로그인 윈도우 클래스
class Login_Windowclass(QDialog,QWidget,login_form_class):
    
    def __init__(self, sock):
        super().__init__()
        self.setupUi(self)
        self.sock = sock
        self.Login_Button.clicked.connect(self.LoginSend)
        self.Accession_Button.clicked.connect(self.AccessionSend)
        self.Receive = Login_Receive(sock)
        self.Receive.LSignal.connect(self.Signal)
        self.Receive.start()
        self.send_Data = ''
    
    def closeEvent(self, event):
            pass
    def LoginSend(self,sock):
        ID_Data = self.ID_Edit.text()
        PW_Data = self.PW_Edit.text()
        
        if ID_Data != '' and PW_Data != '':
            self.send_Data = ID_Data + ' ' + PW_Data
            send_data_header = struct.pack(fmt , b'LA00',len(self.send_Data.encode('utf-8')))
            self.sock.send(send_data_header + self.send_Data.encode('utf-8'))
    
    def AccessionSend(self):
        self.hide()
        self.Accession = AccessionWindowClass(self.sock)
        self.Accession.exec()
        self.show()
    
    def Signal(self, BBB):
        
        if BBB == False:
            QMessageBox.about(self,'알림','로그인 실패')
        else:
            self.close()
           
class Login_Receive(QThread):
    LSignal = pyqtSignal(bool)
    def __init__(self,sock):
        super().__init__()
        self.sock = sock
        
    def run(self):
        while True:
            try:
                recv_data_header=self.sock.recv(HEADER_SIZE)
                header = struct.unpack(fmt,recv_data_header)
                recvData=self.sock.recv(header[1])
                
                if header[0][0] == 76:
                    if header[0][1] == 83:
                        self.LSignal.emit(True)
                    elif header[0][1] == 70:
                        self.LSignal.emit(False)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(f'file name: {str(fname)}')
                print(f'error type: {str(exc_type)}')
                print(f'error msg: {str(e)}')
                print(f'line number: {str(exc_tb.tb_lineno)}')

port = 8080
clientSock = socket(AF_INET, SOCK_STREAM)
clientSock.connect(('localhost', port))
print(clientSock)
print(clientSock.family)
print(clientSock.fileno())
print(clientSock.proto)
print()
print(clientSock.getpeername()[0])
print(clientSock.getpeername()[1])
print()
print(clientSock.getsockname()[0])
print(clientSock.getsockname()[1])
app = QApplication(sys.argv)
window = WindowClass(clientSock)
window.show()
app.exec_()


while True:
    time.sleep(1)
    
    pass
