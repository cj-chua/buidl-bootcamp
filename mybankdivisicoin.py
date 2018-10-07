from copy import deepcopy
from uuid import uuid4

class Tx:

    def __init__(self, id, tx_ins, tx_outs):
        self.id = id
        self.tx_ins = tx_ins
        self.tx_outs = tx_outs

    def sign_input(self, index, private_key):
        sig = private_key.sign(self.tx_ins[index].spend_message)
        self.tx_ins[index].signature = sig

class TxIn:

    def __init__(self, tx_id, index, signature):
        self.tx_id = tx_id
        self.index = index
        self.signature = signature

    @property
    def spend_message(self):
        return f'{self.tx_id}:{self.index}'.encode()

class TxOut:

    def __init__(self, tx_id, index, amount, public_key):
        self.tx_id = tx_id
        self.index = index
        self.amount = amount
        self.public_key = public_key

class Bank:
    
    def __init__(self):
        # bank knows of all the transactions out there
        self.txs = {}

    def issue(self, amount, public_key):
        # bank can create money out of thin air and send it to someone.
        # In this case it's a transaction
        id = str(uuid4())
        tx_ins = []
        tx_outs = [TxOut(id, 0, amount, public_key)]
        tx = Tx(id, tx_ins, tx_outs)
        self.txs[tx.id] = deepcopy(tx)
        return tx

    def is_unspent(self, tx_in):
        for txs in self.txs.values():
            for _tx_in in txs.tx_ins:
                if tx_in.tx_id == _tx_in.tx_id and \
                   tx_in.index == _tx_in.index:
                   return False
        return True

    def validate_tx(self, tx):
        # verify that all inputs are from utxo set
        # verify that all inputs' signature is valid
        # sum(inputs) == sum(outputs)
        sum_ins = 0
        sum_outs = 0
        for tx_in in tx.tx_ins:
            assert self.is_unspent(tx_in)

            tx_out = self.txs[tx_in.tx_id].tx_outs[tx_in.index]
            tx_out.public_key.verify(tx_in.signature, tx_in.spend_message)
            sum_ins += tx_out.amount

        for tx_out in tx.tx_outs:
            sum_outs += tx_out.amount
            
        assert sum_ins == sum_outs

    def handle_tx(self, tx):
        # validate transaction
        # update transactions database
        self.validate_tx(tx)
        self.txs[tx.id] = deepcopy(tx)

    def fetch_utxos(self, public_key):

        txs = self.txs.values()
        spent_pairs = [(tx_in.tx_id, tx_in.index)
                       for tx in txs
                       for tx_in in tx.tx_ins]
        '''
        utxos = [tx_out
                 for tx in txs
                 for tx_out in tx.tx_outs
                 if tx_out.public_key == public_key
                 and (tx_out.tx_id, tx_out.index) not in spent_pairs]
        '''
        return [tx_out for tx in self.txs.values() 
                for i, tx_out in enumerate(tx.tx_outs)
                if public_key.to_string() == tx_out.public_key.to_string()
                and (tx.id, i) not in spent_pairs]

        return utxos
        
    def fetch_balance(self, public_key):
        utxos = self.fetch_utxos(public_key)
        return sum([txo.amount for txo in utxos])
