from core.paTransform import Transformers
from datetime import datetime,date
from core.paDispatch import DispatchSrv
from core.paUsers import UserMng
import json

min_attempt_sec=1

def daystart(): return datetime.utcnow().date()

class  FeedMng:
    def __init__(self,pdb,qname=None): 
        self.pdb=pdb
        self.qname=qname
        self.TR=Transformers(self.pdb)
    def secsSinceAttempt(self,fid): return (self.pdb.selectObj('nodes',fid)['lastattempt']-datetime.utcnow()).seconds
    def update(self, fid, obj): return self.pdb.updateObj('nodes',fid, obj)
    def enumerate(self,query=None): return self.pdb.findObjs('nodes',query)
    
    def generateAsync(self,fid,user,num_docs,since,freq=min_attempt_sec):
        return DispatchSrv(self.pdb,self.qname).startGeneration(fid,user,num_docs,since,freq) if self.secsSinceAttempt(fid)>freq else None
    
    def get(self,fid): 
        obj=self.pdb.selectObj('nodes',fid)
        return {**obj,'transformer':self.TR.get(obj['transformer'])['cfg']} if obj else {}
        
    def delete(self,fid):
        childs=self.pdb.findObjs('nodes', f"source='{fid}'")
        if not childs or len(childs)==0:
            self.pdb.deleteObj('nodes',fid)
        else:
            self.update(fid, {'visibility':'deleted'})
        return fid
        
    def attach(self,obj):
        obj={"source":None,"fees":{'prompt_fees':{},'process_fees':{}},**obj}
        if isinstance(obj['transformer'], dict): 
            print(f"creating companion transformer from {obj['transformer']}")
            obj['transformer']=self.TR.create({"cfg":obj['transformer'],"owner":obj["owner"],"name":f"companion for {obj['name']}"})["uid"]
        obj={**obj,"lastattempt":str(datetime.min),"lastgen":str(datetime.min)}
        return self.pdb.insertObj("nodes",{**obj,"fees":self.feedFees(obj)})
        
    def feedFees(self,obj): #src+node transformer
        transform_fees=self.TR.get(obj['transformer'])['fees'] if obj.get("nodetype")!="splitter" else {'prompt_fees':{},'process_fees':{}}
        src_fees=self.get(obj['source'])['fees'] if obj['source'] else {"prompt_fees":{},'process_fees':{}}
        return Transformers._addFees(transform_fees,src_fees)
        
    def userDocsSince(self, fid,uid, since):
        st=f"select docs.uid FROM docs JOIN rights ON docs.uid = rights.docid WHERE rights.userid = '{uid}' AND docs.datecreated > '{since}' AND docs.feed = '{fid}'"
        return self.pdb._stmt(st).cur.fetchall()
        
    def getTaskStatus(self,gid):
        res=self.pdb.selectObj('tasks',uid=gid)
        return {"uid":gid, "status":"ready"} if not res else res 
        
    def generateAll(self):
        users=self.pdb.findObjs("users","subscription is not NULL")
        usrmng=UserMng(self.pdb)
        if users:
            for u in users:
                print(f"generateAll user {u}")
                for k,v in usrmng.get(u['uid'])['subscription'].items(): self.generateAsync(k,u['uid'],v['num_docs'], daystart(),-1)