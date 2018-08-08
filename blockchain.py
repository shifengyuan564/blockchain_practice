# {
#     "index":0,
#     "timestamp":"",
#     "transactions":[
#         {
#             "sender":"",
#             "recipient":"",
#             "amount":5
#         }
#     ],
#     "proof":"",
#     "previous_hash":""
# }

class Blockchain:

    def __init__(self):
        self.chain = []
        self.current_transactions = []

    def new_block(self):
        pass

    def new_transaction(self, sender, recipient, amount) -> int:
        self.current_transactions.append({
            'sender': sender,
            'recipient':recipient,
            'amount':amount
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(self):
        pass

    @property
    def last_block(self):
        pass
