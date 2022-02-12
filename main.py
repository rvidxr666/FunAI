from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route("/")
def root_route():
    return "Hello World!"


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)
