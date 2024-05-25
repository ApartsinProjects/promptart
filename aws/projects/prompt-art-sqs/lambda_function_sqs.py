import json,boto3
from core.paDB import Pdb
from core.paDispatch import  DispatchSrv
from core.paPublish import PublishMng
import os

qname=os.getenv('qname')
#qname="prompt-art-prod"

#event handlers
def applyTransformEvt(event,pdb): return DispatchSrv(pdb,qname).handle(event['task_id'],event['context'])
def genFeedEvt(event,pdb): return DispatchSrv(pdb,qname).handle(event['task_id'],event['context'])
def processFeedEvt(event,pdb): return DispatchSrv(pdb,qname).handle(event['task_id'],event['context'])
def publishDoc(event,pdb): return PublishMng(pdb,qname).publishDoc(event['context'])
def publishAll(event,pdb): return PublishMng(pdb,qname).publishAll()


#SQS dispatch map
evt_map={"applyTransformer":applyTransformEvt,"genFeed":genFeedEvt,"genAndPayFeed":genFeedEvt,"procFeed":processFeedEvt,"publishDoc":publishDoc,"publishAll":publishAll}

def sqs_handler(event,context):
    print(f"processing sqs messsges {event} num messages {len(event['Records'])}")
    for msg in event['Records']:
        event=msg['body'] if isinstance(msg['body'],dict) else json.loads(msg['body']) #allow debug
        res=evt_map[event['method']](event,Pdb())
    return {'statusCode': 200}

def lambda_handler(event, context):
    return sqs_handler(event,context)

