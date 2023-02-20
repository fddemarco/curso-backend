import os, webapp2, jinja2

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

class Rot13():
    def __init__(self, text):
        self.text = list(text)

    def offset(self):
        if self.c.isupper():
            return ord('A')
        else:
            return ord('a')

    def diff(self):
        return ord(self.c) - self.offset()

    def rotate(self):
        return ((self.diff() + 13) % 26) + self.offset()

    def rot13(self):
        return chr(self.rotate())

    def value(self):
        ciphered_text = []
        for c in self.text:
            if c.isalpha():
                self.c = c
                ciphered_text.append(self.rot13())
            else:
                ciphered_text.append(c)
        return "".join(ciphered_text)

class MainPage(Handler):
    def get(self):
        self.render("rot13.html", text="")

    def post(self):
        text = self.request.get("text")
        cipher = Rot13(text)
        self.render("rot13.html", text=cipher.value())
        

app = webapp2.WSGIApplication([('/', MainPage)], debug=True)

