import os, webapp2, jinja2, re, hashlib, hmac, string, random
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__),"templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

SECRET = b"lLDlx\r1\x0cK+v$!3j`*ZEUUqB%0K(j\x0cn@L"

def separator():
    return "|"

def hash_str(s):
    return hmac.new(SECRET, s.encode()).hexdigest()

def make_secure(s):
    return "{s}{sep}{hash}".format(s=str(s), hash=hash_str(str(s)), sep=separator())

def verify_hash(h, sep):
    if h:
        cookie_val, _ = decode_hash(h, sep)
        if compare_hashes(h, make_secure(cookie_val)):
            return cookie_val

def compare_hashes(hash, verify_hash):
    return hmac.compare_digest(hash.encode(), verify_hash.encode())

def make_salt():
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(32))

def validate_pw(username, password, verify_hash, salt):
    pw_hash = make_hash_for_user(username, password, salt)
    return compare_hashes(pw_hash, verify_hash)

def make_hash_for_user(name, password, salt):
    hash = hashlib.sha256(name + password + salt).hexdigest()
    return hash

def make_pw_hash(name, password):
    salt = make_salt()
    pw_hash = make_hash_for_user(name, password, salt)
    return "{hash}{sep}{salt}".format(hash=pw_hash, salt=salt, sep=separator())

def decode_hash(h, sep):
    v1,_,v2 = h.rpartition(sep)
    return v1,v2


class User(db.Model):
    username = db.StringProperty(required=True)
    password_hash = db.StringProperty(required=True)
    email = db.StringProperty()

    @classmethod
    def find_user_by_name(cls, username):
        query = cls.all().filter("username =", username)
        user = query.get()
        return user 

    @classmethod
    def user_exists(cls, username):
        user = cls.find_user_by_name(username)
        return user is not None

    @classmethod
    def get_username_of(cls, user_id):
        return cls.get_by_id(user_id).get_username()

    @classmethod
    def register(cls, username, password, email=None):
        pw_hash = make_pw_hash(username, password)
        user = cls(username=username, password_hash=pw_hash, email=email)
        user.put()
        return user.key().id()

    @classmethod
    def login(cls, username, password):
        user = cls.find_user_by_name(username)
        
        if user:
            verify_hash, salt = user.get_password_hash()
            if validate_pw(username, password, verify_hash, salt):
                return  user.key().id()

    def pw_separator(self):
        return separator()

    def get_password_hash(self):
        return decode_hash(self.password_hash, self.pw_separator())
    
    def get_username(self):
        return self.username


class Handler(webapp2.RequestHandler):
    def cookie_separator(self):
        return separator()

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **params):
        self.write(self.render_str(template, **params))

    def get_selectors(self, *selectors):
        return [self.request.get(s) for s in selectors]

    def set_cookie_as(self, name, value):
        secured_value = make_secure(value)
        self.response.headers.add_header("Set-Cookie", 
                                        "{name}={value}; Path=/".format(name=name, value=secured_value))

    def read_cookie(self, cookie_name):
        secured_cookie = self.request.cookies.get(cookie_name)
        return verify_hash(secured_cookie, self.cookie_separator())

    def login_as_user(self, user_id):
            self.set_cookie_as("user_id", user_id)
            self.redirect("/welcome")

    def logout(self):
        self.response.headers.add_header("Set-Cookie", "user_id=; Path=/")
        self.redirect("/signup")
        

class SignupValidator():
    def __init__(self,username, password, verify, email):
        self.username = username
        self.password = password 
        self.verify = verify 
        self.email = email
        self.errors = {} 

    def validate_username(self):
        re_username = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
        if not re_username.match(self.username):
            self.errors["invalid_username"] = "Invalid username!"
        else:
            if User.user_exists(self.username):
                self.errors["invalid_username"] = "That user already exists!"
    
    def validate_password(self):
        password_re = re.compile(r"^.{3,20}$")
        if not password_re.match(self.password):
            self.errors["invalid_password"] = "Invalid password!"          

    def validate_verify(self):
        if self.password != self.verify:
            self.errors["invalid_verify"] = "Your passwords didn't match!"            

    def validate_email(self):
        email_re = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
        if self.email and not email_re.match(self.email):
            self.errors["invalid_email"] = "Invalid email!"

    def value(self):
        self.validate_username()
        self.validate_password()
        self.validate_verify()
        self.validate_email()
        return self.errors

class SignupPage(Handler):
    def get(self):
        self.render("signup.html")        
 
    def post(self):
        input = self.get_selectors("username", "password", "verify", "email")
        errors = SignupValidator(*input).value()
        username, password, _, email = input 
        if not(errors):
            user_id = User.register(username=username, password=password, email=email)
            self.login_as_user(user_id)
        else:            
            self.render("signup.html", username=username, **errors)

class WelcomePage(Handler):
    def get(self):
        user_id = self.read_cookie("user_id")
        if user_id:
            username = User.get_username_of(int(user_id))
            self.render("welcome.html", username=username)
        else: # Invalid cookie
            self.logout()

class LoginPage(Handler):
    def get(self):
        self.render("login.html")

    def post(self):
        username, password = self.get_selectors("username", "password")
        user_id = User.login(username, password)
        if user_id:
                self.login_as_user(user_id)
        else:
            self.render("login.html", username=username, error="Invalid access. Username or password is incorrect.")

class LogoutPage(Handler):
    def get(self):
        self.logout()


app = webapp2.WSGIApplication([
    ('/signup', SignupPage),
    ('/welcome', WelcomePage),
    ('/login', LoginPage),
    ('/logout', LogoutPage)
    ], 
    debug=True)
