import os, webapp2, jinja2, re

template_dir = os.path.join(os.path.dirname(__file__),"templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

class InvalidUsername(Exception):
    pass

class InvalidPassword(Exception):
    pass

class InvalidVerify(Exception):
    pass

class InvalidEmail(Exception):
    pass


class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)
	
	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **params):
		self.write(self.render_str(template, **params))

class InputValidator():
    def valid_username(self, username):
        USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
        if not USER_RE.match(username):
            raise InvalidUsername

    def valid_password(self, password):
        PW_RE = re.compile(r"^.{3,20}$")
        if not PW_RE.match(password):
            raise InvalidPassword
        
    def valid_verify(self, password, verify):
        if not password == verify:
            raise InvalidVerify

    def valid_email(self, email):
        EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
        if not EMAIL_RE.match(email):
            raise InvalidEmail

class MainPage(Handler):
    def get(self):
        self.render("signup.html")

    def post(self):
        validator = InputValidator()
        try: 
            username = self.request.get("username")
            validator.valid_username(username)
            
            password = self.request.get("password")
            validator.valid_password(password)

            verify = self.request.get("verify")
            validator.valid_verify(password, verify)

            email = self.request.get("email")
            if email:
                validator.valid_email(email)            
  
            self.redirect("/welcome?username={username}".format(username= username))
        
        except InvalidUsername:
            self.render("signup.html", usrn=username, usrn_error="That's not a valid username.")
        except InvalidPassword:
            self.render("signup.html", usrn=username, password_error="That's not a valid password.")
        except InvalidVerify:
            self.render("signup.html", usrn=username, verify_error="Your passwords didn't match.")
        except InvalidEmail:
            self.render("signup.html", usrn=username, email_error="That's not a valid email.")
        
class WelcomePage(Handler):
    def get(self):
        username = self.request.get("username")
        try:
            InputValidator().valid_username(username)
            self.render("welcome.html", username=username)
        except InvalidUsername:
            self.render("signup.html", usrn=username, usrn_error="That's not a valid username.")


app = webapp2.WSGIApplication([('/', MainPage), ('/welcome', WelcomePage)], debug=True)

