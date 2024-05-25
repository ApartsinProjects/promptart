import sys
import os
import json
import traceback

import boto3

sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.join("..", "..", "core"))))

from core.paDB import Pdb
from core.paDispatch import DispatchSrv
from core.paPublish import PublishMng
from core.paErrorHandler import TaskErrorHandler


# event handlers
def applyTransformEvt(event, pdb): return DispatchSrv(pdb, qname).handle(event['task_id'], event['context'])


def genFeedEvt(event, pdb): return DispatchSrv(pdb, qname).handle(event['task_id'], event['context'])


def processFeedEvt(event, pdb): return DispatchSrv(pdb, qname).handle(event['task_id'], event['context'])


def publishDoc(event, pdb): return PublishMng(pdb, qname).publishDoc(event['context'])


def publishAll(event, pdb): return PublishMng(pdb, qname).publishAll()


# SQS dispatch map
evt_map = {"applyTransformer": applyTransformEvt, "genFeed": genFeedEvt, "genAndPayFeed": genFeedEvt,
           "procFeed": processFeedEvt, "publishDoc": publishDoc, "publishAll": publishAll}

qname = os.environ["PA_SQS_NAME"]


def sqs_messages_handler(sqs_response, sqs_client):
    print(f"processing sqs messsges {sqs_response} num messages {len(sqs_response['Messages'])}")
    if 'Messages' in sqs_response:
        for message in sqs_response['Messages']:
            # Process the message
            event = message['Body'] if isinstance(message['Body'], dict) else json.loads(message['Body'])  # allow debug
            try:
                res = evt_map[event['method']](event, Pdb())
                print(res)
            except Exception as ex:
                if event.get("task_id", None):
                    TaskErrorHandler(Pdb()).handle(event, str(ex))
                print(traceback.format_exc())
                # boto3.client('sqs').purge_queue(QueueUrl=qname)  # debug

            # Delete the processed message from the queue
            sqs_client.delete_message(
                QueueUrl=qname,
                ReceiptHandle=message['ReceiptHandle']
            )


def main():
    # Create an SQS client
    sqs_client = boto3.client('sqs')

    # Continuously poll for messages
    while True:
        # Receive a message from the queue
        response = sqs_client.receive_message(
            QueueUrl=qname,
            AttributeNames=['All'],
            MaxNumberOfMessages=10,
            WaitTimeSeconds=2
        )
        if response.get("Messages"):
            sqs_messages_handler(response, sqs_client)


if __name__ == '__main__':
    main()
