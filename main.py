import webapp2
from webapp2_extras import sessions
from jinja2 import Environment, FileSystemLoader
from google.appengine.ext import ndb
import random
import os


env = Environment(
    loader=FileSystemLoader('html'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class GhostName(ndb.Model):
    ghostName = ndb.StringProperty()
    firstName = ndb.StringProperty()
    lastName = ndb.StringProperty()
    email = ndb.StringProperty()
    isTaken = ndb.BooleanProperty()


# taken from the webapp2 extra session example
class BaseHandler(webapp2.RequestHandler):
    # override dispatch
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            # dispatch the main handler
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()


class OverviewPage(BaseHandler):
    def get(self):

        if not self.session.get('loggedIn'):
            self.session['loggedIn'] = False

        query = GhostName.query()
        allGhostNames = []
        for c in query:
            allGhostNames.append({
                'ghostname': c.ghostName,
                'isTaken': c.isTaken,
                'firstName': c.firstName,
                'lastName': c.lastName,
                'email': c.email,
            })

        self.session['allGhostNames'] = allGhostNames
        template = env.get_template('Mainpage.html')
        self.response.write(template.render(ghost=self.session.get('allGhostNames'), loggedIn=self.session.get('loggedIn')))


class FormPage(BaseHandler):
    def get(self):
        template = env.get_template('Nameform.html')
        self.response.write(template.render(firstname=self.session.get('firstName'), lastname=self.session.get('lastName'),
                                            email=self.session.get('email'),loggedIn=self.session.get('loggedIn')))


class SubmitName(BaseHandler):
    def post(self):
        self.session['firstName'] = self.request.get('firstName')
        self.session['lastName'] = self.request.get('lastName')
        self.session['email'] = self.request.get('email')
        return self.redirect('/showname')


class ShowName(BaseHandler):
    def get(self):
        logged = False
        if self.session.get('loggedIn'):
            logged = True

        template = env.get_template('ChooseName.html')
        query = GhostName.query()
        ghost = []
        for c in query:
            if not c.isTaken:
                ghost.append({
                    'ghostname': c.ghostName,
                    'isTaken': c.isTaken,
                    'firstName': c.firstName,
                    'lastName': c.lastName,
                    'email': c.email,
                })

        namechoice = []
        if len(ghost) >=3:
            for i in range(3):
                num = random.randint(0, len(ghost))
                namechoice.append(ghost[num])
        elif len(ghost) <3:
            for i in len(ghost):
                namechoice.append(ghost[i])

        self.response.write(template.render(firstName=self.session.get('firstName'),
                                            lastName=self.session.get('lastName'),
                                            ghost=namechoice,
                                            changename=logged))


class SelectName(BaseHandler):
    def get(self):
        self.session['loggedIn'] = True
        query = GhostName.query()
        ghost = []
        for c in query:
            if c.ghostName == self.request.get('ghostname'):
                c.isTaken = True
                c.email = self.session.get('email')
                c.firstName = self.session.get('firstName')
                c.lastName = self.session.get('lastName')
                c.put()

        return self.redirect('/')


class ChangeName(BaseHandler):
    def get(self):
        query = GhostName.query()

        for c in query:
            if c.email == self.session.get('email'):
                c.isTaken = False
                c.put()

        query = GhostName.query()
        for c in query:

            if c.ghostName == self.request.get('ghostname'):
                c.isTaken = True
                c.email = self.session.get('email')
                c.firstName = self.session.get('firstName')
                c.lastName = self.session.get('lastName')
                c.put()

        return self.redirect('/')



config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'vVw9bsRtOA',
}

app = webapp2.WSGIApplication([
    webapp2.Route('/', OverviewPage),
    webapp2.Route('/nameform', FormPage),
    webapp2.Route('/sumbitname', SubmitName),
    webapp2.Route('/showname', ShowName),
    webapp2.Route('/selectname', SelectName),
    webapp2.Route('/changename', ChangeName)
], debug=True, config=config)


def main():
    from paste import httpserver
    httpserver.serve(app, host='127.0.0.1', port='8080')


if __name__ == '__main__':
    main()