import uuid,psycopg2
import psycopg2.extras
import json
from datetime import datetime
import boto3
import os

def qstr(x): return f"'{json.dumps(x) if isinstance(x,dict) else str(x)}'"
def drop_none(obj): return {k:v for k,v in obj.items() if v is not None}

class Pdb:
    def __init__(self):
        #dbconnection=json.loads(json.loads(boto3.client('secretsmanager').get_secret_value(**{'SecretId': os.getenv('db_connection')})['SecretString'])["db_connection"])
        #self.con=psycopg2.connect(f"dbname='{dbconnection['dbname']}' user='{dbconnection['user']}' host='{dbconnection['host']}' password='{dbconnection['password']}'")
        self.con=psycopg2.connect("dbname='promptart' user='sasha' host='promtart-free.cuqgeumuhzr3.us-east-1.rds.amazonaws.com' password='promptart'")
        self.cur=self.con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        
    def _stmt(self,sql_str): 
        print(f"executing sql:{sql_str}")
        self.cur.execute(sql_str)
        return self
        
    def selectObj(self,table,uid,key='uid'): 
        res=self._stmt(f"select * from {table} where {key}='{uid}'").cur.fetchone()
        if res:res['datecreated']=str(res['datecreated'])
        return res
        
    def deleteObj(self,table,uid,key='uid'): 
        self._stmt(f"delete from {table} where {key}='{uid}'").con.commit()
        return uid
        
    def insertObj(self,table,obj,key="uid"):
        return self.insert(table,{**drop_none(obj),key:str(uuid.uuid4()),'datecreated':str(datetime.utcnow())})
        
    def updateObj(self,table, uid, obj ,key='uid'):
        obj=drop_none(obj)
        self._stmt(f"update {table} set {','.join([k+'='+qstr(v) for k,v in obj.items()])} where {key}={qstr(uid)}").con.commit()
        return self.selectObj(table,uid,key)
        
    def findObjs(self,table,where_clause):
        return self._stmt(f"select uid from {table} where {where_clause}").cur.fetchall()
        
    def insert(self,table,obj):#insert row
        self._stmt(f"insert into {table} ({','.join(obj.keys())})  values ( {','.join([qstr(x) for x in obj.values()])})").con.commit()
        return obj
        
    def findRows(self,table,filt_dict):
        return self._stmt(f"select * from {table} where {self.whereFilt(filt_dict)}").cur.fetchall()
        
    def whereFilt(self,obj): return "AND".join([f" {k}='{v}'" for k,v in obj.items()])
    
    