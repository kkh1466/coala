import threading
import socket
import time
from datetime import datetime


log_sw=True
def save_log(log_msg):
    try:
        log=open('log.txt','a',encoding='utf-8')
        print(log_msg)
        log.write(log_msg)
    except:
        print('log open error')
    finally:
        log.close()


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
        # if log_sw:
        #     msg=str(datetime.now())+' '+self.teacher_id+' 에 남은 인원 : '+ self.str() +'\n'
        #     save_log(msg)

    def send(self, msg):
        for student in self.clients:
            if student.id != self.teacher_id:
                student.send(msg)

    def __str__(self):
        c = ''
        for i in self.clients:
            c += str(i.id) + ' '
        return c

    def str(self):
        c = ''
        for i in self.clients:
            c += str(i.id) + ' '
        return c



class Client:
    def __init__(self, id:str, sock:socket.socket, room:Room):
        self.id = id
        self.sock = sock
        self.room = room
        self.ping_sw = True
        self.pong_time = time.time()


    def send(self, msg):
        try:
            self.sock.sendall(msg.encode(encoding='utf-8'))
        except:
            print("error")


    def ping(self):
        try:
            while True:
                if self.ping_sw==False:
                    break
                self.send('ping┯')
                time.sleep(3)
        except Exception:
            if self.ping_sw == True:
                print('ping_disconnect')
                self.disconnect()

    def pong(self):
        while True:
            now=time.time()
            if now-self.pong_time >= 5:
                if self.ping_sw == True:
                    print('pong_disconnect')
                    self.disconnect()
            time.sleep(1)

    def run(self):
        t1 = threading.Thread(target=self.receive, args=())
        t2 = threading.Thread(target=self.ping, args=())
        t3 = threading.Thread(target=self.pong, args=())
        t1.daemon=True
        t2.daemon=True
        t3.daemon=True
        t1.start()
        t2.start()
        t3.start()



class Student(Client):
    def __init__(self, id:str, sock:socket.socket, room:Room):
        self.id = id
        self.sock = sock
        self.room = room
        self.ping_sw = True
        self.pong_time = time.time()


    def disconnect(self):
        self.ping_sw = False
        msg='disconnect:'+self.id+'┯'
        self.room.clients[0].send(msg)
        self.sock.close()
        self.room.remove(self)

        print('학생', self.id, '가 종료하였습니다.')
        # if log_sw:
        #     msg=str(datetime.now())+' '+'학생 '+self.id+' 가 종료하였습니다.\n'
        #     save_log(msg)

        del server.students[self.id]
    

    # 선생님의 종료로 인한 강제종료
    def t_disconnect(self):
        self.ping_sw = False
        self.sock.close()
        self.room.remove(self)

        print('학생', self.id, '가 종료하였습니다.')
        # if log_sw:
        #     msg=str(datetime.now())+' '+'학생 '+self.id+' 가 종료하였습니다.\n'
        #     save_log(msg)

        del server.students[self.id]  # 원본 소켓 삭제


    def receive(self):
        try:
            while True:
                msg=''
                while msg[-1:]!='┯':
                    message=self.sock.recv(1024)
                    message=message.decode()
                    msg+=message
                msg = msg[:-1]

                if msg == 'disconnect':
                    break
                elif msg == 'pong':
                    self.pong_time = time.time()

                self.room.clients[0].send(msg)
                print(msg)

        except Exception:
            if self.ping_sw == True:
                self.disconnect() 

        if self.ping_sw == True:
            self.disconnect()



class Teacher(Client):
    def __init__(self, id:str, sock:socket.socket, room:Room):
        self.id = id
        self.sock = sock
        self.room = room
        self.ping_sw = True
        self.pong_time = time.time()


    def disconnect(self):
        self.ping_sw = False
        self.room.send('teacher_disconnect┯')   # 학생들에게 선생님이 종료되었다는 메세지를 날림
        for i in reversed(range(len(self.room.clients)-1)):  # 학생들을 순차적으로 종료
            self.room.clients[i+1].t_disconnect()
        time.sleep(1)
        self.sock.close()
        self.room.remove(self)
        server.rooms.remove(self.room)    # 방폭파
        del server.teachers[self.id]      # 원본 소켓 삭제

        print('선생님', self.id, '가 종료하였습니다.')
        # if log_sw:
        #     msg=str(datetime.now())+' '+'선생님 '+self.id+' 가 종료하였습니다.\n'
        #     save_log(msg)


    def receive(self):
        try:
            while True:
                msg=''
                while msg[-1:]!='┯':
                    message=self.sock.recv(1024)
                    message=message.decode()
                    msg+=message
                msg = msg[:-1]

                if msg == 'disconnect':
                    break
                elif msg == 'pong':
                    self.pong_time = time.time()

                self.room.send(msg)
                print(msg)

        except Exception as e:
            if self.ping_sw == True:
                print(e)
                self.disconnect() 
                
        if self.ping_sw == True:
            self.disconnect() 



