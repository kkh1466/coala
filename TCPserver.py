import threading
import socket
import time

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

    def send(self, msg):
        for student in self.clients:
            if student.id != self.teacher_id:
                student.send(msg)

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



class Student(Client):
    def __init__(self, id:str, sock:socket.socket, room:Room):
        self.id = id
        self.sock = sock
        self.room = room
        self.ping_sw = True


    def disconnect(self):
        msg='disconnect:'+self.id
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
                while msg[-3:]!='end':
                    message=self.sock.recv(1024)
                    message=message.decode()
                    msg+=message
                msg = msg[:-3]

                if msg == 'disconnect':
                    break

                self.room.clients[0].send(msg)
                print(msg)

        except Exception:
            if self in self.room.clients:
                if self.ping_sw == True:
                    self.disconnect() 

        if self.ping_sw == True:
            self.disconnect() 


    def ping(self):
        try:
            while True:
                self.sock.sendall('ping'.encode(encoding='utf-8'))
                time.sleep(3)
        except Exception:
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
        self.room.send('teacher_disconnect')   # 학생들에게 선생님이 종료되었다는 메세지를 날림
        self.sock.close()
        self.room.remove(self)
        server.rooms.remove(self.room)    # 방폭파
        server.socks.remove((self.sock, self.id))  # 원본 소켓 삭제
        print(len(server.socks))
        del self.room
        print('선생님', self.id, '가 종료하였습니다.')
        del self


    def receive(self):
        try:
            while True:
                msg=''
                while msg[-3:]!='end':
                    message=self.sock.recv(1024)
                    message=message.decode()
                    msg+=message
                msg = msg[:-3]

                if msg == 'disconnect':
                    break

                self.room.send(msg)
                print(msg)

        except Exception:
            if self in self.room.clients:
                if self.ping_sw == True:
                    self.disconnect() 
                
        if self.ping_sw == True:
            self.disconnect() 



    def ping(self):
        try:
            while True:
                self.sock.sendall('ping'.encode(encoding='utf-8'))
                time.sleep(3)
        except Exception:
            if self.ping_sw == True:
                self.disconnect()


    def run(self):
        t1 = threading.Thread(target=self.receive, args=())
        t2 = threading.Thread(target=self.ping, args=())
        t1.start()
        t2.start()



class ServerMain:
    ip = ''
    port = 15976

    def __init__(self):
        self.rooms = []   # server에 만들어진 모든방을 넣을 list
        self.socks = []   # server에 접속한 모든 소켓은 넣을 list
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

            msg = 'If you are teacher input (teacher:your_id), else (student:teacher_id:your_id)'
            c_soc.sendall(msg.encode(encoding='utf-8'))
            data = c_soc.recv(1024)
            get_data = data.decode()

            if get_data[:8] == 'teacher:':
                data_list = get_data.split(':')
                teacher_id = data_list[1]

                new_room = Room(teacher_id)
                teacher = Teacher(teacher_id, c_soc, new_room)

                self.socks.append((c_soc, teacher_id))  # server class에 원본 소켓 저장
                self.rooms.append(new_room)
                new_room.add(teacher)
                
                print(teacher_id, 'connected')
                print(new_room.teacher_id,'에 접속한 인원 :',new_room)
                teacher.run()

            elif get_data[:8] == 'student:':
                data_list = get_data.split(':')
                teacher_id=data_list[1]
                student_id=data_list[2]
                
                sw=True
                for room in self.rooms:
                    if room.teacher_id == teacher_id:
                        student = Student(student_id, c_soc, room)

                        self.socks.append((c_soc, student_id)) # server class에 원본 소켓 저장
                        room.add(student)
                        msg='connect:'+student_id
                        room.clients[0].send(msg)

                        print(student_id, 'connected in', room.teacher_id)
                        print(room.teacher_id,'에 접속한 인원 :',room)
                        student.run()
                        sw=False

                if sw:
                    print('not existed teacher_id')
                    c_soc.sendall('not existed teacher_id'.encode(encoding='utf-8'))
                    continue

            else:
                print('client input wrong sentence')
                c_soc.sendall('wrong sentence'.encode(encoding='utf-8'))
                continue

server = ServerMain()
server.run()