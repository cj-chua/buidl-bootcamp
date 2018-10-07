from uuid import uuid4
from copy import deepcopy
from ecdsa import SigningKey, SECP256k1
from utils import serialize

bank_private_key = SigningKey.generate(curve=SECP256k1)
bank_public_key = bank_private_key.get_verifying_key()

def transfer_message(previous_signature, public_key):
    return serialize({
        "previous_signature": previous_signature,
        "next_owner_public_key": public_key,
    })


class Transfer:
    
    def __init__(self, signature, public_key):
        self.signature = signature
        self.public_key = public_key

    def __eq__(self, other):
        return self.signature == other.signature and \
               self.public_key.to_string() == other.public_key.to_string()

class BankCoin:
    
    def __init__(self, transfers):
        self.transfers = transfers
        self.id = uuid4()

    def __eq__(self, other):
        return self.id == other.id and self.transfers == other.transfers

    def validate(self):
        # Check the second transfer and onwards
        # First transfer is issued by bank, no need to be checked
        previous_transfer = self.transfers[0]
        for transfer in self.transfers[1:]:
            # Check previous owner signed this transfer using their private key
            assert previous_transfer.public_key.verify(
                transfer.signature,
                transfer_message(previous_transfer.signature, transfer.public_key)
            )
            previous_transfer = transfer

    def transfer(self, owner_private_key, recipient_public_key):
        message = transfer_message(
            previous_signature=self.transfers[-1].signature,
            public_key=recipient_public_key
        )
        sig = owner_private_key.sign(message)
        transfer = Transfer(
            signature=sig,
            public_key=recipient_public_key
        )
        self.transfers.append(transfer)

class Bank:

    def __init__(self):
        '''
        a database of all existing coins out there.
        Each coin has it's own transactions history
        key: coin's uuid(unique identifier)
        value: the coin itself(contains transactions history)
        '''
        self.coins = {}

    def issue(self, public_key):
        transfer = Transfer(
            signature=None,
            public_key=public_key,
            )
    
        # Create and return the coin with just the issuing transfer
        coin = BankCoin(transfers=[transfer])

        self.coins[coin.id] = deepcopy(coin)

        return coin

    def fetch_coins(self, public_key):
        '''
        find all coins that belong to the public key
        '''
        coins = []
        for coin in self.coins.values():
            if coin.transfers[-1].public_key.to_string() == public_key.to_string():
                coins.append(coin)

        return coins

    def observe_coin(self, coin):
        '''
        validate all transfers in the coin and
        update the database
        '''
        last_observed = self.coins[coin.id]
        assert last_observed.transfers == coin.transfers[:len(last_observed.transfers)]

        coin.validate()

        self.coins[coin.id] = deepcopy(coin)
