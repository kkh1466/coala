import pymysql
import fastapi
import redis
import datetime
from typing import Optional
from pydantic import BaseModel


redis_host = "13.125.180.127"
redis_port = 6379
redis_password = "redispass"

app = fastapi.FastAPI()
rds = redis.Redis(host=redis_host, port=redis_port, db=0, password=redis_password)



# GET http://localhost:8000/
# >> {"message": "Hello, World!"}
@app.get("/")
async def root():
    
    return {"message": "Hello, World!"}


# GET http://localhost:8000/ping
# >> "pong"
@app.get("/ping")
async def ping_pong():
    return "pong"
  

# GET http://localhost:8000/v1/redis/?key=sonsam
# >> "online"
@app.get("/v1/redis/")
async def redis_get(key: str = ""):
    res = rds.get(key)
    return res

@app.get("/key_check")
async def key_check():
    a=[]
    for key in rds.scan_iter(match='*', count=100):
        a.append(key)
    return a

@app.get("/login_check/")
async def login_check(login_text: str = ""):
    conn = pymysql.connect(host='dev-db.coala.services', user='coalaroot', password='coaladbpass', db='CoalaService', charset='utf8') 
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    sql = "select * from teacher_copy where t_name=(%s)" 
    cursor.execute(sql,login_text) 
    rs = cursor.fetchone()
    cursor.close()
    return rs['Login_check']


# redis에 등록시
# 선생님이 학생에게 보낼 때 키 값
# problem_table_teacher:{선생님아이디}♬{학생아이디}
# 학생이 선생님에게 보낼 때 키 값
# problem_table_student:{선생님아이디}♬{학생아이디}

# value 값은
# 선생님이 학생에게 보낼 때
# 1. send -> send♬{문제번호}♬{content_url}
# 2. correct -> correct♬{문제번호}♬{점수}
# 3. incorrect -> incorrect♬{문제번호}
# 4. feedback -> feedback♬{문제번호}♬{코드} -> 코드 수정 필요
# 5. retry -> retry♬{문제번호}

# 학생이 선생님에게 보낼 때
# 1. send -> send♬{문제번호}♬{코드} -> 코드 수정 필요

@app.get("/problems")
async def problem_send(teacher_id: Optional[str] = None,
                       student_id: Optional[str] = None,
                       problem_num: Optional[int] = None,
                       message: Optional[str] = None,
                       code: Optional[str] = None):
    coala_db = pymysql.connect(host='dev-db.coala.services', user='coalaroot', password='coaladbpass', db='CoalaService', charset='utf8')
    cursor = coala_db.cursor(pymysql.cursors.DictCursor)
    try:
        if teacher_id == None or student_id == None or problem_num == None or message == None:
            raise Exception('Essential information is not defined')
    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg

    try:
        # 선생님이 학생에게 문제를 보낼 때
        # value -> send♬{문제번호}♬{content_url}
        if message == 'teacher_send':
            sql = "select * from problem where number=(%s)"
            cursor.execute(sql, (problem_num,))
            problem_info = cursor.fetchone()
            content = problem_info["content"]

            key = "problem_table_teacher:" + teacher_id + "♬" + student_id
            value = "teacher_send♬" + str(problem_num) + "♬" + content
            result = rds.set(key, value, datetime.timedelta(seconds=17200))
            return result
        # 선생님이 학생에게 문제를 보낼 때
        # value -> correct♬{문제번호}♬{점수}
        elif message == 'correct':
            sql = "select * from problem where number=(%s)"
            cursor.execute(sql, (problem_num,))
            problem_info = cursor.fetchone()
            score = problem_info["score"]
            key = "problem_table_teacher:" + teacher_id + "♬" + student_id
            value = "correct♬" + str(problem_num) + "♬" + str(score)
            result = rds.set(key, value, datetime.timedelta(seconds=7200))
            return result

        # 선생님이 학생에게 문제를 보낼 때
        # value -> incorrect♬{문제번호}
        elif message == 'incorrect':
            key = "problem_table_teacher:" + teacher_id + "♬" + student_id
            value = "incorrect♬" + str(problem_num)
            result = rds.set(key, value, datetime.timedelta(seconds=7200))
            return result
        # 선생님이 학생에게 문제를 보낼 때
        # value -> retry♬{문제번호}
        elif message == 'retry':
            key = "problem_table_teacher:" + teacher_id + "♬" + student_id
            value = "retry♬" + str(problem_num)
            result = rds.set(key, value, datetime.timedelta(seconds=7200))
            return result

        # 잘못된 메세지를 날렸을 때 에러 발생
        else:
            raise Exception('unknown message')

    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg


