from flask import Flask, render_template, request , session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug import secure_filename
import json, os, math
from flask_mail import Mail



with open('templates\\config.json',"r") as c:
    params=json.load(c)['params']
    
local_server= True

app = Flask(__name__)
app.secret_key='supreme secret key'
app.config["UPLOAD_FOLDER"]=params['upload_location']
app.config.update(
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT ='465',
    MAIL_USE_SSL =True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)
mail=Mail(app)
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)


class Contacts(db.Model):
    '''srno,name,email,phno,msg,date'''
    srno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),  nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class Posts(db.Model):
    '''srno,name,email,phno,msg,date'''
    srno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), nullable=False)
    subhead = db.Column(db.String(30), nullable=False)
    slug = db.Column(db.String(30), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    imgg = db.Column(db.String(20), nullable=True)



@app.route("/")
def home():
    posts=Posts.query.filter_by().all()
    last=math.ceil(len(posts)/int(params['no_of_post']))
    page=(request.args.get('page'))


    if (not str(page).isnumeric()):
        page=1
    page=int(page)
    posts=posts[(page-1)*int(params["no_of_post"]):(page-1)*int(params["no_of_post"])+int(params["no_of_post"])]

    # pagination 3 kinds
    # 1 at first page (previous = , next=page+1)
    if (page==1):
        prev='#'
        next = "/?page="+ str(page+1)

    # 2 last (prev=pg-1,next= )
    elif (page==last):
        prev="/?page="+ str(page-1)
        next = "#"
    
    # 3 middle p(prev = pg-1, next =pg+1)
    else:
        prev="/?page="+ str(page-1)
        next = "/?page="+ str(page+1)


    
    return render_template("index.html" , params=params, posts=posts, prev=prev, next=next)

@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
    # if logged in ive access
    if ('user' in session and session['user']==params['admin_id']):
        posts=Posts.query.all()
        return render_template('dashboard.html', params=params,posts=posts)

    # if not logged in
    if request.method=="POST":
        username=request.form.get('uname')
        userpass=request.form.get('Password')
        if (username==params["admin_id"] and userpass==params['admin_password']):
            #set session variable
            session['user']= username
            posts=Posts.query.all()
            return render_template('dashboard.html', params=params,posts=posts)
   
    return render_template("login.html" , params=params)




@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if (request.method=="POST"):
        '''ADD ENTRY TO THE DATABASE'''
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        message=request.form.get('message')
        date=datetime.now()

        entry=Contacts(name=name, phone_num=phone, msg=message,date=date, email=email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from '+name, sender=email, recipients=[params['gmail-user']], body=message+ '\n'+phone
        )


    return render_template("contact.html", params=params)


@app.route("/about")
def about():
    return render_template("about.html", params=params)

@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if ('user' in session and session['user']== params['admin_id']):
        if (request.method == "POST"):
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "uploaded successfully"

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
   
    return render_template("post.html", params=params , post=post)

@app.route("/edit/<string:srno>", methods=['GET', 'POST'])
def edit(srno):
    if ('user' in session and session['user']== params['admin_id']):
        if (request.method == 'POST'):
            title_p= request.form.get('title')
            subhead= request.form.get('subhead')
            slug= request.form.get('slug')
            content= request.form.get('content')
            img_f= request.form.get('img_file')
            date=datetime.now()

            if srno=='0':
                post= Posts(title=title_p, slug=slug,subhead=subhead,content=content,imgg=img_f, date=date)
                db.session.add(post)
                db.session.commit()               
            else:
                post= Posts.query.filter_by(srno=srno).first()
                post.title=title_p
                post.slug=slug
                post.subhead=subhead
                post.content=content
                post.imgg=img_f
                post.date=date

                db.session.commit()
                return redirect('/edit/'+srno)


        post= Posts.query.filter_by(srno=srno).first()
        return render_template('edit.html', params=params, srno=srno,post=post)

@app.route("/delete/<string:srno>", methods=['GET', 'POST'])
def delete(srno):
    if ('user' in session and session['user']== params['admin_id']):
        post=Posts.query.filter_by(srno=srno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

app.run(debug=True)
