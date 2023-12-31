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

@app.template_filter('show_online')
def show_online(s):
    if int(s) == 0:
        return "🔴"
    elif int(s) == 1:
        return "🟢"

#Register Jinga2 Templates filters
@app.template_filter('money_format')
def format_test(s):
    ival = int(s)
    perc = 0
    if ival < 1000:
        return f'{ival}'
    elif ival >= 1000 and ival < 1000000:
        perc = math.floor(ival / 1000)
        return f'{perc}K'
    elif ival >= 1000000 and ival < 1000000000:
        perc = math.floor(ival / 1000000)
        return f'{perc}M'
    elif ival >= 10000000000:
        perc = math.floor(ival / 10000000000)
        return f'{perc}B'

#Models
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key=True, nullable=False, autoincrement=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), unique=False, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    online = db.Column(db.Integer,nullable=True)

    def set_online(self):
        self.online = 1

    def set_offline(self):
        self.online = 0

    def get_profile(self):
        return Profile.query.filter_by(user_id=self.id).first()
    
    def get_bank(self):
        return Bank.query.filter_by(user_id=self.id).first()
    
    def get_messages(self):
        return Messages.query.filter_by(user_id=self.id).all()

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
    status = db.Column(db.Text, nullable=False)

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

class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    sender_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Integer, nullable=True)

    def get_author(self):
        return Users.query.filter_by(id=self.sender_id).first()

"""
class ModelName(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
"""


@login_manager.user_loader
def get_user(id):
    return Users.query.get(id)

#Routes
@app.route("/")
def index():
    global current_login
    if current_login:
        return render_template("home.html",messages=current_login.get_messages())
    else:
        logout_user()
        return render_template("home.html",messages=[])

#
#   Messageing
#

@app.get("/messages/delete/<target>")
def delete_target(target):
    i = int(target)
    sel_message = Messages.query.filter_by(id=i).first()
    if sel_message.user_id == current_login.id:
        print(f"Removing {i} -> {sel_message.content}")
        db.session.delete(sel_message)
        db.session.commit()
        return render_template("dashboard.html",user=current_login, profile=current_login.get_profile(),messages=current_login.get_messages())
    else:
        return render_template("dashboard.html",user=current_login, profile=current_login.get_profile(),messages=current_login.get_messages(),msg_error=f'❌ Attempting to remove a message that you didnt send!!!')

@app.get("/send_message/<target>")
def send_message(target):
    global current_login
    target_user = Users.query.filter_by(username=target).first()
    if target_user:
        return render_template("send_message.html",msg=None, user=target_user)
    
    else:
        return render_template("invalid_login.html",msg=f'{target} is not a user')

@app.post("/send_message")
def post_message():
    global current_login
    content = request.form.get("message")
    target_id = request.form.get("target_id")
    print(f"Attempting to send '{content}' to {target_id}")
    target_user = Users.query.filter_by(id=int(target_id)).first()
    if int(target_user.id) == current_login.id:
            return render_template("send_message.html",msg=f'❌ Cant send a message to yourself', user=target_user)
    if target_user:
        new_message = Messages(
            sender_id = current_login.id,
            user_id = int(target_id),
            content = content,
            is_read = 0
        )
        db.session.add(new_message)
        db.session.commit()
        return redirect(f"/user/{target_user.username}")
    else:
        return redirect("/")


#
#   Locations
#

@app.route("/casino")
def casino():
    global current_login
    return render_template("casino.html",user=current_login)

@app.route("/home")
def home():
    global current_login
    return render_template("personal_home.html",user=current_login)

@app.route("/bank")
def bank():
    global current_login
    current_bank = current_login.get_bank()
    return render_template("bank.html",user=current_login, bank=current_bank)

#
#   Bank 
#
@app.post("/bank/withdrawl")
def withdrawl():
    global current_login
    current_profile = current_login.get_profile()
    current_bank = current_login.get_bank()
    amt = int(request.form.get("value"))
    if current_bank.bucks >= amt:
        current_bank.bucks -= amt
        current_profile.bucks += amt;
        db.session.commit()
        return render_template("bank.html",msg=f'🏧 Withdrew {amt} from bank',bank=current_bank)
    else:
        return render_template("bank.html",msg=f'❌ Insufficent Funds',bank=current_bank)
    
@app.post("/bank/deposit")
def deposit():
    global current_login
    current_profile = current_login.get_profile()
    current_bank = current_login.get_bank()
    amt = int(request.form.get("value"))
    if current_profile.bucks >= amt:
        current_profile.bucks -= amt
        current_bank.bucks += amt
        db.session.commit()
        return render_template("bank.html",msg=f'💵 Depositted {amt} Bucks into Account',bank=current_bank)
    else:
        return render_template("bank.html",msg=f'❌ Insufficent Funds',bank=current_bank)


