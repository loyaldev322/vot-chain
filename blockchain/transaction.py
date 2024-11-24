from collections import OrderedDict
from utility.printable import Printable

class Transaction:

    """ A transaction which can be added to a block in the blockchain.
    Attributes:
        :sender: The sender of the coins.
        :recipient: The recipient of the coins.
        :signature: The signature of the transaction.
        :amount: The amount of coins sent.
        :memo: a string label.
    """

    def __init__(self,sender,recipient,signature,amount,memo):
        self.sender = sender
        self.recipient = recipient
        self.signature  = signature
        self.amount = amount
        self.memo = memo

    def to_ordered_dict(self):
        return OrderedDict([
            ('sender', self.sender),
            ('recipient', self.recipient),
            ('amount', self.amount),
            ('memo',self.memo),
            ('signature',self.signature)]
        )