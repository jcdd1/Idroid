from flask import Flask, render_template, request, redirect, url_for, Response, session
from config import Config
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

@app.route('/', methods=['GET','POST'])
def login():
    return render_template("auth/login.html")
    # if request.method =='POST':
    #     user = User(request.form['username'], request.form['password'])
    #     logged_user =  ModelUser.login(db,user)
    #     if logged_user != None:
    #         return redirect(url_for('index'))
    #     else:
    #         print("no existes")
    #     #print(request.form['username'])
    #     return render_template("auth/login.html")
    # else:
    #     return render_template("auth/login.html")

if __name__=='__main__':
    app.run(host='0.0.0.0', port = '8080')