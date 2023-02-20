import os, webapp2, jinja2, re, hashlib, hmac
from google.appengine.ext import db

SECRET = b"key"
template_dir = os.path.join(os.path.dirname(__file__),"templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def hash_str(s):
    return hmac.new(SECRET, s.encode()).hexdigest()

def make_secure(s):
    return "{s}|{hash}".format(s=s, hash=hash_str(s))

def verify_hash(h):
    if h:
        s, delimiter, hash = h.rpartition("|")
        if make_secure(s) == h:
            return s 
    return ""

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **params):
        self.write(self.render_str(template, **params))

    def get_selectors(self, *selectors):
        return [self.request.get(s) for s in selectors]

def render_str(template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

class MainPage(Handler):
    def get(self):
        self.response.headers["Content-Type"] = "text/plain"
        visits_cookie = self.request.cookies.get("visits")
        
        visits_value = verify_hash(visits_cookie)
        visits = int(visits_value) if visits_value.isdigit() else 0

        if visits > 1000:
            self.write("Wow, you are amazing!")
        else:
            self.write("You've been here {count} times!".format(count=visits))
        
        updated_visits = str(visits + 1)
        self.response.headers.add_header(
            'Set-Cookie', "visits={visits_cookie}".format(
                visits_cookie= make_secure(updated_visits)
                )
            )

    def post(self):
        pass

app = webapp2.WSGIApplication([
    ('/', MainPage)], 
    debug=True)
