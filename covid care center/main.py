
from flask import Flask,redirect,render_template,request,flash,session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_login import login_required,login_user,logout_user,LoginManager,login_manager,current_user
from flask_session import Session
from werkzeug.security import generate_password_hash,check_password_hash
from flask.helpers import url_for
from flask_mail import Mail,Message
import json
import smtplib, ssl


# my database connection
local_server=True
app=Flask(__name__)
app.secret_key="sairam"

#loading configuration details into params
with open('config.json','r') as c:
    params=json.load(c)["params"]

#config mail app
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    # MAIL_USE_TLS=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)

mail=Mail(app)


#this is for getting the unique user access
login_manager=LoginManager(app)
login_manager.login_view='login'

#database configuarion 
# app.config["SQLALCHEMY_DATABASE_URI"]="mysql://username:password@localhost/databasename" 
app.config["SQLALCHEMY_DATABASE_URI"]="mysql://root:@localhost/covid"
db=SQLAlchemy(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Test(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(50))

class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    srfid=db.Column(db.String(20),unique=True)
    email=db.Column(db.String(100))
    dob=db.Column(db.String(1000))

class Hospitaluser(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(20),unique=True)
    email=db.Column(db.String(100))
    password=db.Column(db.String(1000))


class Hospitaldata(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(20),unique=True)
    hname=db.Column(db.String(100))
    beds=db.Column(db.Integer)
    icubeds=db.Column(db.Integer)
    hicubeds=db.Column(db.Integer)
    ventilators=db.Column(db.Integer)

class Bookingpatient(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    srfid=db.Column(db.String(20))
    bedtype=db.Column(db.String(50))
    hcode=db.Column(db.String(20))
    spo2=db.Column(db.Integer)
    pname=db.Column(db.String(50))
    pphone=db.Column(db.String(12))
    paddress=db.Column(db.String(100))

class Trig(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(20))
    beds=db.Column(db.Integer)
    hicubeds=db.Column(db.Integer)
    icubeds=db.Column(db.Integer)
    ventilators=db.Column(db.Integer)
    querys=db.Column(db.String(50))
    date=db.Column(db.String(50))


#routes
@app.route("/")
def home():
    return render_template("index.html")

#user signup
@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method=="POST":
        srfid=request.form.get('srf')
        email=request.form.get('email')
        dob=request.form.get('dob')
        # print(srfid,email,dob)

        encpassword=generate_password_hash(dob)

        #validations
        user=User.query.filter_by(srfid=srfid).first()
        emailUser=User.query.filter_by(email=email).first()

        if user or emailUser:
            flash("Email or srfid is already taken","warning")
            return render_template("usersignup.html")
        new_user=db.engine.execute(f"INSERT INTO `user` (`srfid`,`email`,`dob`) VALUES('{srfid}','{email}','{encpassword}') ")

        flash("Signup Successfull ! Please login now ","success")
        return render_template("userlogin.html")

    return render_template("usersignup.html")


#user login
@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=="POST":
        srfid=request.form.get('srf')
        dob=request.form.get('dob')
        user=User.query.filter_by(srfid=srfid).first()
        # print(user)

        if user and check_password_hash(user.dob,dob):
            login_user(user)
            flash("Login Successfull","info")
            return render_template("index.html")
        else:
            flash("Invalid Credentials","danger")
            return render_template("userlogin.html")
       
    return render_template("userlogin.html")


#user logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout Successfull","warning")
    return redirect(url_for('login')) 

#admin login
@app.route('/admin',methods=['POST','GET'])
def admin():
    if request.method=="POST":
        username=request.form.get('username')
        password=request.form.get('password')

        if(username==params['username'] and password==params['password']):
            print(params['username'])
            print(params['password'])
            session['user']=username
            flash("login success","info")
            return render_template("addHospital.html")
        else:
            flash("Invalid Credentials","danger")
            return render_template("adminlogin.html")
        
    return render_template("adminlogin.html")

#admin logout
@app.route("/logoutadmin")
def logoutadmin():
    session.pop('user')
    flash('Admin is logged out from the session','primary')
    return redirect('/admin')


#adding hospital user by admin login 
@app.route('/addHospital',methods=['POST','GET'])
def addHospital():
    if('user' in session and session['user']==params['username']):
        if request.method=="POST":
            hcode=request.form.get('hcode')
            hcode=hcode.upper()
            email=request.form.get('email')
            password=request.form.get('password')

            encpassword=generate_password_hash(password)

            #validations
            huser=Hospitaluser.query.filter_by(hcode=hcode).first()
            emailUser=Hospitaluser.query.filter_by(email=email).first()

            if huser or emailUser:
                flash("Email or hcode is already taken","warning")
                return render_template("addHospital.html")
            db.engine.execute(f"INSERT INTO `hospitaluser` (`hcode`,`email`,`password`) VALUES('{hcode}','{email}','{encpassword}') ")

            msg = Message(
                'Covid Care Center',
                sender =params['gmail-user'],
                recipients = [email]
               )
            msg.body = f"Thanks for choosing us!\n\nYour login credentials are as follows :\nUsername : {email}\nPassword : {password}\nHospital code : {hcode}\n\nDo not share your password\n\nThank You!"
            mail.send(msg)


            # mail.send_message('Covid Care Center',sender=params['gmail-user'],recipients=email)

            flash("Hospital added successfully !","success")
            return redirect('/admin')

        return render_template("addHospital.html")
    else:
        flash("Admin login is required to add hospital user","warning")
        return redirect('/admin')


#hospital login
@app.route('/hospitallogin',methods=['POST','GET'])
def hospitallogin():
    if request.method=="POST":
        email=request.form.get('email')
        password=request.form.get('password')
        user=Hospitaluser.query.filter_by(email=email).first()
        # print(user)

        if user and check_password_hash(user.password,password):
            login_user(user)
            flash("Login Successfull","info")
            return render_template("hospitaldata.html")
        else:
            flash("Invalid Credentials","danger")
            return render_template("hospitallogin.html")
       
    return render_template("hospitallogin.html")

@app.route('/addhospitaldata',methods=['POST','GET'])
def addhospitaldata():
    if request.method=="POST":
        hcode=request.form.get('hcode')
        hname=request.form.get('hname')
        beds=request.form.get('beds')
        icubeds=request.form.get('icubeds')
        hicubeds=request.form.get('hicubeds')
        ventilators=request.form.get('vent')
        hcode=hcode.upper()
        huser=Hospitaluser.query.filter_by(hcode=hcode).first()
        hduser=Hospitaldata.query.filter_by(hcode=hcode)

        if hduser.first():
            for record in hduser:
                hname=record.hname
                hcode=record.hcode
                beds=record.beds
                icubeds=record.icubeds
                hicubeds=record.hicubeds
                ventilators=record.ventilators
    
                flash("Data is already inserted ! You can update it...","primary")
                return render_template("hospitaldata.html", hcode=hcode,hname=hname,beds=beds,icubeds=icubeds,hicubeds=hicubeds,ventilators=ventilators)
        elif huser:
            db.engine.execute(f"INSERT INTO `hospitaldata` (`hcode`,`hname`,`beds`,`icubeds`,`hicubeds`,`ventilators`) VALUES('{hcode}','{hname}','{beds}','{icubeds}','{hicubeds}','{ventilators}')")
            flash("Data added successfully !","success")
            return render_template("hospitaldata.html", hcode=hcode, hname=hname,beds=beds,icubeds=icubeds,hicubeds=hicubeds,ventilators=ventilators)
        else:
            flash("Hospital code doesn't exist","warning")
            return render_template("hospitaldata.html")
    return render_template("hospitaldata.html")


@app.route('/hedit/<string:id>',methods=['POST','GET'])
@login_required
def hedit(id):
    hname=''
    hcode=0
    beds=0
    icubeds=0
    hicubeds=0
    ventilators=0
    hduser=Hospitaldata.query.filter_by(hcode=id)
    
    for record in hduser:
        hname=record.hname
        hcode=record.hcode
        beds=record.beds
        icubeds=record.icubeds
        hicubeds=record.hicubeds
        ventilators=record.ventilators


    if request.method=="POST":
        hcode=request.form.get('hcode')
        hname=request.form.get('hname')
        beds=request.form.get('beds')
        icubeds=request.form.get('icubeds')
        hicubeds=request.form.get('hicubeds')
        ventilators=request.form.get('vent')

        db.engine.execute(f"UPDATE `hospitaldata` SET `hcode`='{hcode}',`hname`='{hname}',`beds`='{beds}',`icubeds`='{icubeds}',`hicubeds`='{hicubeds}',`ventilators`='{ventilators}' WHERE `hospitaldata`.`id`={id}) ")
        flash("Slot updated","success")
        return render_template("hospitaldata.html")
    return render_template("hedit.html",hcode=hcode,hname=hname,beds=beds,icubeds=icubeds,hicubeds=hicubeds,ventilators=ventilators)


@app.route('/hdelete/<string:id>',methods=['POST','GET'])
@login_required
def hdelete(id):
    db.engine.execute(f"DELETE FROM `hospitaldata` WHERE `hospitaldata`.`id`={id}")
    flash("Date Deleted","danger")
    return redirect("/addhospitaldata")


@app.route("/pdetails",methods=['GET'])
@login_required
def pdetails():
    code=current_user.srfid
    print(code)
    data=Bookingpatient.query.filter_by(srfid=code).first()
   
    
    return render_template("details.html",data=data)



@app.route("/slotbooking",methods=['POST','GET'])
@login_required
def slotbooking():
    query=db.engine.execute(f"SELECT * FROM `hospitaldata` ")
    if request.method=="POST":
        srfid=request.form.get('srfid')
        bedtype=request.form.get('bedtype')
        hcode=request.form.get('hcode')
        spo2=request.form.get('spo2')
        pname=request.form.get('pname')
        pphone=request.form.get('pphone')
        paddress=request.form.get('paddress')  
        check2=Hospitaldata.query.filter_by(hcode=hcode).first()
        if not check2:
            flash("Hospital Code not exist","warning")

        code=hcode
        dbb=db.engine.execute(f"SELECT * FROM `hospitaldata` WHERE `hospitaldata`.`hcode`='{code}' ")        
        bedtype=bedtype
        seat=0
        if bedtype=="normalbed":       
            for d in dbb:
                seat=d.beds
                print(seat)
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.beds=seat-1
                db.session.commit()
                
            
        elif bedtype=="hicubed":      
            for d in dbb:
                seat=d.hicubeds
                print(seat)
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.hicubeds=seat-1
                db.session.commit()

        elif bedtype=="icubed":     
            for d in dbb:
                seat=d.icubeds
                print(seat)
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.icubeds=seat-1
                db.session.commit()

        elif bedtype=="ventilatorbed": 
            for d in dbb:
                seat=d.ventilators
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.ventilators=seat-1
                db.session.commit()
        else:
            pass

        check=Hospitaldata.query.filter_by(hcode=hcode).first()
        if(seat>0 and check):
            res=Bookingpatient(srfid=srfid,bedtype=bedtype,hcode=hcode,spo2=spo2,pname=pname,pphone=pphone,paddress=paddress)
            db.session.add(res)
            db.session.commit()
            flash("Slot is Booked kindly Visit Hospital for Further Procedure","success")
        else:
            flash("Something Went Wrong","danger")
    
    return render_template("booking.html",query=query)


#route for testing 
@app.route("/test")
def test():
    try:
        a=Test.query.all()
        print(a)
        return f'My database is Connected {a.id},{a.name}'
    except Exception as e:
        print(e)
        return f'My database is not connected{e}' 

app.run(debug=True)


