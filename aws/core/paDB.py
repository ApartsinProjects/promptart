import uuid,psycopg2
import psycopg2.extras
import json
from datetime import datetime
import os

def qstr(x): return f"'{json.dumps(x) if isinstance(x,dict) else str(x)}'"
def drop_none(obj): return {k:v for k,v in obj.items() if v is not None}


def _db_connection_string():
    # Preferred: explicit DSN
    dsn = os.getenv("PA_DB_DSN") or os.getenv("DATABASE_URL")
    if dsn:
        return dsn

    # Fallback: PG* environment variables
    host = os.getenv("PGHOST")
    dbname = os.getenv("PGDATABASE")
    user = os.getenv("PGUSER")
    password = os.getenv("PGPASSWORD")
    port = os.getenv("PGPORT", "5432")
    if host and dbname and user and password:
        return f"dbname='{dbname}' user='{user}' host='{host}' password='{password}' port='{port}'"

    raise RuntimeError(
        "Database credentials are not configured. "
        "Set PA_DB_DSN (or DATABASE_URL), or PGHOST/PGDATABASE/PGUSER/PGPASSWORD."
    )

class Pdb:
    def __init__(self):
        self.con=psycopg2.connect(_db_connection_string())
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
    
    
