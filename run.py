import os
import sys
import json
from api import app, db
from api.models import Category, Channel
from dotenv import load_dotenv
load_dotenv()


def create_db():
    print("setting up db ...")
    print("importing models ...")
    from api import models
    print("creating tables...")
    with app.app_context():
        # db.drop_all()
        db.create_all()

        with open('data/categories.json', 'r') as file:
            categories = json.load(file)

            for category_name, channels in categories.items():
                category = Category(name=category_name)
                db.session.add(category)

                for channel in channels:
                    channelItem = Channel(
                        name=channel['name'], category=category, description=channel['desc'])
                    db.session.add(channelItem)
            db.session.commit()
            print("done setting up database!")
            exit(0)


# running site
if __name__ == '__main__':
    # without an additional arg to run in debug
    if len(sys.argv) <= 3:
        if sys.argv[1] == 'prod':
            # run this command with the "prod" flag to run in prod
            if (len(sys.argv) == 3 and sys.argv[2] == 'setup'):
                create_db()
            else:
                print("database already exists, skipping")

            print('<< PROD >>')
            os.system(f"gunicorn -b '0.0.0.0:{os.getenv('PORT')}' api:app")

        elif sys.argv[1] == 'dev':
            if (len(sys.argv) == 3 and sys.argv[2] == 'setup'):
                create_db()
            elif (len(sys.argv) == 3 and sys.argv[2] == 'update'):
                with app.app_context():
                    db.create_all()
            else:
                print("database already exists, skipping")

            print('<< DEBUG >>')
            app.run(debug=True, host="0.0.0.0")
        else:
            print(f"unknown option '{sys.argv[1]}', exiting")
            exit(1)
    else:
        print("Too many arguments, exiting")
        exit(1)
