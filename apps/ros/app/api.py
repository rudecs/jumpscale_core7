from flask import Flask
import json

def register_api(namespaces):
    app = Flask('API')
    app.debug = True

    @app.route('/namespace', methods=['GET'])
    def list_namespaces():
        print namespaces
        return json.dumps(namespaces)

    return app

