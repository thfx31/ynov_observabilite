from flask import Flask, jsonify, request

app = Flask(__name__)

orders = []

@app.route('/order', methods=['GET', 'POST'])
def order_management():
    if request.method == 'GET':
        return jsonify(orders)

    elif request.method == 'POST':
        new_order = request.json
        orders.append(new_order)
        return jsonify(new_order), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    # app.run(port=5000)
