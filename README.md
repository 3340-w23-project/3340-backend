# uhelp-backend

Backend of the COMP-3340 final project "UHelp" - written in Flask.

## Prerequesites

- You must have a modern version of Python 3 (3.6+ should suffice)
- The production version of this application works best on Linux/Unix machines (due to the use of gunicorn). Development is still fine on Windows, though

## Setup

1. Install dependencies

```sh
pip3 install -r requirements.txt
```

2. Copy the example config (and modify it how you like)

```sh
cp example-config.json config.json
```

3. Run the database setup script

```sh
python3 run.py db-setup
```

4. Run the application (dev mode)

```sh
python3 run.py
```

## Important Endpoints

### `/signup` and `/login`

These endpoints are both used for authentication, and each expect the same inputs. They also both expect POST requests. The body of the request should look like the following:

```json
{
    "username":"username_here",
    "password":"password_here"
}
```

`/signup` will return a success message when successful, and `/login` will return the JWT token when successful

### `/logout`

This will simply clear the JWT cookies and return a success message

### `/ping` and `/identity`

These are useful when testing the api in development. `/ping` will simply return a success message, and `/identity` will return back your username.

Note that `/identity` requires a valid JWT token. You can set it in your request by adding the `Authorization` header with the value `Bearer <token>`, replacing `<token>` with your actual JWT token. Since authentication is required for `/identity`, it's very useful for testing to see if your front end is handling authentication correctly.