class ServerMain:
    ip = '127.0.0.1'
    port = 15976

    def __init__(self):
        self.rooms = []     # server에 만들어진 모든방을 넣을 list
        self.teachers = {}  # server에 접속한 선생님들의 소켓과 id를 저장할 dic, {teachers_id:teacher객체}형태로 저장
        self.students = {}  # server에 접속한 학생들의 소켓과 id를 저장할 dic, 위와 같은 방식으로 저장
        self.server_soc = None


    def open(self):
        self.server_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_soc.bind((ServerMain.ip, ServerMain.port))
        self.server_soc.listen(10)


    def make_student(self, get_data, sock:socket.socket):
        data_list = get_data.split(':')
        teacher_id=data_list[1]
        student_id=data_list[2]

        # 중복 접속시 기존 접속 해제
        # 딕셔너리 형태이기때문에 in연산자로 먼저 데이터 존재여부 확인(O(1)) 후, 반복문으로 재탐색
        if student_id in self.students:
            for student in self.students:
                if student_id == student:
                    self.students[student].send('disconnect┯')
                    self.students[student].disconnect()
                    break
        
        sw=True  # 성공적으로 방에 들어갔는지 확인하는 switch 변수
        for room in self.rooms:
            if room.teacher_id == teacher_id:
                student = Student(student_id, sock, room)

                self.students[student_id]=student  # 학생 dictionary에 정보 저장
                room.add(student)  # 방에 학생을 넣음

                msg='connect:'+student_id+'┯'
                room.clients[0].send(msg)  # 선생님에게 학생 접속 메세지 전송

                print(student_id, 'connected in', room.teacher_id)
                print(room.teacher_id,'에 접속한 인원 :',room)
                student.run()
                sw=False

        if sw:   # 학생이 방에 들어가지 못했다면
            print('not existed teacher_id')
            # if log_sw:
            #     msg=str(datetime.now())+' not existed teacher_id\n'
            #     save_log(msg)
            return False
        else:    # 학생이 방에 잘 들어갔다면
            return True


    def make_teacher(self, get_data, sock:socket.socket):
        data_list = get_data.split(':')
        teacher_id = data_list[1]

        # 중복 접속시 기존 접속 해제
        if teacher_id in self.teachers:
            for room in self.rooms:
                if room.teacher_id==teacher_id:
                    room.clients[0].send('disconnect┯')
                    room.clients[0].disconnect()  # 선생님 diconnect
                    break
            
        new_room = Room(teacher_id)
        teacher = Teacher(teacher_id, sock, new_room)

        self.teachers[teacher_id]=teacher # 선생님 dictionary에 선생님 저장
        self.rooms.append(new_room)
        new_room.add(teacher)
        
        print(teacher_id, 'connected')
        print(new_room.teacher_id,'에 접속한 인원 :',new_room)

        # if log_sw:
        #     msg=str(datetime.now())+' '+teacher_id+' connected\n'
        #     save_log(msg)
        #     msg=str(datetime.now())+' '+new_room.teacher_id+' 에 접속한 인원 : ' +new_room.str()+'\n'
        #     save_log(msg)
        
        teacher.run()


    def run(self):
        self.open()
        while True:
            try:
                c_soc, addr = self.server_soc.accept()
            except:
                continue
            print(addr)

            data = c_soc.recv(1024)
            get_data = data.decode()
            get_data = get_data[:-1]  # 뒤의 ┯ 삭제

            if get_data[:8] == 'teacher:':
                self.make_teacher(get_data, c_soc)

            elif get_data[:8] == 'student:':
                result = self.make_student(get_data, c_soc)
                if result == False:
                    try:
                        c_soc.sendall('not exist teacher┯'.encode(encoding='utf-8')) # cli에서 재접속하게 만들어야함
                    except:
                        pass

            else:
                print('client input wrong sentence')
                # if log_sw:
                #     msg=str(datetime.now())+' client input wrong sentence\n'
                #     save_log(msg)
                try:
                    c_soc.sendall('wrong sentence┯'.encode(encoding='utf-8'))  # cli에서 재접속하게 만들어야함
                except:
                    pass


server = ServerMain()
server.run()