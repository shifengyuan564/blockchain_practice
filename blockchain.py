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

import hashlib
import json
from time import time

from flask import Flask


class Blockchain:

    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # 创世纪区块
        self.new_block(proof=100, previous_hash=1)

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.last_block())
        }

        # 当前的交易已经打包成区块了，就没有了
        self.current_transactions = []
        self.chain.append(block)

        return block

    def new_transaction(self, sender, recipient, amount) -> int:
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        # 获得摘要信息
        hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    # 工作量证明,用上一个区块的工作量证明和当前一起，
    # 看看算出来的hash值是否满足0000开头。满足返回当前值；不满足加一，进行下一次验证的运算
    def proof_of_work(self, last_proof: int) -> int:
        proof = 0

        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        print("【proof】：" + str(proof))
        return proof

    def valid_proof(self, last_proof: int, proof: int) -> bool:
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        # 【guess_hash】：0000c415de5ceea33c02daa85a1c218ecca1b1c9e9864ed34d183597844de8e2
        print("【guess_hash】：" + guess_hash)

        # 以0000开头
        return guess_hash[0:4] == "0000"


# 计算出一个工作量证明（proof）
# testPow = Blockchain()
# testPow.proof_of_work(100)

app = Flask(__name__)


# 路由
@app.route('/index', methods=['GET'])
def index():
    return "Hello BlockChain"


# 接收请求，添加交易
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    return "We will add a new transactions"


# 挖矿
@app.route('/mine', methods=['GET'])
def mine():
    return "We will a new block"


@app.route('/chain', methods=['GET'])
def full_chain():
    return "return full chain"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
