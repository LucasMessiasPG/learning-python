import bottle 

import pymongo 
import cgi 
import re 
import datetime 
import random 
import hmac 
import user 
import sys 

from pymongo import MongoClient
from bson.objectid import ObjectId

connection = MongoClient('localhost',27017)
db = connection.blog
posts = db.posts

# insere a entrada de dados do blog e retorna um permalink
def insert_entry(title, post, tags_array, author, cat):
    print "inserindo entrada de dados no blog", title, post

    exp = re.compile('\W') # combinar qualquer coisa que nao alfanumerico
    whitespace = re.compile('\s')
    temp_title = whitespace.sub("_",title)
    permalink = exp.sub('', temp_title)

    post = {
        "title": title,
        "author": author,
        "body": post,
        "permalink":permalink,
        "tags": tags_array,
        "category": cat,
        "date": datetime.datetime.utcnow()
    }

    try:
        posts.insert(post)
        print "Inserido post"
    except:
        print "Erro ao inserir post"
        print "Erros inesperado:", sys.exc_info()[0]

    return permalink


@bottle.route('/')
def blog_index():
    l = []

    username = login_check()  # verifique se o usuario esta	 logado

    if (username == None): 
        print "welcome: can't identify user...redirecting to signup" 
        bottle.redirect("/signup") 

    cursor = posts.find().sort('date', direction=-1).limit(10)

    for post in cursor:

        if ('tags' not in post): 
            post['tags'] = []

        if ('comments' not in post): 
            post['comments'] = []   
        
        l.append({
            'title':post['title'], 
            'body':post['body'], 
            'post_date':post['date'],
            'permalink':post['permalink'],
            'tags':post['tags'],
            'author':post['author'],
            'category':post.get('category'),
            'comments': post['comments']
        })

    return bottle.template('blog_template', dict(myposts=l ,username=username))


@bottle.get('/newpost')
def get_newpost():
    username = login_check()  # verifique se o usuario esta	 logado

    if (username == None): 
        print "welcome: can't identify user...redirecting to signup" 
        bottle.redirect("/signup") 

    cursor = db.categories.find({})
    categories = []

    for post in cursor:
        if ('category' not in post): 
            post['category'] = ""

        categories.append({
            'category':post['category'],
            '_id': post['_id']
        })

    return bottle.template("newpost_template", dict(categories = categories, subject="", body="",errors="", tags="", username=username))
 

@bottle.post('/newpost')
def post_newpost():
    title = bottle.request.forms.get("subject")
    post = bottle.request.forms.get("body")
    tags = bottle.request.forms.get("tags")
    cat = bottle.request.forms.get("category")

    username = login_check()  # verifique se o usuario esta	 logado

    if (username == None): 
        print "welcome: can't identify user...redirecting to signup" 
        bottle.redirect("/signup") 

    if (title == "" or post == ""):
        errors="Post must contain a title and blog entry"
        return bottle.template("newpost_template", dict(subject=cgi.escape(title, quote=True), body=cgi.escape(post, quote=True), tags=tags, errors=errors))

    tags = cgi.escape(tags) 
    tags_array = extract_tags(tags)

    # Entrada de dados, insira SCAPE
    escaped_post = cgi.escape(post, quote=True)

    # substituir alguns <p> para as quebras de paragrafo
    newline = re.compile('\r?\n')
    formatted_post = newline.sub("<p>",escaped_post)

    permalink = insert_entry(title, formatted_post, tags_array, username, cat)

    # redireciona para post criado
    bottle.redirect("/post/" + permalink)


@bottle.get("/post/<permalink>")
def show_post(permalink="notfound"):
    permalink = cgi.escape(permalink)

    username = login_check()  # verifique se o usuario esta	 logado

    if (username == None): 
        print "welcome: can't identify user...redirecting to signup" 
        bottle.redirect("/signup") 

    # determina requisica do json
    path_re = re.compile(r"^([^\.]+).json$")

    print "about to query on permalink = ", permalink
    post = posts.find_one({'permalink':permalink})


    if post == None:
        bottle.redirect("/post_not_found")

    print "date of entry is ", post['date']

    # Formata Data
    post['date'] = post['date'].strftime("%A, %B %d %Y at %I:%M%p")

    #inicializacao dos campos do formulario  para adicionar de comentarios
    comment = {}
    comment['name'] = ""
    comment['email'] = ""
    comment['body'] = ""

    # print(post['category'])
    return bottle.template("entry_template", dict(post=post, username= username, errors="", comment=comment))


