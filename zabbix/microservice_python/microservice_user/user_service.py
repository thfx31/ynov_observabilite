from flask import Flask, jsonify, request

app = Flask(__name__)

users = []

@app.route('/user', methods=['GET', 'POST', 'DELETE'])
def user_management():
    if request.method == 'GET':
        return jsonify(users)

    elif request.method == 'POST':
        new_user = request.json
        users.append(new_user)
        return jsonify(new_user), 201

    elif request.method == 'DELETE':
        user_id = request.args.get('id')
        for user in users:
            if user['id'] == user_id:
                users.remove(user)
                return '', 204
        return jsonify({'error': 'User not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    # app.run(port=5000)
