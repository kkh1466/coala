import threading
import socket
import time
from datetime import datetime
import os
import pymysql

log_sw = True
lock=threading.Lock()

def preventDuplication(filename) -> bool:
    # print("preventDuplication 함수 진입")
    path = f'src/{filename}'

    if os.path.isfile(path):
        print('이미 존재하는 파일')
        return True
    else:
        return False


def insertCode(filename, memo):
    '''
    DB에 (저장시간, 학생ID, 문제번호, 파일경로) 를 insert함
    :param filename: 파일 경로 (상대경로)
    :return:
    '''

    # print("insertCode 함수 진입")
    _name, _ext = os.path.splitext(filename)
    filename_splited = _name.split('-')

    try:
        print("DB에 저장하는 중")
        # print(1)
        coala_db = pymysql.connect(
            host='ls-0003016e97366f8af5757aae3a927c0470d990b2.crqrymk8yrjv.ap-northeast-2.rds.amazonaws.com',
            user='dbmasteruser',
            password='(Lwx8|9H5AXfSZ%pH5#RkIcs$W=x1zNo',
            db='CoalaService',
            charset='utf8'
        )
        # print(2)
        cursor = coala_db.cursor(pymysql.cursors.DictCursor)
        # print(3)
        sql = 'INSERT INTO code_history_student (processing_time, student_id, problem_number, submit_code, memo) VALUES (%s, %s, %s, %s, %s)'
        # print(4)
        cursor.execute(sql, (str(datetime.now()), filename_splited[0], filename_splited[1], './' + filename, memo))
        # print(5)
        coala_db.commit()
        # print(6)
        # print("DB에 올리는 내용: ", filename_splited[0], filename_splited[1], './' + filename, memo)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()
        print("insertCode(DB 올림) 함수 종료")


def insertCode_teacher(filename, stdid, compcnt, processingstatus):
    '''
        DB에 (저장시간, 학생ID, 문제번호, 파일경로) 를 insert함
        :param filename: 파일 경로 (상대경로)
        :param stdid: 학생ID
        :param compcnt: 컴파일 횟수
        :param processingstatus: 처리 상태
        :return:
    '''

    # print("insertCode 함수 진입")
    _name, _ext = os.path.splitext(filename)
    filename_splited = _name.split('-')
    # print(filename_splited)

    try:
        print("DB에 저장하는 중")
        # print(1)
        coala_db = pymysql.connect(
            host='ls-0003016e97366f8af5757aae3a927c0470d990b2.crqrymk8yrjv.ap-northeast-2.rds.amazonaws.com',
            user='dbmasteruser',
            password='(Lwx8|9H5AXfSZ%pH5#RkIcs$W=x1zNo',
            db='CoalaService',
            charset='utf8'
        )
        # print(2)
        cursor = coala_db.cursor(pymysql.cursors.DictCursor)
        # print(3)
        sql = 'INSERT INTO code_history_teacher (teacher_id, processing_time, problem_num, student_id, compile_count, submit_code, processing_status) VALUES (%s, %s, %s, %s, %s, %s, %s)'
        # print(4)

        cursor.execute(sql, (
            filename_splited[0][7:], str(datetime.now()), filename_splited[1], stdid, compcnt, './' + filename,
            processingstatus))
        # print(5)
        coala_db.commit()
        # print(6)
        # print("DB에 올리는 내용: ", filename_splited[0], str(datetime.now()), filename_splited[1], stdid, compcnt,
        #      './' + filename, processingstatus)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()
        print("insertCode(DB 올림) 함수 종료")


def getFileFromServer(filename, memo) -> str:
    '''
    파일을 수신받아서 해당 디렉토리에 저장함
    :param filename: 파일 경로 (상대경로)
    :param memo: 메모
    :return: new filename
    '''
    # print("getFileFromServer 함수 진입")
    data_transferred = 0

    # 중복 파일이 있는지 확인
    # 중복 파일이 있으면 카운트업
    if preventDuplication(filename):
        print("중복 파일 있음")
        count = 0
        path = 'src'

        try:
            file_list = os.listdir(path)
            # print(os.listdir(path))

            _name, _ext = os.path.splitext(filename)  # 확장자 분리
            file_list_log = [file for file in file_list if file.startswith(_name)]

            count = len(file_list_log)

            filename = f'{_name}-{count}{_ext}'

        except Exception as e:
            print(e)

    # 저장시간, 학생ID, 문제번호, 파일경로
    # DB에 저장
    insertCode(filename, memo)

    return filename


