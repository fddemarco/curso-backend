import os, webapp2, jinja2, re
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

def render_str(template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self):
        self._render_text = self.content.replace("\n", "<br>")
        return render_str("post.html", post=self)

class BlogFront(Handler):
    def get(self):
        posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC LIMIT 10")
        self.render("blog-front.html", posts=posts)

class PostPage(Handler):
    def get(self, post_id):
        key = db.Key.from_path("Post", int(post_id))
        post = db.get(key)
        if not post:
            self.error(404)
            return 

        self.render("permalink.html", post=post)

class NewPostPage(Handler):
    def create_blog_page(self, subject, content):
        blog_entry = Post(subject=subject, content=content)
        blog_entry.put()
        self.redirect("/{id}".format(id=blog_entry.key().id()))            

    def get(self):
        self.render("newpost.html")

    def post(self):
        subject, content = self.get_selectors("subject", "content")
        if subject and content:
            self.create_blog_page(subject, content)            
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)


app = webapp2.WSGIApplication([
    ('/', BlogFront), 
    ("/newpost", NewPostPage), 
    (r"/([0-9]+)", PostPage)], 
    debug=True)

