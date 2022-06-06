import pymysql
import pandas as pd
import numpy as np


coala_db = pymysql.connect(host='dev-db.coala.services',
                           user='coalaroot',
                           password='coaladbpass',
                           db='CoalaService',
                           charset='utf8')

cursor = coala_db.cursor(pymysql.cursors.DictCursor)


sql = "select * from teacher"
cursor.execute(sql)
teacher_info = cursor.fetchall()
t=pd.DataFrame(teacher_info)


def get_subject(id:str):
    bool_list=[t['id']==id]
    bool_list=np.array(bool_list).reshape(-1)
    x=np.arange(len(bool_list))
    x=x*bool_list
    num=np.argmax(x)

    print("이름 :", t.loc[num]['t_name'])
    print(id)
    print("비밀번호 :", t.loc[num]['pw'])
    print('과목 개수 :', len((bool_list * t['subject']).unique()) )
    print((bool_list * t['subject']).unique())

for i in t['id'].unique():
    get_subject(i)
    input()