def getFileFromServer_teacher(filename, stdid, compcnt, processingstatus) -> str:
    '''
    파일을 수신받아서 해당 디렉토리에 저장함
    :param filename: 파일 경로 (상대경로)
    :param stdid: 학생id
    :param compcnt: 컴파일 횟수
    :param processingstatus: 처리 상태
    :return: new filename
    '''
    # print("getFileFromServer 함수 진입")
    data_transferred = 0

    # DB에 저장
    insertCode_teacher(filename, stdid, compcnt, processingstatus)

    return filename


def save_log(log_msg, lock):
    try:
        log_msg = str(datetime.now())+' '+log_msg+'\n'
        print(log_msg)
        lock.acquire()
        log = open('log.txt', 'a', encoding='utf-8')
        log.write(log_msg)
        lock.release()
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

        if log_sw:
            msg=self.teacher_id+' 에 남은 인원 : '+ self.str()
            t=threading.Thread(target=save_log, args=(msg, lock))
            t.start()

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
        for i, id in enumerate(self.clients):
            if i != 0:
                c += str(id.id) + ','
        return c


class Client:
    def __init__(self, id: str, sock: socket.socket, room: Room):
        self.id = id
        self.sock = sock
        self.room = room
        self.ping_sw = True
        self.pong_time = time.time()

    def send(self, msg):
        try:
            self.sock.sendall(msg.encode(encoding='utf-8'))
        except:
            if log_sw:
                msg="send error"
                t=threading.Thread(target=save_log, args=(msg, lock))
                t.start()

    def ping(self):
        try:
            while True:
                if self.ping_sw == False:
                    break
                self.sock.sendall('ping┯'.encode(encoding='utf-8'))
                time.sleep(3)
        except Exception:
            if self.ping_sw == True:
                self.disconnect()
                if log_sw:
                    msg=self.id+' ping_disconnect'
                    t=threading.Thread(target=save_log, args=(msg, lock))
                    t.start()
    
    def pong(self):
        pong_time_list=[]
        while True:
            now = time.time()

            if len(pong_time_list)<=5:
                pong_time_list.append(self.pong_time)
            else:
                del pong_time_list[0]
                pong_time_list.append(self.pong_time)

            if now - self.pong_time >= 5:
                if self.ping_sw == True:
                    self.disconnect()

                    pong_msg=''
                    for t in pong_time_list:
                        pong_msg+=str(t)+' '

                    if log_sw:
                        msg=self.id+' pong_disconnect\n최근 5개 시간 : '+pong_msg+'\n끊어진 시간 : '+str(time.time())
                        t=threading.Thread(target=save_log, args=(msg, lock))
                        t.start()
            time.sleep(1)


    def run(self):
        t1 = threading.Thread(target=self.receive, args=())
        t2 = threading.Thread(target=self.ping, args=())
        t3 = threading.Thread(target=self.pong, args=())
        t1.daemon = True
        t2.daemon = True
        t3.daemon = True
        t1.start()
        t2.start()
        t3.start()


