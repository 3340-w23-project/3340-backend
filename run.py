import os
import sys
from api import app, db
from api.models import Category, Channel
from dotenv import load_dotenv
from flask_migrate import Migrate
load_dotenv()

migrate = Migrate(app, db)

def setup_db():
    import json
    print("setting up db ...")
    print("creating tables...")
    with app.app_context():
        db.create_all()

        # check if the categories table is empty
        if Category.query.count() == 0:
            print("populating categories table ...")
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
                print("done populating categories table!")
        else:
            print(
                "categories table is not empty, run with the \"update\" argument to update the database")
            print("skipping categories table population ...")
        print("done setting up database!")


def reset_db():
    print("resetting db ...")
    with app.app_context():
        db.drop_all()
        db.session.commit()
        print("done resetting db!")


def reset_categories():
    with app.app_context():
        print("resetting categories ...")
        db.session.query(Category).delete()
        db.session.commit()
        print("done resetting categories!")


# running the app
if __name__ == '__main__':
    if len(sys.argv) > 2:
        print("Too many arguments, exiting")
        exit(1)
    else:
        if len(sys.argv) == 2:
            # The app is running in prod or we are in the reloaded process
            if os.getenv('ENVIRONMENT') == "prod" or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
                if sys.argv[1] == 'setup':
                    setup_db()
                elif sys.argv[1] == 'reset':
                    reset_db()
                    setup_db()
                elif sys.argv[1] == 'update':
                    reset_categories()
                    setup_db()
                else:
                    print("unknown argument, exiting")
                    exit(1)

        # PROD
        if os.getenv('ENVIRONMENT') == "prod":
            print('<< PRODUCTION >>')
            os.system(f"gunicorn -b '0.0.0.0:{os.getenv('PORT')}' api:app")

        # DEV
        elif os.getenv('ENVIRONMENT') == 'dev':
            print('<< DEVELOPMENT >>')
            app.run(debug=True, host="0.0.0.0")

        else:
            print(f"unknown environment: {os.getenv('ENVIRONMENT')}")
            exit(1)
