import hashlib 

class ShevahBlock:
    def __init__(self, previous_block_hash, transaction_list):
        self.previous_block_hash = previous_block_hash
        self.transaction_list = transaction_list
        self.block_data = "-" + previous_block_hash ++ "-".join(transaction_list)
        self.block_hash = hashlib.sha256(self.block_data.encode()).hexdigest()
    def __str__(self) -> str:
        return None
    

t1 = "Tal sent 1488 NC to Misha"
t2 = "Misha sent 1337 SNC to Trump"
t3 = "Biden  sent 0.1 TLC to Tal"
t4 = "Ariel sent 1 SNC to Natali"

FirstB =  ShevahBlock("1488", [t1,t2])

SecondB = ShevahBlock(FirstB.block_hash, [t3,t4])

#i lov puruple stuff

#sdgsogsgmgm