import boto3,json
from core.paDB import Pdb
from utils.paConnector import FbConnector
from datetime import datetime

conn_map={"fb": FbConnector}
format2func_map={"ssText": "post_text"}

class PublishMng:
    def __init__(self,pdb,qname):
        self.pdb=pdb
        self.qname=qname
        self.sqs=boto3.client('sqs')
        
    def publishDoc(self,did):
        doc=self.pdb.selectObj('docs',did)
        pi=self.pdb.selectObj('nodes',doc['feed'])
        self.publish(doc['content'],pi['publishinfo'])
        return self.pdb.updateObj('docs',did,{'datepublished':datetime.utcnow()})
        
    def publish(self,content,pi):
        for k,v in pi.items(): 
            try: getattr(conn_map[k], format2func_map[v['format']])(content[v['format']])
            except: continue
        #content is json with all fields
        #pi is json with all needed info (format not yet defiend)
        #call here fbConnector and twitter
        
    def queueTask(self,did):
        return self.sqs.send_message(QueueUrl=self.qname,MessageBody=json.dumps({"context":did,"method":'publishDoc'}))
        
    def publishAll(self):
        docs=self.yetUnpublished()
        for d in docs: self.queueTask(d['uid'])
        return self
        
    def yetUnpublished(self):
        res=self.pdb._stmt("select docs.uid from docs left join nodes on docs.feed=nodes.uid  where docs.datepublished is NULL and nodes.publishinfo is not NULL")
        return res.cur.fetchall()
        
    