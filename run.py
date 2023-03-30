import os
import json
import sys

from api import app, db
from api.models import Category, Channel

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

                # Hardcode some categories and channels here
                categories = {
                    "First Year": ['COMP-1000', 'COMP-1047', 'COMP-1400', 'COMP-1410'],
                    "Second Year": ['COMP-2057', 'COMP-2067', 'COMP-2077', 'COMP-2097', 'COMP-2120', 'COMP-2140', 'COMP-2310', 'COMP-2540', 'COMP-2560', 'COMP-2650', 'COMP-2660', 'COMP-2707', 'COMP-2750', 'COMP-2800', 'COMP-2980',],
                    "Third Year": ['COMP-3057', 'COMP-3077', 'COMP-3110', 'COMP-3150', 'COMP-3220', 'COMP-3300', 'COMP-3340', 'COMP-3400', 'COMP-3500', 'COMP-3520', 'COMP-3540', 'COMP-3670', 'COMP-3680', 'COMP-3710', 'COMP-3750', 'COMP-3760', 'COMP-3770', 'COMP-3980',],
                    "Fourth Year": ['COMP-4110', 'COMP-4150', 'COMP-4200', 'COMP-4220', 'COMP-4250', 'COMP-4400', 'COMP-4500', 'COMP-4540', 'COMP-4670', 'COMP-4680', 'COMP-4700', 'COMP-4730', 'COMP-4740', 'COMP-4750', 'COMP-4760', 'COMP-4770', 'COMP-4800', 'COMP-4960', 'COMP-4970', 'COMP-4980', 'COMP-4990']
                }

                for category_name, channel_names in categories.items():
                    category = Category(name=category_name)
                    db.session.add(category)

                    for channel_name in channel_names:
                        channel = Channel(name=channel_name, category=category)
                        db.session.add(channel)

                db.session.commit()

            print("done!")
            exit(1)
        elif sys.argv[1] == 'prod':
            # run this command with the "prod" flag to run in prod
            print('<< PROD >>')
            os.system(f"gunicorn -b '0.0.0.0:{data['port']}' api:app")
        else:
            print(f"unknown option '{sys.argv[1]}', exiting")
            exit(1)