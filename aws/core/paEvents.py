from core.paTasks import BaseHandler
from core.paTransform import Transformers
from core.paDocs import DocMng
from utils.paTemplates import prepContext,resolveKey
from core.paAtomic import applyAtomic

class TransformerHandler(BaseHandler): #nadlse asynhcronous sqs events
    def __init__(self): super().__init__()
    def cfg(self): return Transformers(self.TQ.pdb).get(self.task['tid'])['cfg']
    def user(self): return self.task['owner'] 
    def key(self): return self.task.get('key',None)
    def chain(self): return self.ctx['chain']
    def outDid(self): return DocMng(self.TQ.pdb).placeholder(self.user())
    def newTask(self,tid,key=None): return {'tid':tid,'did':self.outDid(),'owner':self.user(),"key":key}
    def saveDoc(self,doc): #save doc from atomic
        self.ctx["out_doc"]={**self.ctx.get("out_doc",{}),**doc}
        return DocMng(self.TQ.pdb).saveContent(self.task['did'],self.ctx['out_doc'])
   
    def _processSingle(self,ctx): #procesisng a singe call
        if ctx['chain'].startswith("_"): #atomic
            self.saveDoc(applyAtomic(ctx['chain'],ctx, self.user())) #process and create doc
            return self.finish() #finish this task
        else:
            return self.submit([self.newTask(ctx['chain'])],ctx) #create and submit child task
        
    def _updateOutput(self,task, dst): #merge out doc with dst and resolve mapping if any
        dst['out_doc']={**dst.get("out_doc",{}),**DocMng(self.TQ.pdb).content(task['did'])}
        res=resolveKey(dst, "out_doc")
        return res
        
    def prepare(self): #prepare context
        if self.key() is not None: #task is a part of a chain
            resolveKey(self.ctx,self.key(),"chain") #context is shared need to prepare specifci item
        else:
            print(f"preparing context cfg={self.cfg()} ctx={self.ctx}")
            self.ctx=prepContext(self.cfg(),self.ctx) #context from transformer
        return self
        
    def onEvent(self): 
        if isinstance(self.chain(),str) or (self.key() is not None): #single transformer
            ctx=self.ctx['chain'][self.key()] if self.key() is not None  else  self.ctx
            return self._processSingle(ctx) 
        else:#start new chain
            return self.submit([self.newTask(v['chain'],k) for k,v in self.chain().items()],self.ctx) 
    
    def nextContext(self,task): #put did of a task into its context and resolve
        self._updateOutput(task,task['context']['chain'][task['key']])
        return task['context']
        
    def popContext(self,task): #put did of a task into its parent context, resolve and save to parent did
        parent=self.TQ.get(task['parent'])
        return DocMng(self.TQ.pdb).saveContent(parent['did'],self._updateOutput(task,parent['context']))
        


   
      
        