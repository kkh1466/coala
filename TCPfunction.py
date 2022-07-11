import os
import pymysql
from datetime import datetime
import threading

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