class Student(Client):
    def __init__(self, id: str, sock: socket.socket, room: Room):
        self.id = id
        self.sock = sock
        self.room = room
        self.ping_sw = True
        self.pong_time = time.time()

    def disconnect(self):
        self.ping_sw = False
        msg = 'disconnect┴' + self.id + '┯'
        self.room.clients[0].send(msg)
        self.sock.close()
        self.room.remove(self)
        del server.students[self.id]

        if log_sw:
            msg='학생 '+self.id+' 가 종료하였습니다.'
            t=threading.Thread(target=save_log, args=(msg, lock))
            t.start()


    # 선생님의 종료로 인한 강제종료
    def t_disconnect(self):
        self.ping_sw = False
        self.sock.close()
        self.room.remove(self)
        del server.students[self.id]  # 원본 소켓 삭제

        if log_sw:
            msg='학생 '+self.id+' 가 종료하였습니다.'
            t=threading.Thread(target=save_log, args=(msg, lock))
            t.start()

    def receive(self):
        try:
            while True:
                msg = ''
                while msg[-1:] != '┯':
                    message = self.sock.recv(1024)
                    message = message.decode()
                    msg += message
                msg = msg[:-1]
                mlist=msg.split('┯')

                sw=False  # break를 위한 sw변수
                for msg in mlist:
                    if msg == 'disconnect':
                        if log_sw:
                            msg='client가 disconnect 메세지를 보내서 정상종료'
                            t=threading.Thread(target=save_log, args=(msg, lock))
                            t.start()
                        sw=True
                        break
                    elif msg == 'pong':
                        self.pong_time = time.time()
                        continue
                    elif msg[:5] == 'file┴':  # 파일 저장
                        print('[옳음] 학생 파일 저장하는 if문 들어옴.')
                        # file┴학생id-문제번호.[확장자]$파일크기$메모$
                        self.filename = msg
                        # print(self.filename)
                        t = threading.Thread(target=self.file_save, args=())
                        t.start()
                        t.join()
                        continue
                    elif msg[:12] == 'codereceive┴':  # 서버에서 저장된 코드 다운로드
                        print('[옳음] 학생 파일 불러오는 if문 들어옴.')
                        # codereceive┴파일경로
                        self.fileroot = msg
                        # print(self.fileroot)
                        t = threading.Thread(target=self.codereceive, args=())
                        t.start()
                        t.join()
                    else:  # 선생님에게 전달
                        #print('[잘못] 선생님에게 전달하는 if문 들어옴')
                        #print('[잘못] : ', msg)
                        msg += '┯'
                        self.room.clients[0].send(msg)

                    print(msg)

                if sw:
                    break

        except Exception as e:
            if self.ping_sw == True:
                if log_sw:
                    msg='receive 함수의 에러로 인한 종료'+' error:'+str(e)
                    t=threading.Thread(target=save_log, args=(msg, lock))
                    t.start()
                self.disconnect()

        if self.ping_sw == True:
            self.disconnect()

    def file_save(self):
        try:
            print("file save 함수 진입")
            data_transferred = 0

            # file┴학생id-문제번호.[확장자]$파일크기$메모$
            self.filename, filesize, memo, _ = self.filename.split('$')
            protocol, self.filename = self.filename.split('┴')  # 프로토콜과 파일이름 분리

            if protocol == 'file':
                print("프로토콜 확인, ♂ok♀보냄")
                self.sock.send("♂ok♀".encode())  # 파일 받기 준비 완료

                self.filename = getFileFromServer(self.filename, memo)  # 파일 수신

                data = self.sock.recv(1024)
                print("받은 데이터", data)
                data_transferred += len(data)
                # 클라우드 컴퓨터에 파일 저장
                with open('src/' + self.filename, 'wb') as f:
                    try:
                        f.write(data)
                        while data_transferred < int(filesize):
                            data = self.sock.recv(1024)
                            data_transferred += len(data)
                            f.write(data)
                            # data = data.decode('utf-8')

                    except Exception as e:
                        print(e)

                print('파일 [%s] 전송 종료. 전송량 [%d]' % (self.filename, data_transferred))
                return True

        except ConnectionResetError as e:
            print('Disconnected from client error:', e)
            return False

    def codereceive(self):
        try:
            print("codereceive 함수 진입")

            data = ''
            # codereceive┴파일경로$
            protocol, filename = self.fileroot.split('┴')
            filename = filename.split('$')[0]

            if protocol == 'codereceive':
                datatransfer = 0
                _name = filename[2:]
                filesize = str(os.path.getsize(f'src/{_name}'))

                s = f'codereceive┴{_name}╋{filesize}╋'

                with open('src/' + _name, 'r') as f:
                    try:
                        _data = f.read(1024)
                        while _data:
                            data += str(_data)
                            datatransfer += len(_data)
                            _data = f.read(1024)

                    except Exception as e:
                        print(e)

                s += data
                # s += '$'
                # print("encode", s.encode())
                self.sock.send(s.encode())
                # print("decode", s.encode().decode())

                print('파일 [%s] 전송 종료. 전송량 [%d]' % (_name, datatransfer))


            else:
                print('서버에서 준비 실패 : file로 프로토콜이 제대로 설정되어있는지 확인 필요')

        except Exception as e:
            print(e)
            return False