"""
# Test Function to Gernerate random users, limit to 500
@app.get("/test/<num>")
def test_create(num):
    if int(num) > 500:
        num = 500
    for i in range(int(num)):
        name = random.choice(["Anna","Beth","Cindy","Deana","Evin","Felicity","Geany","Adam","Bob","Bill","Charlie","Chad","Derick","Dan","Eric","Unknown","Forever","Together","Slots","Casino","Gambler"])
        r_value = random.randint(1,999999)
        r_name = f'{name}-{r_value}'
        new_user = Users(
            username=r_name,
            password='password',
            email=f'{r_name}@fake.com',
            online=0
        )
        #print(f"Register {username} : {password}")
        
        db.session.add(new_user)
        db.session.commit()
        #print(f"New User ID: {new_user.id}")
        # Create Profile
        new_profile = Profile(
            user_id = int(new_user.id),
            coins = 999,
            bucks = 999,
            limecoins = 999,
            ambinar = 999,
            gillinite = 999,
            wins = 999,
            losses = 999,
            bio = f"I am a Fake User {r_name}",
            status=f"Just Fake",
            energy = 999
        )
        db.session.add(new_profile)
        db.session.commit()
        #print(f"Profile ID: {new_profile.id}")
        # Create Bank
        new_bank = Bank(
            user_id = int(new_user.id),
            bucks = 9999
        )
        db.session.add(new_bank)
        db.session.commit()
    return redirect("/")
"""

@app.route("/library")
def library():
    global current_login
    return render_template("library.html",user=current_login)

@app.route("/xchange")
def xchange():
    global current_login
    return render_template("xchange.html",user=current_login)

@app.get("/xchange/coins/<amt>")
def xchange_coins(amt):
    global current_login
    current_profile = current_login.get_profile()
    val = int(amt)
    if val == 100:
        if current_profile.coins >= 100:
            current_profile.coins -= 100
            current_profile.bucks += 1
        else:
            return redirect("/xchange")
    elif val == 500:
        if current_profile.coins >= 500:
            current_profile.coins -= 500
            current_profile.bucks += 5
        else:
            return redirect("/xchange")
    db.session.commit()
    return redirect("/xchange")
    


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

#
#   Activities
#
@app.get("/rest")
def rest():
    global current_login
    r_restore = random.randint(15,36)
    r_rest = r_restore * 2
    current_login.get_profile().add_energy(math.ceil(r_rest))
    db.session.commit()
    return render_template("rest.html",user=current_login,msg=f'Rest for {r_restore} hours regained {r_rest} ⚡ Energy')

@app.route("/beg")
def beg():
    global current_login
    current_profile = current_login.get_profile()
    if current_profile.energy <= 0:
        return render_template("beg.html",user=current_login,msg_error=f'❌ Out of Energy')
    
    event_chances = [False, True, False, False, False, False, True, False, False, True]
    r_event = random.choice(event_chances)
    if r_event:
        r_beg = random.randint(1,10)
        
        beg_phrases = ["Here, ya go","Thats pathetic, but here","You poor thing, here you go."]
        currencies = ["bucks","coins","limecoins"]
        r_phrase = random.choice(beg_phrases)
        r_type = random.choice(currencies)
        current_profile.add_by_string(r_type, r_beg)
    else:
        beg_phrases = ["Many pass by, but nobody offers you anything","They ignore you"]
        r_phrase = random.choice(beg_phrases)
        r_beg = False
        r_type = False
    current_profile.sub_energy(10)
    db.session.commit()
    if r_event:
        return render_template("beg.html",user=current_login,phrase=r_phrase,amt=r_beg,amt_type=r_type,msg=f'👍 Begging was Successful')
    else:
        return render_template("beg.html",user=current_login,phrase=r_phrase,msg_error=f'👎 Begging gets you nothing')

#
#   Games
#   Slots / Roulette / War
#
@app.route("/slots/coins",methods=["GET","POST"])
def slots():
    global current_login
    msg = None
    msg_error = None
    curr_profile = current_login.get_profile()
    if curr_profile.energy <= 0:
        return render_template("no_energy.html",user=current_login)
    if request.method == "POST":
        bet = int(request.form.get("bet"))
        
        if curr_profile.coins >= bet:
            curr_profile.coins -= bet
            curr_profile.sub_energy(5)
            roll = "2️,3,4,5,6,7,🎱,9,A,j,K,Q,♥,♦,♠,♣".split(",")
            rolls = []
            roll_data = []
            multi = 0
            did_win = False
            winning = 0
            for i in range(5):
                rolls = []
                for y in range(3):
                    random.seed(None)
                    roll_i = random.choice(roll)
                    rolls.append(roll_i)
                roll_data.append(rolls)
                #print(f"SPIN {i}/5\t{rolls[0]}|{rolls[1]}|{rolls[2]}")
                
                
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
                    #print(f"Win Multiplier x{multi}")
                    if multi > 3:
                        #print(f"+ 4x Bonus +500")
                        winning += 500
                    winning *= multi
                curr_profile.add_coins(winning)
                msg = f"💲💲💲 You Won { winning } coins"
            else:
                msg_error = f"👎 You lost {bet} coins"
                curr_profile.losses += 1
            db.session.commit()
            return render_template("slot_coin.html",user=current_login,winning=winning,msg=msg,msg_error=msg_error,data=roll_data)
        else:
            return render_template("slot_coin.html",user=current_login,winning=False,msg_error=
            f'❌ Not enough coin to bet {bet}')
    elif request.method == "GET":
        return render_template("slot_coin.html",user=current_login,winning=False,msg=False)

