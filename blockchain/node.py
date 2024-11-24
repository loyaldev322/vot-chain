from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from wallet import Wallet
from blockchain import Blockchain


prt = 5001
app = Flask(__name__)
CORS(app)


# @app.route('/wallet', methods=['POST'])
# def create_keys():
#     wallet.create_keys()
#     if wallet.save_keys():
#         global blockchain
#         blockchain = Blockchain(wallet.public_key, prt)
#         response = {
#             'public_key': wallet.public_key,
#             'private_key': wallet.private_key,
#             'funds': blockchain.get_balance()
#         }
#         return jsonify(response), 201
#     else:
#         response = {
#             'message': 'Saving the keys failed.'
#         }
#         return jsonify(response), 500
    
    

# @app.route('/wallet', methods=['GET'])
# def load_key():
#     if wallet.load_keys():
#         global blockchain
#         blockchain = Blockchain(wallet.public_key, prt)
#         response = {
#             'public_key': wallet.public_key,
#             'private_key': wallet.private_key,
#             'funds': blockchain.get_balance()
#         }
#         return jsonify(response), 201
#     else:
#         response = {
#             'message': 'loading the keys failed.'
#         }
#         return jsonify(response), 500

# @app.route('/balance', methods=['GET'])
# def get_balance():
#     balance = blockchain.get_balance()
#     if balance is not None:
#         response = {
#             'message': 'Fetched balance successfully.',
#             'funds': balance
#         }
#         return jsonify(response), 200
#     else:
#         response = {
#             'message': 'Loading balance failed.',
#             'wallet_set_up': wallet.public_key is not None
#         }
#         return jsonify(response), 500


@app.route('/broadcast-transaction', methods=['POST'])
def broadcast_transaction():
    values = request.get_json()
    if not values:
        response = {'message': 'No data found.'}
        return jsonify(response), 400
    required = ['sender', 'recipient', 'amount', 'signature','memo']
    if not all(key in values for key in required):
        response = {'message': 'Some data is missing'}
        return jsonify(response), 400
    success = blockchain.add_transaction(
        values['recipient'], values['sender'], values['signature'],
        values['amount'], values['memo'], is_receiving=True)
    if success:
        response = {
            'message': 'Successfully added transaction.',
            'transaction': {
                'sender': values['sender'],
                'recipient': values['recipient'],
                'amount': values['amount'],
                'signature': values['signature'],
                'memo': values['memo']
            }
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Creating a transaction failed.'
        }
        return jsonify(response), 500


@app.route('/broadcast-block', methods=['POST'])
def broadcast_block():
    values = request.get_json()
    if not values:
        response = {'message': 'No data found.'}
        return jsonify(response), 400
    if 'block' not in values:
        response = {'message': 'Some data is missing'}
        return jsonify(response), 400
    block = values['block']
    if block['index'] == blockchain.chain[-1].index + 1:
        if blockchain.add_block(block):
            response = {'message': 'Block is successfully added.'}
            return jsonify(response), 201
        else:
            response = {'message': 'Block seems invalid.'}
            return jsonify(response), 409  # stands for confilct
    elif block['index'] > blockchain.chain[-1].index:
        response = {
            'message': 'Blockchain seems to differ from local blockchain.'}
        blockchain.need_resolve_conflicts = True
        return jsonify(response), 200
    else:
        response = {
            'message': 'Blockchain seems to be shorter, block not added.'}
        return jsonify(response), 409


@app.route('/transaction', methods=['POST'])
def add_transaction():

    values = request.get_json()
    if not values:
        response = {
            'message': 'No data found.'
        }
        return jsonify(response), 400
    required_field = ['recipient', 'amount','memo','privateKey','publicKey']
    if not all(field in values for field in required_field):
        response = {
            'message': 'Required data is missing.'
        }
        return jsonify(response), 400
    recipient = values['recipient']
    amount = values['amount']
    memo = values['memo']
    publickey = values['publicKey']
    privatekey = values['privateKey']
    signature = wallet.sign_transaction(publickey, recipient, amount,memo,privatekey)
    success = blockchain.add_transaction(
        recipient, publickey, signature, amount,memo)
    if success:
        response = {
            'message': 'Successfully added transaction.',
            'transaction': {
                'sender': publickey,
                'recipient': recipient,
                'amount': amount,
                'signature': signature
            },
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Creating a transaction failed.'
        }
        return jsonify(response), 500


# @app.route('/mine', methods=['POST'])
# def mine():
#     if blockchain.need_resolve_conflicts:
#         response = {'message': 'Resolve conflicts first, block not added!'}
#         return jsonify(response), 409
#     block = blockchain.mine_block()
#     if block is not None:
#         dict_block = block.__dict__.copy()
#         dict_block['transactions'] = [
#             tx.__dict__ for tx in dict_block['transactions']]
#         response = {
#             'message': 'Block added successfully.',
#             'block': dict_block,
#             'funds': blockchain.get_balance()
#         }
#         return jsonify(response), 201
#     else:
#         response = {
#             'message': 'Adding a block failed.',
#             'wallet_set_up': wallet.public_key is not None
#         }
#         return jsonify(response), 500


@app.route('/resolve-conflicts', methods=['POST'])
def resolve_conflicts():
    replaced = blockchain.resolve()
    if replaced:
        response = {'message': 'Chain was replaced.'}
    else:
        response = {'message': 'Local chain kept!'}
    return jsonify(response), 200


@app.route('/transactions', methods=['GET'])
def get_open_transactions():
    transactions = blockchain.get_open_transactions()
    dict_transactions = [tx.__dict__ for tx in transactions]
    response = {
        'message': 'Fetched transactions successfully.',
        'transactions': dict_transactions
    }
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def get_chain():
    chain_snapshot = blockchain.chain
    dict_chain = [block.__dict__.copy() for block in chain_snapshot]
    for dict_block in dict_chain:
        dict_block['transactions'] = [
            tx.__dict__ for tx in dict_block['transactions']]
    print(dict_chain)
    return jsonify(dict_chain), 200


@app.route('/node', methods=['POST'])
def add_node():
    values = request.get_json()  # return a dictionary
    if not values:
        response = {
            'message': 'No data attached.'
        }
        return jsonify(response), 400
    if 'node' not in values:
        response = {
            'message': 'No node data found.'
        }
        return jsonify(response), 400
    node = values['node']
    # adding node is possible without a wallet, though
    blockchain.add_peer_node(node)
    response = {
        'message': 'Node added successfully.',
        'all_nodes': blockchain.get_peer_nodes()
    }
    return jsonify(response), 201


@app.route('/node/<node_url>', methods=['DELETE'])
def remove_node(node_url):
    if node_url == '' or node_url is None:
        response = {
            'message': 'Node is not found.'
        }
        return jsonify(response), 400
    blockchain.remove_peer_node(node_url)
    response = {
        'message': 'Node is removed successfully.',
        'all_nodes': blockchain.get_peer_nodes()
    }
    return jsonify(response), 200


@app.route('/nodes', methods=['GET'])
def get_nodes():
    nodes = blockchain.get_peer_nodes()
    response = {
        'all_nodes': nodes
    }
    return jsonify(response), 200


if __name__ == '__main__':
    wallet = Wallet()
    blockchain = Blockchain(prt)
    app.run(host='0.0.0.0', port=prt)
