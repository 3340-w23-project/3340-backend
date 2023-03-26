import os
import json
import sys

from api import app, db

# getting config details
with open('config.json') as f:
    data = json.load(f)


# running site
if __name__=='__main__':
    # without an additional arg to run in debug
    if len(sys.argv) < 2:
        print('<< DEBUG >>')
        app.run(debug=True, host="0.0.0.0")

    elif len(sys.argv) > 2:
        print("Too many arguments, exiting")
        exit(1)
    else:
        # run this command with the flag "db-setup" to set up the database
        if sys.argv[1] == 'db-setup':
            print("setting up db ...")
            print("importing models ...")
            from api import models
            print("creating tables...")
            with app.app_context():
                db.create_all()
            print("done!")
            exit(1)
        elif sys.argv[1] == 'prod':
            # run this command with the "prod" flag to run in prod
            print('<< PROD >>')
            os.system(f"gunicorn -b '0.0.0.0:{data['port']}' api:app")
        else:
            print(f"unknown option '{sys.argv[1]}', exiting")
            exit(1)
