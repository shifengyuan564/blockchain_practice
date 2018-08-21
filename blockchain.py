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
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from uuid import uuid4
from argparse import ArgumentParser

from flask import Flask, jsonify, request
from pipenv.vendor import requests


class Blockchain:

    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # 创世纪区块
        self.new_block(proof=100, previous_hash='1')

    def register_node(self, address: str):
        """
        Add a new node to the list of nodes
        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def resolve_conflicts(self) -> bool:
        """
        共识算法解决冲突
        使用网络中最长的链.

        :return:  如果链被取代返回 True, 否则为False
        """
        neighbours = self.nodes

        # We're only looking for chains longer than ours
        max_length = len(self.chain)
        new_chain = None

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def valid_chain(self, chain: List[Dict[str, Any]]) -> bool:
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        # iterate the chain, check from chain[1]
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")

            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct ( begin with 0000)
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True  # the chain is valid

    def new_block(self, proof: int, previous_hash: Optional[str]) -> Dict[str, Any]:
        """
        生成新块

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        # 当前的交易已经打包成区块了，就没有了
        self.current_transactions = []
        self.chain.append(block)

        return block

    def new_transaction(self, sender: str, recipient: str, amount: int) -> int:
        """
        生成新交易信息，信息将加入到下一个待挖的区块中

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block: Dict[str, Any]) -> str:
        block_string = json.dumps(block, sort_keys=True).encode()
        # 获得摘要信息
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self) -> Dict[str, Any]:
        return self.chain[-1]

    # 工作量证明,用上一个区块的工作量证明和当前一起，
    # 看看算出来的hash值是否满足0000开头。满足返回当前值；不满足加一，进行下一次验证的运算
    def proof_of_work(self, last_proof: int) -> int:
        proof = 0

        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        print("【proof】：" + str(proof))
        return proof

    @staticmethod
    def valid_proof(last_proof: int, proof: int) -> bool:
        """
        验证证明: 是否hash(last_proof, proof)以4个0开头

        :param last_proof: Previous Proof
        :param proof: Current Proof
        :return: True if correct, False if not.
        """

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
blockchain = Blockchain()

# represent myself
node_identifier = str(uuid4()).replace('-', '')


# 路由
@app.route('/index', methods=['GET'])
def index():
    return "Hello BlockChain"


# 接收请求，添加交易
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ["sender", "recipient", "amount"]

    if values is None:
        return "Missing values", 400

    # all the keys in values[] should be in required[]
    if not all(k in values for k in required):
        return "Missing values", 400

    # make a new transaction
    idx = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    response = {"message": f'Transaction will be added to Block {idx}'}

    return jsonify(response), 201


# 挖矿
@app.route('/mine', methods=['GET'])
def mine():
    # wop
    last_proof = blockchain.last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # 给工作量证明的节点提供奖励.
    # 发送者为 "0" 表明是新挖出的币
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1
    )

    new_packed_block = blockchain.new_block(proof, None)

    response = {
        "message": "New Block Forged",
        "index": new_packed_block['index'],
        "transaction": new_packed_block['transactions'],
        "proof": new_packed_block['proof'],
        "previous_hash": new_packed_block['previous_hash']
    }

    return jsonify(response), 200


# {"nodes": ["http://localhost:5000"] }
@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    nodes = request.get_json().get('nodes')

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)  # register all nodes in blockchain

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


# python blockchain.py -p 5001
# python blockchain.py -p 5000
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port)
