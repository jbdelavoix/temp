from flask import Flask, redirect, render_template, request, session, url_for
from ldap3 import ALL, Connection, Server

app = Flask(__name__)
app.secret_key = "bgrvefdsbhvrgdfshbvregdfshgrvtfdsc"

LDAP_SERVER = "ldap://ldap.forumsys.com"
LDAP_BASE_DN = "dc=example,dc=com"
LDAP_PEOPLE_DN = LDAP_BASE_DN


def ldap_authenticate(username, password):
    user_dn = f"uid={username},{LDAP_PEOPLE_DN}"
    try:
        server = Server(LDAP_SERVER, get_info=ALL)
        conn = Connection(server, user=user_dn, password=password, auto_bind=True)
        return conn
    except Exception:
        return None


@app.route("/", methods=["GET"])
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = ldap_authenticate(username, password)
        if conn:
            session["username"] = username
            conn.search(LDAP_BASE_DN, f"(uid={username})", attributes=["cn"])
            try:
                groups = conn.entries[0]["cn"]
            except IndexError:
                groups = []
            session["groups"] = [str(g) for g in groups]
            return redirect(url_for("profile"))
        else:
            error = "Identifiants incorrects"
    return render_template("login.html", error=error)


@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template(
        "profile.html", username=session["username"], groups=session.get("groups", [])
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
