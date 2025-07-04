from flask import Flask, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Pour stocker la session

# Configuration OIDC
app.config['OIDC_CLIENT_ID'] = 'your-client-id'
app.config['OIDC_CLIENT_SECRET'] = 'your-client-secret'
app.config['OIDC_DISCOVERY_URL'] = 'https://your-idp.com/.well-known/openid-configuration'
app.config['OIDC_REDIRECT_URI'] = 'http://localhost:5000/auth/callback'

oauth = OAuth(app)
oidc = oauth.register(
    name='oidc',
    client_id=app.config['OIDC_CLIENT_ID'],
    client_secret=app.config['OIDC_CLIENT_SECRET'],
    server_metadata_url=app.config['OIDC_DISCOVERY_URL'],
    client_kwargs={
        'scope': 'openid email profile',
    }
)

@app.route('/')
def homepage():
    user = session.get('user')
    if user:
        return f"Hello, {user['name']} (<a href='/logout'>Logout</a>)"
    return '<a href="/login">Login with SSO</a>'

@app.route('/login')
def login():
    return oidc.authorize_redirect(redirect_uri=app.config['OIDC_REDIRECT_URI'])

@app.route('/auth/callback')
def callback():
    token = oidc.authorize_access_token()
    user_info = oidc.parse_id_token(token)
    session['user'] = {
        'name': user_info.get('name'),
        'email': user_info.get('email'),
        'sub': user_info.get('sub')
    }
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    # Optionnel : rediriger vers le logout du fournisseur OIDC
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
