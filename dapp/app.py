from types import MethodType
from flask import Flask, app, session, render_template,redirect
from flask.globals import request
from flask.helpers import url_for
from flask_cors import CORS
from flask_pymongo import PyMongo
import bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from datetime import timedelta

import requests
from util import verfiyKey,SendOtp
import os

app = Flask(__name__)
CORS(app)

app.secret_key = 'secret'

app.config['MONGO_DBNAME'] = 'users'
app.config['MONGO_URI'] = os.environ.get('mongoURI')
mongo = PyMongo(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sdb.sqlite3'
app.config['SESSION_TYPE'] = 'sqlalchemy'

sdb = SQLAlchemy(app)

app.config['SESSION_SQLALCHEMY'] = sdb

sess = Session(app)



@app.route('/')
def index():
    if 'emailSession' in session:
        return 'You are logged in as ' + session['emailSession']

    return 'pleas login'


@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    if request.method == 'POST':
        users = mongo.db.users

        existing_user = users.find_one({'_id':request.form['email']})
        if existing_user is None:
            if not verfiyKey(request.form['pKey']):
                return 'invalid key'
            
            # users.insert({'name' : request.form['userName'], 'email': request.form['email'], 'pKey':request.form['pKey'] , 'password' : hashpass})
            session.permanent = True
            app.permanent_session_lifetime = timedelta(minutes=15)
            session['otp'] = SendOtp(request.form['email'],'Verify')
            session['name'] = request.form['userName']
            session['email'] = request.form['email']
            session['pKey'] = request.form['pKey']
            session['password'] = request.form['pass']

            return redirect(url_for('verifyOtp'))
    
        return 'email used'


@app.route('/otp',methods=['GET','POST'])
def  verifyOtp():
    if request.method == 'GET': 
        return render_template('otp.html')
    
    if request.method == 'POST':
        print(session['otp']) 
        if 'otp' not in session:
            return 'somthing fishy'
        if session['otp'] == request.form['otp']:
            users = mongo.db.users
            hashpass = bcrypt.hashpw(session['password'].encode("utf-8"), salt=bcrypt.gensalt())
            users.insert({'name' : session['name'], '_id': session['email'], 'pKey':session['pKey'] , 'password' : hashpass})
            session.pop('name')
            session.pop('pKey')
            session.pop('password')
            session.pop('otp')
            session['emailSession'] = session['email'] 
            session.pop('email')
            return redirect(url_for('index'))
        else:
            return redirect(url_for('verifyOtp'))


@app.route('/login',methods=['GET','POST'])
def login(): 
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        users = mongo.db.users
        login_user = users.find_one({'_id' : request.form['email']})
        if login_user:
            passVerif = bcrypt.checkpw(request.form['pass'].encode("utf-8"), login_user['password'])
            # print(request.form['pass'] + ' from dbb] '+ login_user['password'])
            if (passVerif == True):
                session.permanent = True
                app.permanent_session_lifetime = timedelta(minutes=60)
                session['emailSession'] = request.form['email']
                return 'logged in'
            else:
                return 'pass invalid'
        else:
            return "invalid"


@app.route('/forgotPass',methods=['GET','POST'])
def forgotPass():
    if request.method == 'GET':
        return render_template('forgotpass-new.html')
    elif request.method == 'POST':
        if 'email' in request.form:
            users = mongo.db.users
            existing_user = users.find_one({'_id':request.form['email']})
            if existing_user :
                session['resetotp'] = SendOtp(request.form['email'],'Reset')
                session['forgotemail'] = request.form['email']
                return render_template('reset-otp.html')
            else:
                return render_template('user-not-exist.html')
        if  request.form['resetotp']:
            if session['resetotp'] == request.form['resetotp']:
                users = mongo.db.users
                if users.update_one({'_id':session['forgotemail']},{"$set": { 'password': bcrypt.hashpw(request.form['newpass'].encode("utf-8"), salt=bcrypt.gensalt())}}) :
                    return 'pass updated'
                else:
                    return 'somthing went wrong'
            else:
                return render_template('reset-pass-wrong-otp.html')

        


@app.route('/new-poll',methods=['GET','POST'])
def new_poll():
    if request.method == 'GET':
        return render_template('create-poll.html')
    if request.method == 'POST':
        file = request.files['file']    
        file.save('/home/abhi/votechain/candidateIMG/' +file.filename)
        return 'succ'

if __name__ == '__main__' :
    app.run(debug=False,port=5001)