class Teacher(Client):
    def __init__(self, id: str, sock: socket.socket, room: Room):
        self.id = id
        self.sock = sock
        self.room = room
        self.ping_sw = True
        self.pong_time = time.time()

    def disconnect(self):
        self.ping_sw = False
        self.room.send('teacher_disconnect┯')  # 학생들에게 선생님이 종료되었다는 메세지를 날림
        for i in reversed(range(len(self.room.clients) - 1)):  # 학생들을 순차적으로 종료
            self.room.clients[i + 1].t_disconnect()
        time.sleep(1)
        self.sock.close()
        self.room.remove(self)
        server.rooms.remove(self.room)  # 방폭파
        del server.teachers[self.id]    # 원본 소켓 삭제

        if log_sw:
            msg='선생님 '+self.id+' 가 종료하였습니다.'
            t=threading.Thread(target=save_log, args=(msg, lock))
            t.start()

    def receive(self):
        try:
            while True:
                msg = ''
                while msg[-1:] != '┯':
                    message = self.sock.recv(1024)
                    message = message.decode()
                    msg += message
                msg = msg[:-1]
                mlist=msg.split('┯')

                sw=False # break를 위한 sw변수
                for msg in mlist:
                    if msg == 'disconnect':
                        if log_sw:
                            msg='client가 disconnect 메세지를 보내서 정상종료'
                            t=threading.Thread(target=save_log, args=(msg, lock))
                            t.start()
                        sw=True
                        break
                    elif msg == 'pong':
                        self.pong_time = time.time()
                        print('pong')
                        continue
                    elif msg == 'connect_student_list':
                        return_msg = 'connect_student_list┴' + self.room.str() + '┯'
                        self.send(return_msg)
                        continue
                    elif msg[:5] == 'file┴':  # 파일 저장
                        print('[옳음] 선생님 파일 저장하는 if문 들어옴')
                        self.filename = msg
                        # file┴teacher선생님id-문제번호.cpp$파일크기$학생id$컴파일횟수$processingstatus$
                        # print(self.filename)
                        t = threading.Thread(target=self.file_save, args=())
                        t.start()
                        t.join()
                    else:  # 학생에게 전달
                        if msg[:8] == 'student┴':  # 특정학생에게 전달
                            msg_list = msg.split('┴')
                            who = msg_list[1]
                            for student in self.room.clients:
                                if student.id == who:
                                    msg = msg_list[2] + '┯'
                                    student.send(msg)
                                    break
                        else:  # 모든 학생에게 전달
                            msg += '┯'
                            self.room.send(msg)
                    print(msg)

                if sw:
                    break

        except Exception as e:
            if self.ping_sw == True:
                if log_sw:
                    msg='receive 함수의 에러로 인한 종료'+' error:'+str(e)
                    t=threading.Thread(target=save_log, args=(msg, lock))
                    t.start()
                self.disconnect()

        if self.ping_sw == True:
            self.disconnect()

    def file_save(self):
        try:
            print("teacher file save 함수 진입")
            data_transferred = 0

            # file┴teacher선생님id-문제번호.cpp$파일크기$학생id$컴파일횟수$processingstatus$
            self.filename, filesize, stdid, compcnt, processingstatus, _ = self.filename.split('$')

            protocol, self.filename = self.filename.split(':')  # 프로토콜과 파일이름 분리
            if protocol == 'file':
                print("프로토콜 확인, ♂ok♀보냄")
                self.sock.send("♂ok♀".encode())  # 파일 받기 준비 완료

                print("getFileFromServer 함수 이제 진입할거임.")
                self.filename = getFileFromServer_teacher(self.filename, stdid, compcnt, processingstatus)  # 파일 수신
                print(self.filename)

                data = self.sock.recv(1024)
                data_transferred += len(data)
                # 클라우드 컴퓨터에 파일 저장
                with open('src/' + self.filename, 'wb') as f:
                    try:
                        f.write(data)
                        while data_transferred < int(filesize):
                            data = self.sock.recv(1024)
                            data_transferred += len(data)
                            f.write(data)
                            # data = data.decode('utf-8')


                    except Exception as e:
                        print(e)

                print('파일 [%s] 전송 종료. 전송량 [%d]' % (self.filename, data_transferred))
                return True

        except ConnectionResetError as e:
            print('Disconnected from client error:', e)
            return False