# 학생이 자신에게 온  문제를 가져오고, redis에서 삭제시키는 api
@app.get("/problem-get-and-delete-student")
async def problem_get_and_delete_student(teacher_id: Optional[str] = None,
                                         student_id: Optional[str] = None):
    try:
        if teacher_id == None or student_id == None:
            raise Exception('Essential information is not defined')
    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg

    try:
        key = "problem_table_teacher:" + teacher_id + "♬" + student_id
        result = rds.get(key)
        rds.delete(key)
        return result
    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg


# 선생님이 redis를 통해 자신에게 온  문제를 가져오고, redis에서 삭제시키는 api
# 여러명의 정보가 한번에 올 수 있음(학생 id를 키값으로 가지도록 딕셔너리 형태로 받음)
@app.get("/problem-get-and-delete-teacher")
async def problem_get_and_delete_teacher(teacher_id: Optional[str] = None,):
    try:
        if teacher_id == None:
            raise Exception('Essential information is not defined')
    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg
    try:
        dic = {}
        for key in rds.scan_iter(match='problem_table_student:' + teacher_id + '♬*', count=100):
            result = rds.get(key)
            rds.delete(key)
            key = str(key, 'utf-8')
            student_list = key.split("♬")
            dic[student_list[1]] = result
        return dic

    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg
        
# 실제로 사용하지 않는 내부 테스트용 api
# redis에 등록되어 있는 모든 key와 value값 확인
@app.get("/get-all-redis")
async def get_all_redis():
    try:
        redis_dic={}
        for key in rds.scan_iter(match='*', count=300):
            result=rds.get(key)        
        return result
    except Exception as e:
        error_msg="Error:"+str(e)
        return error_msg


# redis에 등록되어 있는 problem_table 키들을 확인
# 실제로 사용하지 않는 내부 테스트용 api
@app.get("/get-all-problem-redis")
async def get_all_problem_redis():
    try:
        pro_dic = {}
        for key in rds.scan_iter(match='problem_table*', count=200):
            result = rds.get(key)
            pro_dic[key] = result
        return pro_dic
    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg
        
# redis에 원하는 key를 삭제하는 API
# 정상삭제시 1반환
# version 삭제용으로 자주 사용될 듯
@app.get("/delete-redis/{key}")
async def delete_redis(key:str):
    try:
        result=rds.delete(key)
        return result
    except Exception as e:
        error_msg="Error:"+str(e)
        return error_msg


# redis에 원하는 key, value 를 등록하는 API
# 정상등록 시 true 반환
# version 등록용으로 자주 사용될 듯
# 버전은 key 값이 version, value 값이 현재버전 으로 함  ex)version:0329
@app.get("/resist-redis/{key}/{value}")
async def resist_redis(key:str, value:str):
    try:
        result=rds.set(key,value)
        return result
    
    except Exception as e:
        error_msg="Error:"+str(e)
        return error_msg  

# 버전 체크용 API
# 현재 버전(value)를 반환
@app.get("/version-check")
async def version_check():
    try:
        value=rds.get('version')
        return value
    except Exception as e:
        error_msg="Error:"+str(e)
        return error_msg
        
# redis에 원하는 key, value 를 등록하는 API
# 정상등록 시 true 반환
# 이전 사
# 버전은 key 값이 version, value 값이 현재버전 으로 함  ex)version:0329
@app.get("/resist-redis-short/{key}/{value}")
async def resist_redis_short(key:str, value:str):
    try:
        result=rds.set(key,value,datetime.timedelta(seconds=10))
        return result
    
    except Exception as e:
        error_msg="Error:"+str(e)
        return error_msg   

# valuecheck_short
# value를 반환 후 삭제
@app.get("/redis-check-short/{key}")
async def redis_check_short(key:str):
    try:
        value=rds.get(key)
        result=rds.delete(key)
        return value
    except Exception as e:
        error_msg="Error:"+str(e)
        return error_msg   
        
# valuecheck
# value를반환
@app.get("/redis-check/{key}")
async def redis_check(key:str):
    try:
        value=rds.get(key)
        return value
    except Exception as e:
        error_msg="Error:"+str(e)
        return error_msg  
        
# 선생님이 로그인정보를 redis에 남기는 API
# 정상등록시 true 반환
@app.get("/teacher-redis-Login")
async def teacher_redis_Login(teacher_id: Optional[str] = None):
    try:
        if teacher_id == None:
            raise Exception('Essential information is not defined')
    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg

    try:
        key = "teacher_Login_table:"+ teacher_id
        value = "Login"
        result = rds.set(key, value, datetime.timedelta(seconds=10))
        return result

    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg



