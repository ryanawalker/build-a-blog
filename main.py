#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def get_posts(limit, offset):
    return list(db.GqlQuery("SELECT * FROM Posts ORDER BY created DESC LIMIT " + str(limit) + " OFFSET " + str(offset)))

class Handler(webapp2.RequestHandler):
    def write(self, *args, **kwargs):
        self.response.out.write(*args, **kwargs)

    def render_str(self,template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kwargs):
        self.write(self.render_str(template, **kwargs))

class Posts(db.Model):
    title = db.StringProperty(required = True)
    body = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

class Index(Handler):
    def get(self):
        self.redirect("/blog")

class Blog(Handler):
    page_size = 5

    def get(self):
        page = self.request.get('page')
        page_offset = 0
        page = page and int(page)
        if page:
            page_offset = (page - 1) * self.page_size
        else:
            page = 1

        posts = get_posts(self.page_size, page_offset)
        
        previous_page = None
        if page > 1:
            previous_page = page - 1

        next_page = None
        if len(posts) == self.page_size and Posts.all().count() > page_offset + self.page_size:
            next_page = page + 1

        self.render('blog.html', page=page, posts=posts, previous_page=previous_page, next_page=next_page)


class NewPost(Handler):
    def render_form(self, title="", body="", error=""):
        self.render("newpost.html", title=title, body=body, error=error)
    
    def get(self):
        self.render_form()

    def post(self):
        title = self.request.get('title')
        body = self.request.get('body')

        if title and body:
            p = Posts(title=title, body=body)
            p.put()
            id_number = p.key().id()
            self.redirect("/blog/" + str(id_number))
        else:
            error = "Posts need both a subject and a body!"
            self.render_form(title, body, error)

class ViewPostHandler(Handler):
    def render_blog(self, id=0):
        posts = Posts.get_by_id(id)
        self.render("post.html", posts=posts)

    def get(self, id):
        posts = Posts.get_by_id(int(id))
        if not posts:
            self.render("notfound.html")
        else:
            self.render_blog(int(id))


app = webapp2.WSGIApplication([('/', Index), 
                               ('/blog', Blog), 
                               ('/newpost', NewPost),
                               webapp2.Route('/blog/<id:\d+>', ViewPostHandler)], 
                               debug=True)