class ServerMain:
    ip = ''
    port = 15555

    def __init__(self):
        self.rooms = []  # server에 만들어진 모든방을 넣을 list
        self.teachers = {}  # server에 접속한 선생님들의 소켓과 id를 저장할 dic, {teachers_id:teacher객체}형태로 저장
        self.students = {}  # server에 접속한 학생들의 소켓과 id를 저장할 dic, 위와 같은 방식으로 저장
        self.server_soc = None

    def open(self):
        self.server_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_soc.bind((ServerMain.ip, ServerMain.port))
        self.server_soc.listen(10)

    def make_student(self, get_data, sock: socket.socket):
        data_list = get_data.split('┴')
        teacher_id = data_list[1]
        student_id = data_list[2]

        # 중복 접속시 기존 접속 해제
        # 딕셔너리 형태이기때문에 in연산자로 먼저 데이터 존재여부 확인(O(1)) 후, 반복문으로 재탐색
        if student_id in self.students:
            for student in self.students:
                if student_id == student:
                    self.students[student].send('disconnect┯')
                    self.students[student].disconnect()
                    break

        sw = True  # 성공적으로 방에 들어갔는지 확인하는 switch 변수
        for room in self.rooms:
            if room.teacher_id == teacher_id:
                student = Student(student_id, sock, room)

                self.students[student_id] = student  # 학생 dictionary에 정보 저장
                room.add(student)  # 방에 학생을 넣음

                msg = 'connect┴' + student_id + '┯'
                room.clients[0].send(msg)  # 선생님에게 학생 접속 메세지 전송

                student.run()
                student.send('connect complete┯')

                if log_sw:
                    msg=student_id+ ' connected in '+ room.teacher_id+'\n'+room.teacher_id+ ' 에 접속한 인원 : '+ room.str()
                    t=threading.Thread(target=save_log, args=(msg, lock))
                    t.start()

                sw = False

        if sw:  # 학생이 방에 들어가지 못했다면
            if log_sw:
                msg='not existed teacher_id\n'+'cli에게 받은 메세지 : '+get_data
                t=threading.Thread(target=save_log, args=(msg, lock))
                t.start()
            return False
        else:  # 학생이 방에 잘 들어갔다면
            return True

    def make_teacher(self, get_data, sock: socket.socket):
        data_list = get_data.split('┴')
        teacher_id = data_list[1]

        # 중복 접속시 기존 접속 해제
        if teacher_id in self.teachers:
            for room in self.rooms:
                if room.teacher_id == teacher_id:
                    room.clients[0].send('disconnect┯')
                    room.clients[0].disconnect()  # 선생님 diconnect
                    break

        new_room = Room(teacher_id)
        teacher = Teacher(teacher_id, sock, new_room)

        self.teachers[teacher_id] = teacher  # 선생님 dictionary에 선생님 저장
        self.rooms.append(new_room)
        new_room.add(teacher)
        teacher.send('connect complete┯')
        teacher.run()

        if log_sw:
            msg=teacher_id+' connected\n'+new_room.teacher_id+' 에 접속한 인원 : ' +new_room.str()
            t=threading.Thread(target=save_log, args=(msg, lock))
            t.start()


    def run(self):
        self.open()
        while True:
            try:
                c_soc, addr = self.server_soc.accept()
            except:
                if log_sw:
                    msg='accept중 error 발생'
                    t=threading.Thread(target=save_log, args=(msg, lock))
                    t.start()
                continue
            print(addr)

            try: 
                data = c_soc.recv(1024)
            except:
                if log_sw:
                    msg='mainsocket recv중 error 발생'
                    t=threading.Thread(target=save_log, args=(msg, lock))
                    t.start()
                continue
            get_data = data.decode()
            get_data = get_data[:-1]  # 뒤의 ┯ 삭제

            if get_data[:8] == 'teacher┴':
                self.make_teacher(get_data, c_soc)

            elif get_data[:8] == 'student┴':
                result = self.make_student(get_data, c_soc)
                if result == False:
                    try:
                        c_soc.sendall('not exist teacher┯'.encode(encoding='utf-8'))  # cli에서 재접속하게 만들어야함
                    except:
                        pass

            else:
                if log_sw:
                    msg='client input wrong sentence : '+get_data
                    t=threading.Thread(target=save_log, args=(msg, lock))
                    t.start()
                try:
                    c_soc.sendall('wrong sentence┯'.encode(encoding='utf-8'))  # cli에서 재접속하게 만들어야함
                    c_soc.close()
                except:
                    pass


server = ServerMain()
server.run()