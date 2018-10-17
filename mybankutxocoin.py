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

    @property
    def outpoint(self):
        return (self.tx_id, self.index)

class TxOut:

    def __init__(self, tx_id, index, amount, public_key):
        self.tx_id = tx_id
        self.index = index
        self.amount = amount
        self.public_key = public_key

    @property
    def outpoint(self):
        return (self.tx_id, self.index)

class Bank:
    
    def __init__(self):
        # bank knows of all the transactions out there
        # (tx_id,index) -> tx_out
        self.utxo = {}

    def update_utxo(self, tx):
        for tx_in in tx.tx_ins:
            del self.utxo[tx_in.outpoint]
        for tx_out in tx.tx_outs:
            self.utxo[tx_out.outpoint] = tx_out

    def issue(self, amount, public_key):
        # bank can create money out of thin air and send it to someone.
        # In this case it's a transaction
        id = str(uuid4())
        tx_ins = []
        tx_outs = [TxOut(id, 0, amount, public_key)]
        tx = Tx(id, tx_ins, tx_outs)
        self.update_utxo(tx)
        return tx

    def validate_tx(self, tx):
        # verify that all inputs are from utxo set
        # verify that all inputs' signature is valid
        # sum(inputs) == sum(outputs)
        sum_ins = 0
        sum_outs = 0
        for tx_in in tx.tx_ins:
            assert tx_in.outpoint in self.utxo

            tx_out = self.utxo[tx_in.outpoint]
            tx_out.public_key.verify(tx_in.signature, tx_in.spend_message)
            sum_ins += tx_out.amount

        for tx_out in tx.tx_outs:
            sum_outs += tx_out.amount
            
        assert sum_ins == sum_outs

    def handle_tx(self, tx):
        # validate transaction
        # update transactions database
        self.validate_tx(tx)
        self.update_utxo(tx)

    def fetch_utxos(self, public_key):
        return [utxo
                for utxo in self.utxo.values()
                if utxo.public_key.to_string() == public_key.to_string()]
        
    def fetch_balance(self, public_key):
        utxos = self.fetch_utxos(public_key)
        return sum([txo.amount for txo in utxos])