# Extrai a tag do elemento de formulario tags. 
def extract_tags(tags): 
    whitespace = re.compile('\s') 

    nowhite = whitespace.sub("",tags) 
    tags_array = nowhite.split(',') 

    # limpando 
    cleaned = [] 
    for tag in tags_array: 
        if (tag not in cleaned and tag != ""): 
            cleaned.append(tag) 

    return cleaned

# usado para processar um comentario em um post de blog
@bottle.post('/newcomment')
def post_newcomment():
    name = bottle.request.forms.get("commentName")
    email = bottle.request.forms.get("commentEmail")
    body = bottle.request.forms.get("commentBody")
    permalink = bottle.request.forms.get("permalink")

    permalink = cgi.escape(permalink)

    post = posts.find_one({'permalink':permalink})

    if post == None:
        bottle.redirect("/post_not_found")

    errors=""
    if (name == "" or body == ""):

        # Formata data
        post['date'] = post['date'].strftime("%A, %B %d %Y at %I:%M%p")

        # Inicializa Comentarios
        comment = {}
        comment['name'] = name
        comment['email'] = email
        comment['body'] = body

        errors="Post must contain your name and an actual comment."
        print "newcomment: comment contained error..returning form with errors"
        return bottle.template("entry_template", dict(post=post, username="indefinido", errors=errors, comment=comment))

    else:

        comment = {}
        comment['author'] = name
        if (email != ""):
            comment['email'] = email
            
        comment['body'] = body

    try:

        last_error = posts.update({'permalink':permalink}, {'$push':{'comments':comment}}, upsert=False )

        print "about to update a blog post with a comment"

    except:
        print "Could not update the collection, error"
        print "Unexpected error:", sys.exc_info()[0]


        print "newcomment: added the comment....redirecting to post"

    bottle.redirect("/post/"+permalink)


@bottle.get("/post_not_found") 
def post_not_found(): 
    return "Desculpe, post nao encontrado" 

@bottle.route('/tag/<tag>')
def posts_by_tag(tag="notfound"):
    tag = cgi.escape(tag)
    cursor = posts.find({'tags':tag}).sort('date', direction=-1).limit(10)
    l=[]

    for post in cursor:
        post['date'] = post['date'].strftime("%A, %B %d %Y at %I:%M%p") 
        if ('tags' not in post):
            post['tags'] = [] 
        if ('comments' not in post):
            post['comments'] = []

        l.append({'title':post['title'], 'body':post['body'], 'post_date':post['date'],
        'permalink':post['permalink'],
        'tags':post['tags'],
        'author':post['author'],
        'category':post.get("category"),
        'comments':post['comments']})

    return bottle.template('blog_template', dict(myposts=l,username="indefinido"))


@bottle.route('/category/<cat>')
def posts_by_category(cat="notfound"):
    cat = cgi.escape(cat)
    cursor = posts.find({'category':cat}).sort('date', direction=-1).limit(10)
    l=[]

    for post in cursor:
        post['date'] = post['date'].strftime("%A, %B %d %Y at %I:%M%p") 
        if ('tags' not in post):
            post['tags'] = [] 
        if ('comments' not in post):
            post['comments'] = []

        l.append({'title':post['title'], 'body':post['body'], 'post_date':post['date'],
        'permalink':post['permalink'],
        'tags':post['tags'],
        'author':post['author'],
        'category':post.get("category"),
        'comments':post['comments']})

    return bottle.template('blog_template', dict(myposts=l,username="indefinido"))


@bottle.get('/signup') 
def present_signup(): 

    username = bottle.request.forms.get("username") 

    if (username != None): 
            print "user logged" 
            return bottle.redirect("/") 

    return bottle.template("signup", dict(username="", password="", password_error="", email="", username_error="", email_error="", verify_error =""))

