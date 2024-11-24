from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import binascii

class Wallet:    


    def sign_transaction(self,sender,recipient,amount,memo,private_key):
        signer = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(private_key)))
        h = SHA256.new((str(sender)+str(recipient)+str(amount)+str(memo)).encode('utf8'))
        signature = signer.sign(h)
        return binascii.hexlify(signature).decode('ascii')
    
    @staticmethod
    def verify_transaction(transaction):
        publc_key = RSA.importKey(binascii.unhexlify(transaction.sender))
        verifier =PKCS1_v1_5.new(publc_key)
        h = SHA256.new((str(transaction.sender)+str(transaction.recipient)+str(transaction.amount)+str(transaction.memo)).encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(transaction.signature))
