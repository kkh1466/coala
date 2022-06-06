import threading
import socket
import time
import sys
import os

# dev-api.coala.services

class thread_with_exception(threading.Thread):
    def __init__(self, t, a):
        threading.Thread(target=t, args=a)
    
    def raise_exception(self): 
        thread_id = self.get_id() 
        os.kill(thread_id, 2)


class Room:
    def __init__(self, teacher_id):
        self.teacher_id = teacher_id
        self.clients = []

    def add(self, client):
        self.clients.append(client)

    def remove(self, client):
        if client in self.clients:
            self.clients.remove(client)
        print(self.teacher_id,'에 남은 인원 :', self)

    # 방의 모든 사람들에게 메세지를 전달하는 메서드
    def send(self, msg):
        for student in self.clients:
            if student.id != self.teacher_id:
                student.send(msg)

    # 방의 특정 한명에게 메세지를 전달하는 메서드
    def dm(self, student_id, msg):
        for client in self.clients:
            if client.id == student_id:
                client.send(msg)
                break

    def __str__(self):
        c = ''
        for i in self.clients:
            c += str(i.id) + ' '
        return c



class Client:
    def __init__(self, id:str, sock:socket.socket, room:Room):
        self.id = id
        self.sock = sock
        self.room = room

    def send(self, msg):
        try:
            self.sock.sendall(msg.encode(encoding='utf-8'))
        except:
            print("error")

    def ping(self):
        try:
            while True:
                self.sock.sendall('ping'.encode(encoding='utf-8'))
                #print('ping♩')
                time.sleep(3)
        except Exception:
            print('ping')
            if self.ping_sw == True:
                self.disconnect()



class Student(Client):
    def __init__(self, id:str, sock:socket.socket, room:Room):
        self.id = id
        self.sock = sock
        self.room = room
        self.ping_sw = True


    # 학생이 종료
    def disconnect(self):
        msg='disconnect♬'+self.id+'♩'
        self.room.clients[0].send(msg)
        self.ping_sw = False
        self.sock.close()
        self.room.remove(self)
        print('학생', self.id, '가 종료하였습니다.')
        server.socks.remove((self.sock, self.id))  # 원본 소켓 삭제
        print(len(server.socks))
        del self
    

    # 선생님의 종료로 인한 강제종료
    def t_disconnect(self):
        self.ping_sw = False
        msg = 'teacher_disconnect♩'
        self.send(msg)
        self.sock.close()
        self.room.remove(self)
        print('학생', self.id, '가 종료하였습니다.')
        server.socks.remove((self.sock, self.id))  # 원본 소켓 삭제
        print(len(server.socks))
        del self


    def receive(self):
        try:
            while True:
                msg=''
                while msg[-3:] != 'end':
                    message=self.sock.recv(1024)
                    message=message.decode()
                    msg+=message

                if msg == 'disconnectend':
                    break

                msg=self.id+":"+msg
                self.room.clients[0].send(msg)
                print(msg)

        except Exception:
            if self in self.room.clients:
                if self.ping_sw == True:
                    self.disconnect() 

        if self.ping_sw == True:
            self.disconnect() 


    def run(self):
        t1 = threading.Thread(target=self.receive, args=())
        t2 = threading.Thread(target=self.ping, args=())
        t1.start()
        t2.start()




class Teacher(Client):
    def __init__(self, id:str, sock:socket.socket, room:Room):
        self.id = id
        self.sock = sock
        self.room = room
        self.ping_sw = True


    def disconnect(self):
        self.ping_sw = False
        for i in reversed(range(len(self.room.clients)-1)):  # 학생들을 순차적으로 종료
            self.room.clients[i+1].t_disconnect()
        time.sleep(2)
        self.sock.close()
        self.room.remove(self)
        server.rooms.remove(self.room)    # 방폭파
        server.socks.remove((self.sock, self.id))  # server의 원본 소켓 삭제
        print(len(server.socks))
        del self.room
        print('선생님', self.id, '가 종료하였습니다.')
        del self


    def receive(self):
        try:
            while True:
                msg=''
                while msg[-3:] != 'end':
                    message=self.sock.recv(1024)
                    message=message.decode()
                    msg+=message

                if msg == 'disconnect♩':
                    break

                msg_list = msg.split(':')
                if msg_list[0] == 'all':
                    print('all')
                    self.room.send(msg[1])
                else:
                    print('dm')
                    self.room.dm(msg_list[0], msg_list[1])
                
                print(msg)
            
            if self.ping_sw == True:
                self.disconnect() 

        except Exception:
            #if self in self.room.clients:
            if self.ping_sw == True:
                self.disconnect() 


    def run(self):
        t1 = threading.Thread(target=self.receive, args=())
        t2 = threading.Thread(target=self.ping, args=())
        t1.start()
        t2.start()