@bottle.post('/signup') 
def process_signup(): 

    email = bottle.request.forms.get("email") 
    username = bottle.request.forms.get("username") 

    if (username == None): 
            print "welcome: can't identify user...redirecting to signup" 
            return bottle.redirect("/signup") 

    password = bottle.request.forms.get("password") 
    verify = bottle.request.forms.get("verify") 

    errors = {
        'username':cgi.escape(username), 
        'email':cgi.escape(email),
        'username_error': '',
    } 

    if (user.validate_signup(username, password, verify, email, errors)): 
        if(not user.newuser(connection, username, password, email)):
            print(errors)
            errors['username_error'] = "Username already in use. Please choose another" 
            return bottle.template("signup",  errors)

        session_id = user.start_session(connection, username) 
        print session_id 
        cookie= user.make_secure_val(session_id) 
        bottle.response.set_cookie("session",cookie) 
        return bottle.redirect("/welcome") 

@bottle.get("/welcome") 
def present_welcome(): 
    # check for a cookie, if present, then extract value 

    username = login_check() 

    if (username == None): 
        print "welcome: can't identify user...redirecting to signup" 
        bottle.redirect("/signup") 

    return bottle.template("welcome", {'username':username})

def login_check(): 
    #connection = pymongo.Connection(connection_string, safe=True) 
    cookie = bottle.request.get_cookie("session") 

    if (cookie == None): 
        print "no cookie..." 
        return None 

    else: 
        session_id = user.check_secure_val(cookie) 

    if (session_id == None): 
        print "no secure session_id" 
        return None 

    else: 
        # look up username record 
        session = user.get_session(connection, session_id) 
        if (session == None): 
            return None 

    return session['username'] 


@bottle.get('/logout')
def process_logout():


    cookie = bottle.request.get_cookie("session")

    if (cookie == None):
        print "no cookie..."
        bottle.redirect("/signup")

    else:
        session_id = user.check_secure_val(cookie)

        if (session_id == None):
            print "no secure session_id"
            bottle.redirect("/signup")

        else:
            # remove the session

            user.end_session(connection, session_id)

            print "clearing the cookie"

            bottle.response.set_cookie("session","")


            bottle.redirect("/signup")


@bottle.get('/login')
def present_login():
    return bottle.template("login", dict(username="", password="", login_error=""))


@bottle.post('/login')
def process_login():


    username = bottle.request.forms.get("username")

    if (username == None): 
        print "welcome: can't identify user...redirecting to signup" 
        bottle.redirect("/signup") 

    password = bottle.request.forms.get("password")

    print "user submitted ", username, "pass ", password

    userRecord = {}
    if (user.validate_login(connection, username, password, userRecord)):
        session_id = user.start_session(connection, username)
        if (session_id == -1):
            bottle.redirect("/internal_error")

        cookie = user.make_secure_val(session_id)

        bottle.response.set_cookie("session", cookie)

        bottle.redirect("/welcome")

    else:
        return bottle.template("login", dict(username=cgi.escape(username), password="", login_error="Invalid Login"))


@bottle.get('/categories') 
def present_signup(): 

    username = login_check()

    print(username)

    if (username == None): 
        print "welcome: can't identify user...redirecting to signup" 
        bottle.redirect("/signup") 

    cursor = db.categories.find({})
    categories = []

    for post in cursor:
        if ('category' not in post): 
            post['category'] = ""

        categories.append({
            'category':post['category'],
            '_id': post['_id']
        })

    return bottle.template("categories", dict(username = username, categories = categories))


@bottle.post('/create_category') 
def present_signup(): 

    username = bottle.request.forms.get("username") 

    if (username != None): 
            print "user logged" 
            return bottle.redirect("/") 

    cat = bottle.request.forms.get("category")

    db.categories.insert({ "category" : cat})

    return bottle.redirect("/categories")


@bottle.post('/remove_category') 
def present_signup(): 

    username = bottle.request.forms.get("username") 

    if (username != None): 
            print "user logged" 
            return bottle.redirect("/") 

    cat_id = bottle.request.forms.get("category_id")
    print(cat_id)
    db.categories.remove({ "_id" : ObjectId(cat_id) })

    return bottle.redirect("categories")

bottle.debug(True) 
bottle.run(host='localhost', port=8082)