import os, webapp2, jinja2
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__),"templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

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
        
class Art(db.Model):
    title = db.StringProperty(required=True)
    art = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

class MainPage(Handler):
    def render_front(self, **kw):
        art_posts = db.GqlQuery("SELECT * FROM Art ORDER BY created DESC")        
        list_arts = [art_post for art_post in art_posts]
        self.render("ascii-chan-front.html", art_posts=list_arts, len=len(list_arts), **kw)

    def get(self):
        self.render_front()

    def post(self):
        title, art = self.get_selectors("title", "art")
        if title and art:
            art_post = Art(title=title, art=art)
            art_post.put() # DB won't update until it receives another query.
            art_post.put()

            self.redirect("/")
        else:
            error ="We need a title and some artwork!"
            self.render_front(title=title, art=art, error=error)
        

app = webapp2.WSGIApplication([('/', MainPage)], debug=True)