# 선생님의 로그인정보를 redis에서 확인하는 API
# 로그인이 되어 있다면 1 반환
# 로그인이 안되어 있다면 0 반환
@app.get("/teacher-redis-Login-check")
async def teacher_redis_Login_check(teacher_id: Optional[str] = None):
    try:
        if teacher_id == None:
            raise Exception('Essential information is not defined')
    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg

    try:
        key = "teacher_Login_table:"+ teacher_id
        result=rds.exists(key)
        return result

    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg



# 접속해있는 모든 선생님 아이디 리스트를 반환하는 API
@app.get("/get-all-redis-teacher")
async def get_all_redis_teacher():
    try:
        teacher_list=[]
        for key in rds.scan_iter(match='teacher_Login_table:*', count=200):
            teacher_list.append(key[20:])
        return teacher_list
    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg
    



# 학생이 로그인정보를 redis에 남기는 API
# 정상등록시 true 반환
@app.get("/student-redis-Login")
async def student_redis_Login(teacher_id: Optional[str] = None,
                              student_id: Optional[str] = None):
    try:
        if teacher_id == None or student_id == None:
            raise Exception('Essential information is not defined')
    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg

    try:
        key = "student_Login_table:" + student_id
        value = teacher_id
        result = rds.set(key, value, datetime.timedelta(seconds=10))
        return result

    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg



# 학생의 로그인정보를 redis에서 확인하는 API
# 선생님의 아이디를 반환
@app.get("/student-redis-Login-check")
async def student_redis_Login_check(student_id: Optional[str] = None):
    try:
        if student_id == None:
            raise Exception('Essential information is not defined')
    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg

    try:
        key = "student_Login_table:"+ student_id
        result=rds.get(key)
        return result

    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg




# 접속한 모든 학생들을 확인해서 반환하는 API
@app.get("/get-all-redis-student")
async def get_all_redis_student():
    try:
        student_dic={}
        for key in rds.scan_iter(match='student_Login_table:*', count=200):
            student_dic[key[20:]]=rds.get(key)
        return student_dic
    except Exception as e:
        error_msg = "Error:" + str(e)
        return error_msg


# 로그인시 DB에 로그인 상태로 바꾸는 API
# 정상 등록시 "udtate_Login_END" 반환
@app.get("/DB-Login")
async def read_item(User_id: Optional[str] = None,
                    value: Optional[str] = None,
                    subject: Optional[str] = None):

    # 입력정보가 없을 시 에러 발생시킴
    try:
        if User_id == None or value == None:
            raise Exception('Essential information is not defined')
    except Exception as e:
        error_msg = "Error1:" + str(e)
        return error_msg
    
    try:
        coala_db = pymysql.connect(host='dev-db.coala.services', user='coalaroot', password='coaladbpass', db='CoalaService', charset='utf8')
        cursor = coala_db.cursor(pymysql.cursors.DictCursor)
        if(value=='std'):
            sql = "update std set Login_state = 'Login' where id= (%s)"
            cursor.execute(sql,(User_id,))
        else:
            sql = "update teacher set Login_state = 'Login' where id= (%s) and subject=(%s)"
            cursor.execute(sql,(User_id,subject,))
        coala_db.commit()
        result_msg = "udtate_Login_END"
        return result_msg
    
    except Exception as e:
        error_msg = "Error2:" + str(e)
        return error_msg

    finally:
        cursor.close()


    

# 로그아웃시 DB에 로그아웃 상태로 바꾸는 API
# 정상등록시 "udtate_Logout_END"
@app.get("/DB-Logout")
async def Delete_item(User_id: Optional[str] = None,
                      value: Optional[str] = None):

    # 입력정보가 없을 시 에러 발생시킴
    try:
        
        if User_id == None or value == None:
            raise Exception('Essential information is not defined')
    except Exception as e:
        error_msg = "Error1:" + str(e)
        return error_msg

    try:
        coala_db = pymysql.connect(host='dev-db.coala.services', user='coalaroot', password='coaladbpass', db='CoalaService', charset='utf8')
        cursor = coala_db.cursor(pymysql.cursors.DictCursor)
        if(value=='std'):
            sql = "update std set Login_state = 'Logout' where id= (%s)"
        else:
            sql = "update teacher set Login_state = 'Logout' where id= (%s)"
        cursor.execute(sql,(User_id,)) 
        coala_db.commit()
        result_msg = "udtate_Logout_END"
        return result_msg
    
    except Exception as e:
        error_msg = "Error2:" + str(e)
        return error_msg

    finally:
        cursor.close()
