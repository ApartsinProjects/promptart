
def total_bill(user,bill): return sum([v for k,v in bill.items() if k!=user])
def total_payoff(user, fees): return sum([total_bill(user, v) for v in fees.values()])

class UserMng:
    def __init__(self,pdb):self.pdb=pdb
        
    def payoff(self, uid, fees):
        for k,v in fees.items(): self.payBill(uid,v)
        return self
        
    def payBill(self,uid, bill):
        for recipient,value in bill.items(): self.transfer(uid,recipient,value)
        return self
        
    def credit(self, uid, value):return self.pdb.updateObj('users',uid,{"balance":self.get(uid)['balance']+value})
    def create(self,obj):return self.pdb.insertObj('users',obj)
    def get(self, uid): return self.pdb.selectObj('users',uid)
    def delete(self, uid): return self.pdb.deleteObj('users',uid)
    def enumerate(self, q): return self.pdb.findObjs('users',q)
    def balance(self,uid): return self.get(uid)['balance']
    def update(self,uid,obj): return self.pdb.updateObj("users",uid,obj) 
        
    def transfer(self, sender, recipient, value):
        self.credit(sender,-value)
        self.credit(recipient,+value)
        
    def attemptPayoff(self,uid,fees):
        total=total_payoff(uid, fees)
        if total<self.balance(uid):
            self.payoff(uid, fees)
            return True
        else:
            return False
            
        