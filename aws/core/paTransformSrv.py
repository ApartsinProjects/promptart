from core.paTasks import BaseHandler
from utils.paTemplates import prepContext,resolveKey
from core.paAtomic import applyAtomic

#input is in contenxt, output is in docid in task
class TransformSrv(BaseHandler): #nadlse asynhcronous sqs events
    def __init__(self,pdb=None,qname="promptart-tasks"): super().__init__(pdb,qname)
    
    def transformId(self): return self.opId() #just rename for clarity, 
    def outDocId(self): return self.docId() #for clarity
    def obj(self): return self.pdb.selectObj("transformer",self.transformId())
    def cfg(self): return self.obj()['cfg']
    def chain(self): return self.ctx['chain']
    def applyTask(self,opId,key=None,docId=None,userId=None): return self.newTask(opId=opId,docId=docId,userId=userId,method="applyTransformer",key=key)
    
    def saveDoc(self,doc): #save doc from atomic
        self.ctx["out_doc"]={**self.ctx.get("out_doc",{}),**doc} #merge and resolve output
        return self.DM.saveContent(self.outDocId(),self.ctx['out_doc']) #save content into did
   
    def _processSingle(self,ctx): #procesisng a singe call
        if ctx['chain'].startswith("_"):
            self.saveDoc(applyAtomic(ctx['chain'],ctx, self.userId())) #process and create doc
            return self.finish()
        else:
            return self.submit([self.applyTask(ctx['chain'])],ctx) #create and submit child task
        
    def _updateOutput(self,task, dst): #merge out doc with dst and resolve mapping if any
        dst['out_doc']={**dst.get("out_doc",{}), **self.DM.content(task['did'])} if self.DM.content(task['did']) else dst.get("out_doc",{})
        return resolveKey(dst, "out_doc")

    def prepare(self): #prepare context
        if self.key() is not None: #task is a part of a chain
            resolveKey(self.ctx,self.key(),"chain") #context is shared need to prepare specifci item
        else:
            print(f"preparing context cfg={self.cfg()} ctx={self.ctx}")
            self.ctx=prepContext(self.cfg(),self.ctx) #context from transformer
        return self
        
    def onEvent(self): 
        print(f"processing transform event {self.task} with ctx={self.ctx}")
        if isinstance(self.chain(),str) or (self.key() is not None): #single transformer
            ctx=self.ctx['chain'][self.key()] if self.key() is not None  else  self.ctx
            return self._processSingle(ctx) 
        else:#start new chain
            return self.submit([self.applyTask(v['chain'],k) for k,v in self.chain().items()],self.ctx) 
    
    def nextContext(self,task): #task results are in its did in DB, need to fetch and put into the context out_doc so next task can pick its input from contexnt
        if task.get('context',None) and task.get("key",None): self._updateOutput(task,task['context']['chain'][task['key']])
        return task['context']
        
    def popContext(self,task): #put this task out_doc into the parent context, resolve and save as a parent DID
        parentTask=self.TM.get(task['parent'])
        print(f"popping contexnt parent={parentTask}")
        if parentTask and (parentTask['method']=="applyTransformer"):
            print(f'saving to parent {parentTask}')
            return self.DM.saveContent(parentTask['did'],self._updateOutput(task,parentTask['context']))
        else:
            print(f"no context in parent {parentTask}")
            return None
        
    def startTransform(self,transformId,in_docId,userId,feedId=None,parent_taskId=None): 
        print(f"starting transform id={transformId} on doc={in_docId} with parent={parent_taskId}")
        root_task=self.applyTask(transformId,None,self.placeholder(in_docId,feedId,userId),userId)
        print(f"root task for transform created={root_task}")
        self.submit([root_task], {"in_doc":self.DM.content(in_docId)}, parent_taskId)
        return {"did":root_task['did']}  
   
        


   
      
        