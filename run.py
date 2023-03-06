import os
import json
import sys

from backend import app

# getting config details
with open('config.json') as f:
    data = json.load(f)


# running site
if __name__=='__main__':
    # run this command with any additional arg to run in production
    if len(sys.argv) > 1:
        print('<< PROD >>')
        os.system(f"gunicorn -b '0.0.0.0:{data['port']}' backend:app")
    # or just run without an additional arg to run in debug
    else:
        print('<< DEBUG >>')
        app.run(debug=True)
