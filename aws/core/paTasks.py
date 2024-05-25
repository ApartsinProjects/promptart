import boto3,json
from core.paDB import Pdb
from core.paDocs import DocMng


class BaseHandler: #basic class for task specific handler
    def __init__(self,pdb=None,qname="promptart-tasks"):
        self.pdb=pdb if pdb else Pdb()
        self.qname=qname
        self.TM=TaskMng(qname,pdb) #knows about task manager
        self.DM=DocMng(pdb) #knows about task manager
        self.task,self.ctx=None,None
    
    def taskId(self): return self.task['uid'] if self.task else None
    def method(self): return self.task['method']
    def userId(self): return self.task['owner'] #user of teh task
    def opId(self): return self.task['tid'] #subject/actor transformer or feed/node
    def docId(self): return self.task['did'] #argument, 
    def doc(self): return self.DM.get(self.docId())
    def key(self): return self.task['key'] #for task train
    def placeholder(self,parent=None,feed=None,userId=None): 
        print(f"creating placeholder doc parent={parent} feed={feed} user={userId}")
        return self.DM.placeholder(userId if userId else self.userId() ,parent,feed) #create output placeholder
    
    def finish(self):return self.TM.finish(self.taskId(),self) #anounce current task as done
    def submit(self,task_list,ctx,parentTaskId=None): return self.TM.submit(task_list, ctx, parentTaskId if parentTaskId else self.taskId(),self.ctx) #submit new tasks with shared context while pushing current task/ctx to table
    def handle(self, task_id,ctx): #get task details from id, call virtual prepare and event hanlders
        print(f"handle event task={self.TM.get(task_id)} and ctx={ctx}")
        self.ctx,self.task =ctx,self.TM.get(task_id) #save current event into object
        return self.prepare().onEvent()
        
    def newTask(self,opId,docId=None,method='applyTransform',key=None,userId=None,placeholder=True): 
        return {'tid':opId,'did':docId if docId else (self.placeholder(userId=userId) if placeholder else None),'owner':userId if userId else self.userId(),"key":key, "method":method}
        
    #override these
    def onEvent(self): return self #process events
    def prepare(self):  return self #prepare context
    def nextContext(self,task): return task['context'] #update context for next in chainfor 
    def popContext(self,task): pass #update and save parent did
        
class TaskMng:
    def __init__(self,qname="promptart-tasks", pdb=None):self.pdb,self.sqs,self.qname= pdb if pdb else Pdb(),boto3.client('sqs'),qname
    def publish(self,task, next_taskId,parent_taskId):
        print(f"publishing task={task}")
        return self.pdb.insertObj('tasks',{**{'parent':parent_taskId,'next':next_taskId},**task})['uid']
        
    def get(self,taskId):return self.pdb.selectObj('tasks', taskId)
    def pushContext(self,taskId,ctx): return self.pdb.updateObj('tasks',taskId, {'context':ctx}) #save context when opening a node
    def queue(self,taskId,ctx):
        print(f"queue task={self.get(taskId)} ctx={ctx} taskId={taskId} qname={self.qname}")  
        self.sqs.send_message(QueueUrl=self.qname,MessageBody=json.dumps({'task_id':taskId,'context':ctx,"method":self.get(taskId)['method']}, default=str))
        return {'taskid':taskId}
    
    def submit(self,task_list, ctx, parent_taskId=None, parent_context=None): #use this to submit task trains
        if parent_context: self.pushContext(parent_taskId,parent_context) #push parent content
        next_taskId=None
        for t in reversed(task_list): next_taskId=self.publish(t,next_taskId,parent_taskId) #build a linked list of chain
        return self.queue(next_taskId,ctx) #queue first item
        
    def finish(self,taskId,handler): #call from atomic, when finished in task did there is a transform results
        task=self.get(taskId)
        print(f"finishing task={task}")
        if task['next']:  #if part of the chain
            print(f"queue next task={task['next']}")
            self.queue(task['next'],handler.nextContext(task)) #call next with updated context
        elif task['parent']: #need pop parent
            print(f"finish parent task={task['parent']}")
            parent_handler=self.getParentHandler(task,handler)
            parent_handler.popContext(task) #update parent with context, put result of child in parent did
            self.finish(task['parent'],handler) #anounce him as finished
        else:
            print("====root task finished====")
        ##self.pdb.updateObj('tasks',taskId,{'status':'ready'})
        return self.pdb.deleteObj('tasks', taskId)
        return self

    def getParentHandler(self, task,handler): 
        print(f"returning handler for task={task} src handler={handler}")
        return handler