from flask import (Flask, render_template, request, url_for, redirect, flash, session)
from flask_sqlalchemy import SQLAlchemy
from typing import Callable
import pickle
import boto3
import os
from sklearn.linear_model import LinearRegression
import sklearn

# from flask import render_template
# from flask import request

app = Flask(__name__)
housing_prices_model = pickle.load(open(r"ML Models/housing_prices_pred_without_furnishing.pkl", "rb"))
client = boto3.client('rekognition')


class MySQLAlchemy(SQLAlchemy):
    Column: Callable
    String: Callable
    Integer: Callable


app.config['SECRET_KEY'] = 'the random string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///DBs/user.db'
app.config['UPLOAD_FOLDER'] = r"static/Photos"
db = MySQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    surname = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


db.create_all()


@app.route("/logout")
def logout():
    print("user" in session)
    if "user" in session:
        session.pop("user")
        return redirect(url_for("login_page"))
    return redirect(url_for("login_page"))


@app.route("/")
def root_route():
    if "user" not in session:
        return redirect(url_for("login_page"))
    return render_template("main.html")


def query_amazon(file):
    response = client.recognize_celebrities(Image={'Bytes': file.read()})
    if response['CelebrityFaces']:
        person = response['CelebrityFaces'][0]
        name = person["Name"]
        return name
    return "Unindentified"


@app.route("/celebrity", methods=["POST", "GET"])
def celebrity():
    if "user" not in session:
        return redirect(url_for("login_page"))
    if request.method == "POST":
        file = request.files['filename']
        if not file:
            flash("Please select the file!")
            return redirect(url_for("celebrity"))

        name = query_amazon(file)

        if name == "Unindentified":
            result = "Unindentified"
        else:
            result = "This is the " + name

        return render_template("celebrity-result.html", result=result)
    return render_template("celebrity.html")


@app.route("/house-price", methods=["POST", "GET"])
def house_price():
    if "user" not in session:
        return redirect(url_for("login_page"))
    if request.method == "POST":
        input_lst_for_model = []
        string_params = ["mainroad", "guestrooms", "basement", "waterheating", "airconditioning", "pref-area"]
        for param in request.form:
            if not request.form[param]:
                flash("Please fill all the fields!")
                return redirect(url_for("house_price"))
            # if not request.form[param].isnumeric() and request.form[param].lower().strip() not in ["yes", "no"]:
            #     flash("Please input only Yes/No in the Text Fields!")
            #     return redirect(url_for("register_page"))
            if not request.form[param].isnumeric() or param in string_params:
                if request.form[param].lower().strip() == "yes":
                    input_lst_for_model.append(1)
                    continue
                elif request.form[param].lower().strip() == "no":
                    input_lst_for_model.append(0)
                    continue
                else:
                    flash("Please input only Yes/No in the Text Fields!")
                    return redirect(url_for("house_price"))

            input_lst_for_model.append(int(request.form[param]))

        print(input_lst_for_model)
        price = round(housing_prices_model.predict([input_lst_for_model])[0][0])
        result = f"Approximate price is {price}$"
        return render_template("house-result.html", result=result)
        # print(type(request.form["bedrooms"]))
        # print(type(request.form["guestrooms"]))
        # return render_template("house-price.html")
    return render_template("house-price.html")


@app.route("/login", methods=["POST", "GET"])
def login_page():
    if "user" in session:
        return redirect(url_for("root_route"))
    if request.method == "POST":
        print(request.form)
        current_user = User.query.filter_by(email=request.form["email"]).first()

        if current_user:
            if current_user.password == request.form["password"]:
                session["user"] = current_user.email
                print(session)
                return redirect(url_for("root_route"))
            else:
                flash("Incorrect Password!")
                return redirect(url_for("login_page"))
        else:
            flash("Email is not registered!")
            return redirect(url_for("login_page"))

    return render_template("login.html")


@app.route("/register", methods=["POST", "GET"])
def register_page():
    if request.method == "POST":
        params = [request.form["name"], request.form["surname"], request.form["email"], request.form["password"]]
        # print(params)

        for param in params:
            if not param:
                flash("Please fill all the fields!")
                return redirect(url_for("register_page"))

        if User.query.filter_by(email=request.form["email"]).first():
            flash("Email is already registered")
            return redirect(url_for("register_page"))
        else:
            if not User.query.all():
                user_id = 0
            else:
                user_id = User.query.order_by(User.id.desc()).first().id + 1
            new_user = User(id=user_id, name=request.form["name"], surname=request.form["surname"],
                            email=request.form["email"], password=request.form["password"])
            db.session.add(new_user)
            db.session.commit()
            print(User.query.all())
            return redirect(url_for("login_page"))
    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)
