import json,boto3
from core.paErrorHandler import TaskErrorHandler
from core.paDB import Pdb
from core.paTransform import Transformers
from core.paUsers import UserMng
from core.paMedia import PAMedia,file2type
from core.paDocs import DocMng
from core.paGraph import FeedMng
import os

qname=os.getenv('qname')
#qname="prompt-art-prod"

#transformers
def getTransformer(event,pdb):return Transformers(pdb,qname).get(event["pathParameters"]['tid'])
def deleteTransformer(event,pdb):return Transformers(pdb,qname).delete(event["pathParameters"]['tid'])
def updateTransformer(event,pdb): return Transformers(pdb,qname).update(event["pathParameters"]['tid'],event['body'])
def enumerateTransformers(event,pdb):return Transformers(pdb,qname).enumerate(event["queryStringParameters"]['query'])
def createTransformer(event,pdb): return Transformers(pdb,qname).create(event['body'])
def applyTransformer(event,pdb):  return Transformers(pdb,qname).applyAsync(event["pathParameters"]['tid'],event['body'])

#users
def insertUser(event,pdb):return UserMng(pdb).create(event['body'])
def getUser(event,pdb): return UserMng(pdb).get(event["pathParameters"]['uid'])
def enumerateUsers(event,pdb): return UserMng(pdb).enumerate(event["queryStringParameters"]['query'])
def deleteUser(event,pdb): return UserMng(pdb).delete(event["pathParameters"]['uid'])
def creditUser(event,pdb):return UserMng(pdb).credit(event["pathParameters"]['uid'],float(event["queryStringParameters"]['delta']))
def updateUser(event,pdb):return UserMng(pdb).update(event["pathParameters"]['uid'],event['body'])

#docs
def enumerateDocs(event,pdb): return DocMng(pdb).enumerate(event["queryStringParameters"]['query'])
def deleteDoc(event,pdb): return DocMng(pdb).delete(event["pathParameters"]['did'])
def createDoc(event,pdb): return DocMng(pdb).create(event.get('body',"{}"),save_media=True)
def formatDoc(event,pdb): return DocMng(pdb).format(event["pathParameters"]['did'], event["pathParameters"]['format'])
def updateDoc(event,pdb): return DocMng(pdb).update(event.get('body',"{}"),event["pathParameters"]['did'])

#feeds/graph
def getFeed(event,pdb): return FeedMng(pdb,qname).get(event['pathParameters']['fid'])
def updateFeed(event, pdb): return FeedMng(pdb,qname).update(event["pathParameters"]['fid'],event.get('body',"{}"))
def deleteFeed(event,pdb):return FeedMng(pdb,qname).delete(event["pathParameters"]['fid'])
def enumerateFeeds(event, pdb): return FeedMng(pdb,qname).enumerate(event["queryStringParameters"]['query'])
def createFeed(event,pdb): return FeedMng(pdb,qname).attach(event['body'])
def getMyFeedDocs(event, pdb): return FeedMng(pdb,qname).userDocsSince(event["pathParameters"]['fid'],event["queryStringParameters"]['uid'],event["queryStringParameters"]['since'])
def genFeedDocs(event,pdb): return FeedMng(pdb,qname).generateAsync(event["pathParameters"]['fid'],event["queryStringParameters"]['uid'],
                                                              event["queryStringParameters"]['maxnum'],event["queryStringParameters"]['since'],int(event["queryStringParameters"]['freq']))
def getFeedGenStatus(event,pdb): return FeedMng(pdb).getTaskStatus(event["pathParameters"]['gid'])


#API call map
ops_map={"getTransformer":getTransformer,"composeTransformer":createTransformer,"updateTransformer":updateTransformer,
         "deleteTransformer":deleteTransformer, "enumTransformers":enumerateTransformers,"applyTransformer":applyTransformer,
         "enumUsers":enumerateUsers, "createUser":insertUser,'getUser':getUser,'updateUserBalance':creditUser,'deleteUser':deleteUser,"updateUser":updateUser,
         "getFormattedDoc":formatDoc, "createDoc":createDoc,"updateDoc":updateDoc,"deleteDoc":deleteDoc,"enumDocs":enumerateDocs,
         "getFeed": getFeed, "deleteFeed": deleteFeed, "updateFeed":updateFeed,"enumFeeds":enumerateFeeds,"createFeed":createFeed,"getMyFeedDocs":getMyFeedDocs, "genFeedDocs":genFeedDocs,
         "genFeedStatus":getFeedGenStatus
}

def getMediaResponse(event):
    return {'headers': { "Content-Type": file2type(event["pathParameters"]['mid']) },
            'statusCode': 200,
            'body': PAMedia().fetchBase64(event["pathParameters"]['mid']),
            'isBase64Encoded': True}


def api_handler(event, context):
    print(f"processing api call {event}")
    try:
        # boto3.client('sqs').purge_queue(QueueUrl=qname) #debug
        print("not purging")
    except:
        print("purge in progress")
    op_name = event['requestContext']['operationName']
    if op_name == "getDocMedia":
        return getMediaResponse(event)
    else:
        if "body" in event:
            event['body'] = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        res = ops_map[op_name](event, Pdb())
        print(f"api handler returned {res} and {res is None}")
        return {'statusCode': 200, 'body': json.dumps(res, default=str)} if res is not None else {'statusCode': 404}

def lambda_handler(event, context):
    return api_handler(event, context)

