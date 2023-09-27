from flask import Flask, request, url_for, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user
import os
import math
import random

#Setup
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

#Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')


app.config["SECRET_KEY"] = "Super Secret Key"

#Init
db = SQLAlchemy()

login_manager = LoginManager()
login_manager.init_app(app)

#Globals
current_login = None

#Models
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key=True, nullable=False, autoincrement=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), unique=False, nullable=False)

    def get_profile(self):
        return Profile.query.filter_by(user_id=self.id).first()
    
    def get_bank(self):
        return Bank.query.filter_by(user_id=self.id).first()

class Profile(db.Model):
    id = db.Column(db.Integer,primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.id') ,nullable=False )
    coins = db.Column(db.Integer, nullable=False)
    bucks = db.Column(db.Integer, nullable=False)
    limecoins = db.Column(db.Integer, nullable=False)
    ambinar = db.Column(db.Integer, nullable=False)
    energy = db.Column(db.Integer, nullable=False)
    gillinite = db.Column(db.Integer, nullable=False)
    wins = db.Column(db.Integer, nullable=False)
    losses = db.Column(db.Integer, nullable=False)
    bio = db.Column(db.Text, nullable=True)

    def add_by_string(self, s, val):
        lower_s = s.lower()
        if lower_s == "bucks":
            self.add_bucks(val)
        elif lower_s == "coins":
            self.add_coins(val)
        elif lower_s == "limecoins":
            self.add_limecoins(val)
        elif lower_s == "ambinar":
            self.add_ambinar(val)
        elif lower_s == "gillinite":
            self.add_gillinite(val)

    def sub_energy(self, val):
        self.energy -= val
        if self.energy <= 0:
            self.energy = 0

    def add_energy(self, val):
        self.energy += val
        if self.energy >= 100:
            self.energy = 100

    def add_coins(self, val):
        self.coins += val

    def add_bucks(self, val):
        self.bucks += val

    def add_limecoins(self, val):
        self.limecoins += val

    def add_win(self):
        self.wins += 1

    def add_loss(self):
        self.losses += 1

    def add_ambinar(self, val):
        self.ambinar += val

    def add_gillinite(self, val):
        self.gillinite += val

class Bank(db.Model):
    id = db.Column(db.Integer(),primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer(), nullable=False)
    bucks = db.Column(db.Integer(), nullable=False)



@login_manager.user_loader
def get_user(id):
    return Users.query.get(id)

#Routes
@app.route("/")
def index():
    all_users = Users.query.all()
    return render_template("home.html",all_users=all_users)


@app.route("/casino")
def casino():
    global current_login
    return render_template("casino.html",user=current_login)

"""
<a href="/casino">🎰 Go to Casino</a><br />
<a href="/home">🏠 Go Home</a><br />
<a href="/bank">🏦 Go Bank</a><br />
<a href="/library">📕 Go Library</a><br />
<a href="/xchange">💶 Go Currency Exchange</a><br />
<a href="/store">🏬 Go Store</a><br />
<a href="/airport">✈ Go Airport</a><br />
<a href="/docks">🚢 Go Docks</a><br />
"""

@app.route("/home")
def home():
    global current_login
    return render_template("personal_home.html",user=current_login)

@app.route("/bank")
def bank():
    global current_login
    return render_template("bank.html",user=current_login)

@app.route("/library")
def library():
    global current_login
    return render_template("library.html",user=current_login)

@app.route("/xchange")
def xchange():
    global current_login
    return render_template("xchange.html",user=current_login)

@app.route("/store")
def store():
    global current_login
    return render_template("store.html",user=current_login)

@app.route("/airport")
def airport():
    global current_login
    return render_template("airport.html",user=current_login)

@app.route("/docks")
def docks():
    global current_login
    return render_template("docks.html",user=current_login)

@app.get("/rest")
def rest():
    global current_login
    r_restore = random.randint(1,24)
    r_rest = r_restore * 1.5
    current_login.get_profile().add_energy(math.ceil(r_rest))
    db.session.commit()
    return render_template("rest.html",user=current_login,msg=f'Rest for {r_restore} hours regained {r_rest} ⚡ Energy')

@app.route("/beg")
def beg():
    global current_login
    current_profile = current_login.get_profile()
    if current_profile.energy <= 0:
        return render_template("no_energy.html",user=current_login)
    r_beg = random.randint(1,10)
    
    beg_phrases = ["Here, ya go","Thats pathetic, but here","You poor thing, here you go."]
    currencies = ["bucks","coins","limecoins"]
    r_phrase = random.choice(beg_phrases)
    r_type = random.choice(currencies)
    current_profile.add_by_string(r_type, r_beg)
    current_profile.sub_energy(10)
    db.session.commit()
    return render_template("beg.html",user=current_login,phrase=r_phrase,amt=r_beg,amt_type=r_type)


@app.route("/slots/coins",methods=["GET","POST"])
def slots():
    global current_login
    curr_profile = current_login.get_profile()
    if curr_profile.energy <= 0:
        return render_template("no_energy.html",user=current_login)
    if request.method == "POST":
        bet = int(request.form.get("bet"))
        
        if curr_profile.coins >= bet:
            curr_profile.coins -= bet
            curr_profile.sub_energy(5)
            roll = "2,3,4,5,6,7,8,9,A,J,K,Q,♥,♦,♠,♣".split(",")
            rolls = []
            multi = 0
            did_win = False
            winning = 0
            for i in range(5):
                rolls = []
                for y in range(3):
                    random.seed(None)
                    roll_i = random.choice(roll)
                    rolls.append(roll_i)
                print(f"SPIN {i}/5\t{rolls[0]}|{rolls[1]}|{rolls[2]}")
                
                
                if rolls[0] == rolls[1] == rolls[2]:
                    did_win = True
                    winning += (bet) * 3
                    #print(f"💲💲💲 WIN! WIN! WIN! {rolls[0]}x3 -> {get_value(rolls[0]) * 3}")
                    curr_profile.add_win()
                    multi += 1
                elif rolls[0] == rolls[1]:
                    did_win = True
                    winning += (bet) * 2
                    #print(f"💲 WIN! {rolls[0]} x2 -> {get_value(rolls[0]) * 2}")
                    curr_profile.add_win()
                    multi += 1
                elif rolls[1] == rolls[2]:
                    did_win = True
                    winning += (bet) * 2
                    #print(f"💲 WIN! {rolls[1]} x2 -> {get_value(rolls[1]) * 2}")
                    curr_profile.add_win()
                    multi += 1
                elif rolls[0] == rolls[2]:
                    did_win = True
                    winning += (bet) * 2
                    #print(f"💲 WIN! {rolls[0]} x2 -> {get_value(rolls[0]) * 2}")
                    curr_profile.add_win()
                    multi += 1
            if did_win:
                
                if multi > 1:
                    print(f"Win Multiplier x{multi}")
                    if multi > 3:
                        print(f"+ 4x Bonus +500")
                        winning += 500
                    winning *= multi
                curr_profile.add_coins(winning)
                msg = f"💲💲💲 You Won { winning } coins"
            else:
                msg = f"👎 You lost {bet} coins"
                curr_profile.losses += 1
            db.session.commit()
            return render_template("slot_coin.html",user=current_login,winning=winning,msg=msg)
        else:
            return render_template("slot_coin.html",user=current_login,winning=False,msg=
            f'❌ Not enough coin to bet {bet}')
    elif request.method == "GET":
        return render_template("slot_coin.html",user=current_login,winning=False,msg=False)

@app.get("/profile")
def profile():
    global current_login
    print()
    print("/Profile Debug")
    print(current_login)
    return render_template("profile.html",user=current_login, profile=current_login.get_profile())

@app.get("/user/<name>")
def get_profile(name):
    user = Users.query.filter_by(username=name).first()
    if user:
        profile = user.get_profile()
        return render_template("profile.html",user=user, profile=profile)
    else:
        return f"No User named {name}"

@app.route("/register", methods=["GET", "POST"])
def register():
    global current_login
    if request.method == "POST":
        username=request.form.get('username')
        password=request.form.get('password')
        #Check if user exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template("signup.html",msg=f'❌ Username {username} already exists')
        # Create User
        new_user = Users(
            username=username,
            password=password
        )
        print(f"Register {username} : {password}")
        
        db.session.add(new_user)
        db.session.commit()
        print(f"New User ID: {new_user.id}")
        # Create Profile
        new_profile = Profile(
            user_id = int(new_user.id),
            coins = 0,
            bucks = 0,
            limecoins = 0,
            ambinar = 0,
            gillinite = 0,
            wins = 0,
            losses = 0,
            bio = "",
            energy = 100
        )
        db.session.add(new_profile)
        db.session.commit()
        print(f"Profile ID: {new_profile.id}")
        # Create Bank
        new_bank = Bank(
            user_id = int(new_user.id),
            bucks = 0
        )
        db.session.add(new_bank)
        db.session.commit()
        print(f"Bank ID: {new_bank.id}")

        #Login new user.
        login_user(new_user)
        current_login = new_user
        return redirect(url_for("index"))
    return render_template("signup.html",msg=None)

@app.route("/login", methods=["GET","POST"])
def login():
    global current_login
    if request.method == "POST":
        post_username = request.form.get("username")
        post_password = request.form.get("password")
        print(f"Login {post_username} : {post_password}")
        user = Users.query.filter_by(
            username=post_username
        ).first()
        if user:
            if user.password == post_password:
                login_user(user)
                current_login = user
                return redirect(url_for("index"))
        else:
            return render_template("invalid_login.html",username=post_username)
    return render_template("login.html")

@app.get("/logout")
def logout():
    logout_user()
    return redirect("/")

#Main

print("Initialize DB")
db.init_app(app)
print("Create All...")
with app.app_context():
    db.create_all()

