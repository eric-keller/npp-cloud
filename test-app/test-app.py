import os
from flask import Flask
app = Flask(__name__)

myhost = os.uname()[1]

@app.route('/health')
def health_check():
   print("HC")
   return 'ok'

@app.route('/hello')
def hello_name():
   return 'Hello %s!' % myhost

if __name__ == '__main__':
   host = "0.0.0.0"
   port = 5000
   print(f"Running REST server on {host}:{port}")
   app.run(host=host, port=port, debug=True)