@app.route("/roll/coins",methods=["GET","POST"])
def rolls():
    global current_login
    if request.method == "POST":
        bet = int(request.form.get("bet"))
        r_color = random.choice(["red","black","red","black","red","black","red","black"])
        r_num = random.randint(2,20)

    elif request.method == "GET":
        return render_template("rollergame.html",user=current_login,winning=False,msg=False)
#
#   Dashboard / Profile
#
@app.get("/dashboard")
def profile():
    global current_login
    if current_login is None:
        logout_user()

        return redirect("/")
    else:
        return render_template("dashboard.html",user=current_login, profile=current_login.get_profile(),messages=current_login.get_messages())

@app.post("/status")
def update_status():
    global current_login
    new_status = request.form.get("status")
    if new_status:
        current_login.get_profile().status = new_status
        db.session.commit()
        return redirect("/dashboard")
    else:
        return redirect("/dashboard")
    
@app.post("/bio")
def update_bio():
    global current_login
    new_bio = request.form.get("bio")
    if new_bio:
        current_login.get_profile().bio = new_bio
        db.session.commit()
        return redirect("/dashboard")
    else:
        return redirect("/dashboard")

#
#   Members
#
@app.get("/members")
def member_view():
    global current_login
    return render_template("members.html",users=Users.query.all())

@app.get("/user/<name>")
def get_profile(name):
    user = Users.query.filter_by(username=name).first()
    if user:
        profile = user.get_profile()
        return render_template("profile.html",user=user, profile=profile)
    else:
        return f"No User named {name}"

#
#   Login / Register / Logout
#

@app.route("/register", methods=["GET", "POST"])
def register():
    global current_login
    if request.method == "POST":
        username=request.form.get('username')
        password=request.form.get('password')
        password2=request.form.get("password2")
        email = request.form.get("email")
        bio = request.form.get("bio")

        #Check if user exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template("signup.html",msg_error=f'❌ Username {username} already exists')
        # Create User
        #Check if passwords match
        if password != password2:
            return render_template("signup.html",msg_error=f'❌ Passwords dont match!')
        new_user = Users(
            username=username,
            password=password,
            email=email,
            online=1
        )
        #print(f"Register {username} : {password}")
        
        db.session.add(new_user)
        db.session.commit()
        #print(f"New User ID: {new_user.id}")
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
            bio = bio,
            status="A new user",
            energy = 100
        )
        db.session.add(new_profile)
        db.session.commit()
        #print(f"Profile ID: {new_profile.id}")
        # Create Bank
        new_bank = Bank(
            user_id = int(new_user.id),
            bucks = 0
        )
        db.session.add(new_bank)
        db.session.commit()
        #print(f"Bank ID: {new_bank.id}")

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
        #print(f"Login {post_username} : {post_password}")
        user = Users.query.filter_by(
            username=post_username
        ).first()
        if user:
            if user.password == post_password:
                
                user.online = 1
                current_login = user
                db.session.commit()
                login_user(user)
                return redirect(url_for("index"))
        else:
            return render_template("invalid_login.html",username=post_username)
    else:
        return render_template("login.html")

@app.get("/logout")
def logout():
    global current_login
    if current_login:
        my_user = Users.query.filter_by(id=current_login.id).first()
        my_user.online = 0
        db.session.commit()
        print(f'Setting status for {current_login.username} to {"Online" if current_login.online == 1 else "Offline"}')
        logout_user()
    
    return redirect("/")

#
#   Main
#
print("Initialize DB")
db.init_app(app)
db.session.expire_on_commit = False
print("Create All...")
with app.app_context():
    db.create_all()
    #Assing Everyone offline
    print(f"Resetting all online statuses")
    all_users = Users.query.all()
    for user in all_users:
        print(f"Settings {user.username} to offline")
        user.online = 0
        #Fix any negatives
        if user.get_profile().coins < 0:
            user.get_profile().coins = 0

    db.session.commit()

#app.run(host="0.0.0.0",port=80)