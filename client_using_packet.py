from socket import *
from threading import *
import time
import struct
import os
import sys
from PyQt5.QtWidgets import*
from PyQt5 import uic
from PyQt5.QtCore import *


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
        self.Login.show()
        self.Login.Login_Signal.connect(self.Login_close)
        
        self.Chatting_Send_Button.clicked.connect(self.Chatting_Send)
        self.Chatting.returnPressed.connect(self.Chatting_Send)
        self.File_Send_Button.clicked.connect(self.File_Send)
        
        self.receive = Receive(self.sock)
        self.receive.Chatting_Signal.connect(self.Chatting_Slot)
        self.receive.File_Sending_Signal.connect(self.File_Sending_Slot)
        self.receive.File_End_Signal.connect(self.File_End_Slot)
        self.receive.start()
        
        struct_header = struct.pack(fmt, b'UU00', 0)
        self.sock.send(struct_header)
        
    @pyqtSlot(bool)
    def Login_close(self, Login):
        print(Login)
        if Login == False:
            self.close()
    
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
            
        
        
    def Chatting_Send(self):
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
                        print(recvData)
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
            except Exception as e:
                print(e)
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
                send_data_header = struct.pack(fmt , b'USL0',len(self.Send_NickName.encode('utf-8')))
                self.sock.send(send_data_header + self.Send_NickName.encode('utf-8'))
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
            
class Friend_Receive(QThread):
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
    
    def run(self):
        while True:
            try:
                recv_data_header = self.sock.recv(HEADER_SIZE)
                header = struct.unpack(fmt, recv_data_header)
                recvData = self.sock.recv(header[1].decode())
                print(recvData)
                
                if header[0][0] == 85:
                    if header[0][1] == 82:
                        if header[0][2] == 76:
                            #요청 리스트 주는거
                            pass
                    elif header[0][1] == 83:
                        if header[0][2] == 76:
                            # 검색 리스트 주는거
                            pass
                    elif header[0][1] == 65:
                        if header[0][2] == 76:
                            # 친구 신청 리스트 주는거
                            pass
            except Exception as e:
                print(e)
#회원가입 윈도우 클래스
class AccessionWindowClass(QDialog,QWidget,Accession_form_class):
    def __init__(self,sock):
        super().__init__()
        self.setupUi(self)
        self.sock = sock
        self.Accession_Button.clicked.connect(self.AccessionFunction)
        self.Receive = Accession_Receive(self.sock)
        self.Receive.Accession_Error.connect(self.Error_Slot)
        self.Receive.Accession_Success.connect(self.Success_Slot)
        self.Receive.start()
        self.send_Data = b''
    
    def AccessionFunction(self):
        ID_Data = self.ID_Edit.text()
        PW_Data = self.PW_Edit.text()
        NAME_Data = self.NAME_Edit.text()
        
        self.send_Data = ID_Data + ' ' + PW_Data + ' ' + NAME_Data
        
        if ID_Data != '' and PW_Data != '' and NAME_Data != '':
            send_data_header = struct.pack(fmt,b'AU00',len(self.send_Data.encode('utf-8')))
            self.sock.send(send_data_header + self.send_Data.encode('utf-8'))
    
    @pyqtSlot(str)
    def Error_Slot(self,error):
        if error == 'I':
            QMessageBox.about(self,'알림','아이디 중복')
        elif error == 'N':
            QMessageBox.about(self,'알림','닉네임 중복')
    
    @pyqtSlot(str)
    def Success_Slot(self, message):
        if (message == 'S'):
            QMessageBox.about(self,'알림','회원가입 성공')
            self.close()
            
class Accession_Receive(QThread):
    Accession_Error = pyqtSignal(str)
    Accession_Success = pyqtSignal(str)
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        
    def run(self):
        while True:
            try:
                recv_data_header = self.sock.recv(HEADER_SIZE)
                header = struct.unpack(fmt,recv_data_header)
                recvData=self.sock.recv(header[1])
                
                if header[0][0] == 65:
                    print('받기 완료')
                    if header[0][1] == 83:
                        Accession_Success.emit('S')
                    elif header[0][1] == 70:
                        if header[0][2] == 73:
                            #아이디 중복
                            Accession_Error.emit('I')
                        elif header[0][2] == 78:
                            #닉네임 중복
                            Accession_Error.emit('N')
            except Exception as e:
                print(e)

#로그인 윈도우 클래스
class Login_Windowclass(QDialog,QWidget,login_form_class):
    Login_Signal = pyqtSignal(bool)
    def __init__(self,sock):
        super().__init__()
        self.setupUi(self)
        self.sock = sock
        self.Login_Button.clicked.connect(self.LoginSend)
        self.Accession_Button.clicked.connect(self.AccessionSend)
        self.Receive = Login_Receive(sock)
        self.Receive.Login_Signal.connect(self.Login_Slot)
        self.Receive.start()
        self.Login = False
        self.send_Data = ''
    
    def closeEvent(self, event):
        if self.Login == False:
            self.Login_Signal.emit(False)
        else:
            self.Login_Signal.emit(True)
            
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
        self.Accession.show()
        
    @pyqtSlot(bool)
    def Login_Slot(self,Access):
        if Access == True:
            #QMessageBox.about(self,'알림','로그인 성공')
            self.Login = True
            self.close()
        elif Access == False:
            QMessageBox.about(self,'알림','로그인 실패')
        
class Login_Receive(QThread):
    Login_Signal = pyqtSignal(bool)
    
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
                        self.Login_Signal.emit(True)
                    elif header[0][1] == 70:
                        self.Login_Signal.emit(False)
            except Exception as e:
                print(e)

port = 8080
clientSock = socket(AF_INET, SOCK_STREAM)
clientSock.connect(('localhost', port))
print(clientSock)
app = QApplication(sys.argv)
window = WindowClass(clientSock)
window.show()
app.exec_()


while True:
    time.sleep(1)
    
    pass
