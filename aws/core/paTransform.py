from core.paDocs import DocMng
from core.paUsers import UserMng
from core.paTransformSrv import TransformSrv



class Transformers:
    def __init__(self,pdb,qname=None):self.pdb,self.qname=pdb,qname
    def get(self,tid): return self.pdb.selectObj("transformer",tid)
    def delete(self,tid): 
        self.update(tid,{'visibility':'deleted'})
        return tid
    def update(self,tid,obj): return self.pdb.updateObj("transformer",tid,obj)
    def enumerate(self,query):return self.pdb.findObjs('transformer',query)

    def create(self,obj): #create or compose
        if isinstance(obj["cfg"]["chain"], list): obj=self._compose(obj)
        obj['fees']=self._updateFees(obj.get('fees',None),obj['cfg'])
        return self.pdb.insertObj("transformer",obj)

    def setup(self, tid, obj):  # save inpt, pay, prepare ctx
        dm = DocMng(self.pdb)
        if not UserMng(self.pdb).attemptPayoff(obj['owner'], self.get(tid)['fees']):
            print(f"user {obj['owner']} has not enough credits to execute transform {tid}")
            return None
        if obj.get('content',None):obj['did']=dm.create(obj,save_media=True)['uid']
        print(f"prepared doc for  transformer API call doc={obj}")
        return obj['did']

    def applyAsync(self,tid, obj):
        return TransformSrv(self.pdb,self.qname).startTransform(tid,self.setup(tid,obj),obj['owner'])

    def _compose(self,obj):
        obj['cfg']=self._fromChain(obj['cfg']['chain'], obj.get('mapio',{}) if obj.get('mapio',{}) else {})
        return obj

    def _fromChain(self, chain, chain_map={}):  # chain cofgs together
        out, last_label = {"chain": {}}, None

        for label, tid in enumerate(chain):
            out = self._insertStep(out, tid, str(label), last_label, chain_map)
            last_label = str(label)

        out["out_doc"] = {**out["chain"][last_label]['out_doc'],
                          **{'$$': "{{chain[" + "\"" + last_label + "\"" + "][\"out_doc\"]}}"}}
        return out
    
    def _insertStep(self,out,tid,label, prev_label,chain_map):
        cfg=self.pdb.selectObj("transformer",tid)['cfg']
        
        out['vars']={**out.get("vars",{}),**cfg.get("vars",{})}
        out['chain'][label]={"vars":{k:"{{vars[\""+k+"\"]}}" for k in cfg.get("vars",{})},"chain":tid,"out_doc":{},"in_doc":{}}
        
        if not prev_label: #first step
            out["in_doc"]=cfg.get("in_doc",{})
            out["chain"][label]["in_doc"]={'$':"{{in_doc}}"}
        else:
            out['chain'][label]["in_doc"] = {"$": "{{chain[" + "\"" + prev_label + "\"" + "][\"out_doc\"]}}"}

        out['chain'][label]["in_doc"].update(chain_map.get(label, {}))
        return out
        
    def _updateFees(self,fees,cfg):
        print(f"updateing fees {fees} using cfg={cfg}")
        if not fees: fees={"process_fees":{},"prompt_fees":{}}
        if isinstance(cfg["chain"],dict):
            for k,v in cfg["chain"].items():
                fees=Transformers._addFees(fees, self.pdb.selectObj("transformer", v["chain"])['fees'])
        elif not cfg["chain"].startswith('_'):
            fees=Transformers._addFees(fees, self.pdb.selectObj("transformer", cfg["chain"])['fees'])
        return fees 
    
    @staticmethod
    def _addFees(fees, child):
        print(f"adding fees of child={child} to parent={fees}")
        for k in ["prompt_fees","process_fees"]:
            for u,f in child.get(k, {}).items(): fees[k][u]=fees[k].get(u,0)+f
        return fees
