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

#메인 윈도우 클래스
class WindowClass(QMainWindow, form_class):
    def __init__(self, sock, NickName):
        super(WindowClass, self).__init__()
        self.setupUi(self)
        self.sock = sock
        
        self.NickName = NickName
        
        self.Chatting_Send_Button.clicked.connect(self.Chatting_Send)
        self.Chatting.returnPressed.connect(self.Chatting_Send)
        self.File_Send_Button.clicked.connect(self.File_Send)
        
        self.receive = Receive(self.sock)
        self.receive.Chatting_Signal.connect(self.Chatting_Slot)
        self.receive.File_Sending_Signal.connect(self.File_Sending_Slot)
        self.receive.File_End_Signal.connect(self.File_End_Slot)
        self.receive.start()
    
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
                recvData = self.sock.recv(header[1])
                
                if header[0][0] == 109:
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

#회원가입 윈도우 클래스
class AccessionWindowClass(QDialog,QWidget,Accession_form_class):
    def __init__(self,sock):
        super().__init__()
        self.setupUi(self)
        self.sock = sock
        self.Accession_Button.clicked.connect(self.AccessionFunction)
        self.Receive = Accession_Receive(sock)
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
            QMessageBox(self,'알림','아이디 중복')
        elif error == 'N':
            QMessageBox(self,'알림','닉네임 중복')
    
    @pyqtSlot(str)
    def Success_Slot(self, message):
        if (message == 'S'):
            QMessageBox(self,'알림','회원가입 성공')
            self.close()
            second_window = Login_Windowclass(self.sock)
            second_window.exec()
            second_window.show()


class Accession_Receive(QThread):
    Accession_Error=pyqtSignal(str)
    Accession_Success = pyqtSignal(str)
    
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        print(self.sock)
    def run(self):
        while True:
            print('A')
            try:
                recv_data_header = self.sock.recv(HEADER_SIZE)
                header = struct.unpack(fmt,recv_data_header)
                recvData = self.sock.recv(header[1])
                print(header)
                print('받기 완료')
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
    def __init__(self,sock):
        super().__init__()
        self.setupUi(self)
        self.sock = sock
        self.Login_Button.clicked.connect(self.LoginSend)
        self.Accession_Button.clicked.connect(self.AccessionSend)
        self.Receive = Login_Receive(sock)
        self.Receive.Login_Signal.connect(self.Login_Slot)
        self.Receive.start()
        self.send_Data = ''
    
    def LoginSend(self,sock):
        ID_Data = self.ID_Edit.text()
        PW_Data = self.PW_Edit.text()
        
        if ID_Data != '' and PW_Data != '':
            self.send_Data = ID_Data + ' ' + PW_Data
            send_data_header = struct.pack(fmt , b'LA00',len(self.send_Data.encode('utf-8')))
            self.sock.send(send_data_header + self.send_Data.encode('utf-8'))
    
    def AccessionSend(self):
        self.close()
        Accession = AccessionWindowClass(self.sock)
        Accession.show()
        Accession.exec()
        
    @pyqtSlot(object)
    def Login_Slot(self,Access):
        if Access[0] == True:
            QMessageBox.about(self,'알림','로그인 성공')
            self.close()
            window = WindowClass(self.sock, Access[1])
            window.show()
        elif Access[0] == False:
            QMessageBox.about(self,'알림','로그인 실패')
        
class Login_Receive(QThread):
    Login_Signal = pyqtSignal(object)
    
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
                        self.Login_Signal.emit((True, recvData.decode()))
                    elif header[0][1] == 70:
                        self.Login_Signal.emit(False, 'Fail')
            except Exception as e:
                print(e)

port = 8888
clientSock = socket(AF_INET, SOCK_STREAM)
clientSock.connect(('localhost', port))

app = QApplication(sys.argv)
window = Login_Windowclass(clientSock)
window.show()
app.exec_()


while True:
    time.sleep(1)
    
    pass
