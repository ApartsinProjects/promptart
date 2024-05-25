import json,boto3
from core.paDB import Pdb
from core.paGraph import FeedMng
import os

qname=os.getenv('qname')
#qname="prompt-art-prod"

def timeSubUpdate(event,pdb): return FeedMng(pdb,qname).generateAll()


#API call map
ops_map={"timeSubUpdate":timeSubUpdate}


def schedule_handler(event, context):
    print(f"processing eventbridge call {event}")
    try:
        #boto3.client('sqs').purge_queue(QueueUrl=qname) #debug
        print("not purging")
    except:
        print("purge in progress")
    op_name=event['requestContext']['operationName']
    if "body" in event:
        event['body']=json.loads(event['body']) if isinstance(event['body'],str) else event['body']
    res=ops_map[ op_name](event,Pdb())
    print(f"schedule handler returned {res} and {res is None}")
    return {'statusCode': 200,'body': json.dumps(res, default=str)} if res is not None  else {'statusCode': 404}

def lambda_handler(event, context):
    return schedule_handler(event, context)

