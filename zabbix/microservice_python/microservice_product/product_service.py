from flask import Flask, jsonify

app = Flask(__name__)

products = []

@app.route('/product', methods=['GET'])
def get_products():
    return jsonify(products)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    # app.run(port=5000)
