from datetime import datetime
from core.paUsers import UserMng
from core.paTransformSrv import TransformSrv

#here docId is input doc, not a placeholder for output a sin transformers
class DispatchSrv(TransformSrv):
    def __init__(self,pdb=None,qname="promptart-tasks"): super().__init__(pdb,qname)
       
    def feedId(self): return self.opId()  #task are generic and have opId, here opId is the same as feedId (or NodeId)
    def node(self): return self.pdb.selectObj("nodes",self.feedId())
    def srcFeedId(self): return self.node()['source']
    def lastAttempt(self): return self.node()['lastattempt']
    def since(self): return self.ctx["since"]
    def freq(self): return self.ctx["freq"]
    def numReqDocs(self): return int(self.ctx["num_docs"])
    def nodeTransformId(self): return self.node()['transformer']
    def transformer(self): return  self.pdb.selectObj("transformer",self.nodeTransformId())
    def feedDocs(self):return self.DM.feedDocs(self.feedId(),self.since())
    def srcDocs(self): return self.DM.feedDocs(self.srcFeedId(),self.since()) if self.srcFeedId() else [None]*self.numReqDocs() 
    def numLeft(self): return self.numReqDocs()-len(self.feedDocs())
    def numReady(self): return self.numReqDocs() if self.numLeft()<0 else self.numReqDocs()-self.numLeft()
    def numSrcLeft(self): return self.numReqDocs()-len(self.srcDocs()) if self.srcFeedId() else 0
    def secsToNextAttempt(self): return self.freq()-(datetime.utcnow()-self.lastAttempt()).seconds
    
    
    def onEvent(self): 
        ehmap={"genAndPayFeed":self.onGenAndPayEvent, "genFeed":self.onGenEvent, "procFeed":self.onProcEvent,"applyTransformer":super().onEvent}
        return ehmap[self.method()]()   
    
            
    def onGenAndPayEvent(self): #process feed generation event or pay if exists
        print(f"processing feed generation onGenAndPayEvent task={self.task} ctx={self.ctx}")
        
        if self.secsToNextAttempt()>=0:
            print(f"nothing to generate time since last attempt {self.secsToNextAttempt()} ctx={self.ctx} last={self.lastAttempt()} num_left={self.numLeft()}")
            return self.finish()
        
        print(f"userid {self.userId()}, numrequest {self.numReqDocs()}, numleft {self.numLeft()}, numready {self.numReady()},  nonuserdocs {self.feedDocs()}, numsrcleft {self.numSrcLeft()}")
        if self.numLeft()>0:
            if self.numReady()>0: list(map(self.buyDocAccess, self.feedDocs()[-self.numReady():])) # buy access for already generated docs and generate the rest
            self.pdb.updateObj("nodes",self.feedId(),{'lastattempt':datetime.utcnow()})
            srcTask=[self.newTask(opId=self.srcFeedId(), method='genFeed',placeholder=False)] if self.numSrcLeft()>0 else []
            return self.submit(srcTask+[self.newTask(opId=self.feedId(), method='procFeed',placeholder=False)],self.ctx)#{**self.ctx, "num_docs":self.numLeft()}) #break it into source gen and src doc process
        elif self.numReady()>0:
            list(map(self.buyDocAccess, self.feedDocs()[-self.numReady():])) # buy access for already generated docs
         
        return self.finish()
            

    def onGenEvent(self): #process feed generayion event
        print(f"processing feed generation onGenEvent task={self.task} ctx={self.ctx}")
        print(f"userid {self.userId()}, numleft {self.numLeft()}, nonuserdocs {self.feedDocs()}, feed {self.feedId()}")

        if self.numLeft()>0 and self.secsToNextAttempt()<0:
            
            self.pdb.updateObj("nodes",self.feedId(),{'lastattempt':datetime.utcnow()})
            srcTask=[self.newTask(opId=self.srcFeedId(), method='genFeed',placeholder=False)] if self.numSrcLeft()>0 else []
            return self.submit(srcTask+[self.newTask(opId=self.feedId(), method='procFeed',placeholder=False)],self.ctx) #break it into source gen and src doc process
        else:
            print(f"nothing to generate time since last attempt {self.secsToNextAttempt()} ctx={self.ctx} last={self.lastAttempt()} num_left={self.numLeft()}")
            return self.finish()
            
    def onProcEvent(self):
        return self.splitDocs() if self.node()['nodetype']=='splitter' else self.procDocs()
            
    def splitDocs(self):
        print(f"SplitDocs, src docs={self.srcDocs()}")
        for docId in self.srcDocs():
            if self.buyDocAccess(docId):
                doc=self.DM.get(docId)
                if isinstance(doc['content'],list):
                    for p in doc['content']:
                        self.DM.create({'feed':self.feedId(),'owner':self.userId(),'parent':docId,'content':p})
                else:
                    self.DM.create({'feed':self.feedId(),'owner':self.userId(),'parent':docId,'content':doc['content']})
            else:
                break
        return self
        
    def procDocs(self):
        tasks=[]
        for docId in self.srcDocs()[-self.numReqDocs():]:
            print(f"processing doc={docId} by feed={self.feedId()}")
            if self.chargeUser(docId): 
                tasks+=[self.applyTask(self.nodeTransformId(),docId,self.placeholder(docId,self.feedId(),self.userId()),self.userId())]
            else:
                print("no more money")
                break
        return self.submit(tasks, None, self.task['uid']) if len(tasks) else self
            
    def startGeneration(self,feedId,userId,num_docs,since,freq):
        return self.submit([self.newTask(opId=feedId,method='genAndPayFeed',userId=userId,placeholder=False)],ctx={'num_docs':num_docs,'since': since,'freq':freq}) 

    def updateGenTime(self,did):
        doc=self.DM.get(did)
        return self.pdb.updateObj("nodes",doc['feed'],{'lastgen':doc['datecreated']}) if doc.get("feed", None) else None
        
    def buyDocAccess(self, docId):
        if docId and not self.DM.buyAccess(docId,self.userId()):
            print(f"user {self.userId()} has not enough credits to pay royaltees for src doc {docId}")
            return False
        return True
            
    def chargeUser(self,docId):
        if not self.buyDocAccess(docId): return False
        if not UserMng(self.pdb).attemptPayoff(self.userId(),self.transformer()['fees']):
            print(f"user {self.userId()} has not enough credits to apply feed transform {self.feedId()}")
            return False
        return True
        
    def nextContext(self,task): #task results are in its did in DB, need to fetch and put into the context out_doc so next task can pick its input from contexnt
        if task['method']=='applyTransformer':
            self.updateGenTime(task['did'])
            return super().nextContext(task)
        else:
            return task['context']
        
    def popContext(self,task): 
        return super().popContext(task) if task['method']=='applyTransformer' else None
            
    def prepare(self):
        if self.method()=="applyTransformer":
            if not self.ctx:
                self.ctx={"in_doc":self.DM.content(self.task['key'])}
                self.task['key']=None #dirty trick
            return super().prepare()
        else:
            return self