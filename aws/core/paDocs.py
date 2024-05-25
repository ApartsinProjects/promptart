from core.paMedia import PAMedia
from core.paUsers import UserMng

class DocMng:
    def __init__(self,pdb):self.pdb=pdb
    def get(self,did): return self.pdb.selectObj("docs",did)
    def delete(self,did):
        if (doc:=self.get(did)).get("content"):
            PAMedia().deleteDocMedia(doc)
        return self.pdb.deleteObj("docs",did)
    def enumerate(self, q): return self.pdb.findObjs('docs',q)
    def update(self,obj,did=None,save_media=False): 
        return self.pdb.updateObj("docs",did,{**{'status': 'ready'}, **obj}) if did else self.create(obj,save_media)
    
    def create(self,obj,save_media=False):
        if save_media: PAMedia().saveDocMedia(obj['content'])
        doc=self.pdb.insertObj("docs",{**{'status': 'ready'}, **obj})
        self.addAccess(doc['uid'],obj['owner'])
        return doc
        
    def placeholder(self, owner,parent=None,feed=None): return self.create({'owner':owner,"status":'pending','parent':parent,"feed":feed})['uid']
    def content(self,did): return self.format(did)['content'] if did else  {} 
    def status(self,did): return self.format(did)['status']
    def saveContent(self,did,content,save_media=False): return self.update({'content':content},did,save_media)
        
    def format(self,did,fmt=None):
        obj=self.get(did)
        if fmt=="json_base64": PAMedia().fetchDocMedia(obj['content'])
        return obj
        
    def feedDocs(self,fid,since): 
        res=self.enumerate(f"feed='{fid}' and datecreated>'{since}'")
        return [r['uid'] for r in res]
    def hasAccess(self,did,uid):return len(self.pdb.findRows('rights',{'userid':uid,'docid':did}))!=0 
    def addAccess(self,did,uid): return self.pdb.insert('rights',{'userid':uid,'docid':did})    
    def buyAccess(self,did,uid):
        if self.hasAccess(did,uid): return True
        doc=self.get(did)
        
        if doc['parent'] and not self.buyAccess(doc['parent'],uid):
             print(f"can't buy access to parent {doc['parent']} for user={uid}")
             return False
         
        fees=self.pdb.selectObj('transformer',self.pdb.selectObj('nodes',doc['feed'])['transformer'])['fees']
        if not UserMng(self.pdb).attemptPayoff(uid, {'prompt_fees':fees['prompt_fees']}): 
            print(f"can't pay transformer royaltees {doc['feed']} for user={uid}")
            return False
        
        return self.addAccess(did,uid)
       
        
    