class Dummy(Client):
    def __init__(self, c_soc:socket.socket):
        self.sock = c_soc
        self.ping_sw = True
        self.event = threading.Event()
        msg = 'If you are teacher input (teacher:your_id), else (student:teacher_id:your_id)'
        try:
            self.sock.sendall(msg.encode(encoding='utf-8'))
        except:
            print("error")

    
    def disconnect(self):
        self.ping_sw = False
        time.sleep(1)
        server.dummy_socks.remove(self.sock)
        del self


    def make_student(self, get_data):
        data_list = get_data.split(':')
        teacher_id=data_list[1]
        student_id=data_list[2]
        
        sw=True
        for room in server.rooms:
            if room.teacher_id == teacher_id:
                student = Student(student_id, self.sock, room)

                server.socks.append((self.sock, student_id)) # server class에 원본 소켓 저장
                room.add(student)
                msg='connect♬'+student_id+'♩'
                room.clients[0].send(msg)

                print(student_id, 'connected in', room.teacher_id)
                print(room.teacher_id,'에 접속한 인원 :',room)
                student.run()
                sw=False

        if sw:
            print('not existed teacher_id')
            self.send('not existed teacher_id')
        else:
            if self.ping_sw == True:
                self.disconnect() 


    def make_teacher(self, get_data):
        data_list = get_data.split(':')
        teacher_id = data_list[1]

        new_room = Room(teacher_id)
        teacher = Teacher(teacher_id, self.sock, new_room)

        server.socks.append((self.sock, teacher_id))  # server class에 원본 소켓 저장
        server.rooms.append(new_room)
        new_room.add(teacher)
        
        print(teacher_id, 'connected')
        print(new_room.teacher_id,'에 접속한 인원 :',new_room)
        teacher.run()

        if self.ping_sw == True:
            self.disconnect() 


    def receive(self, event):
        try:
            while True:
                get_data=''
                while get_data[-3:]!='end':
                    message=self.sock.recv(1024)
                    message=message.decode()
                    get_data+=message

                get_data = get_data[:-3]

                if get_data == 'disconnect':
                    self.disconnect()

                if get_data[:8] == 'teacher:':
                    self.make_teacher(get_data)
                    event.wait()
                elif get_data[:8] == 'student:':
                    self.make_student(get_data)
                else:
                    self.send('you submit wrong message')
            
        except Exception:
            if self.ping_sw == True:
                self.disconnect() 
                

    def run(self):
        t1 = threading.Thread(target=self.receive, args=(self.event,))
        t2 = threading.Thread(target=self.ping, args=())
        t1.start()
        t2.start()


class ServerMain:
    ip = '127.0.0.1'
    port = 15976

    def __init__(self):
        self.rooms = []   # server에 만들어진 모든방을 넣을 list
        self.socks = []   # server에 접속한 모든 소켓은 넣을 list (sock, id)의 튜플형태로 저장
        self.dummy_socks = []
        self.server_soc = None

    def open(self):
        self.server_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_soc.bind((ServerMain.ip, ServerMain.port))
        self.server_soc.listen(10)

    def run(self):
        self.open()
        while True:
            c_soc, addr = self.server_soc.accept()
            print(addr)

            self.dummy_socks.append(c_soc)
            dummy=Dummy(c_soc)
            dummy.run()


server = ServerMain()
server.run()