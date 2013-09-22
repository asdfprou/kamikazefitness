# NIMBUS 1.0

# Created by Jon H.M. Chan
# me [at] jonhmchan [dot] com

# This software is free to use under the MIT License.

import logging
import tornado.auth
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
from tornado.options import define, options

import math

import datetime
import time
from time import time
import pytz
from pytz import timezone

import os.path

import json
import urllib

import pymongo
import asyncmongo

import base64
import random
from random import randrange
import hashlib

import re

from pprint import pprint

from tornado import ioloop

# Import SMTP Client
from tornadomail.message import EmailMessage, EmailMultiAlternatives
from tornadomail.backends.smtp import EmailBackend

define("port", default=8888, help="run on the given port", type=int)

# SSH
# Sometimes you'll get an RSA fingerprint error when you try to push to heroku
# Make sure that
# =======================================================================
# ssh-keygen -t rsa -C "youremail@somewhere.com" -f  ~/.ssh/id_rsa_heroku
# ssh-add ~/.ssh/id_rsa_heroku
# heroku keys:add ~/.ssh/id_rsa_heroku.pub

# MongoDB
# =======================================================================
# ADD YOUR MONGO COMMAND HERE TO COPY INTO THE TERMINAL FOR EASY ACCESS (Copy from MongoHQ admin tab)
# mongo paulo.mongohq.com:10005/app18253122 -u <user> -p<password>
# Pusher credentials

class Application(tornado.web.Application):

    def __init__(self, debug = False):
        handlers = [
            # Home page
            (r"/", MainHandler),
            (r"/facebook", FacebookHandler),
            (r"/logout", LogoutHandler),
            (r"/test", TestHandler),
            (r"/update", UpdateHandler),
            (r"/user", UserHandler)
        ]
        settings = dict(
            cookie_secret="/Vo=",
            login_url="",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            facebook_api_key="",
            facebook_secret="",
            debug=debug
        )

        # Define cron
        self.cron = CronHandler()

        # logging.info("Static URL: {}".format(settings['static_path']))
        tornado.web.Application.__init__(self, handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):

    response = {}

    def _async(self, response = False, error = False):
        if error:
            print(error)

    def _respond(self):
        self.write(tornado.escape.json_encode(self.response))
        print tornado.escape.json_encode(self.response)
        self.finish()
    @property
    def db(self):
        if not hasattr(self, '_db'):
            self._db = asyncmongo.Client(pool_id='test_pool', host='paulo.mongohq.com', port=10005, dbuser="heroku", dbpass="hello!", dbname="app18253122", maxcached=10, maxconnections=1000)
        return self._db

    @property
    def http(self):
        self._http = tornado.httpclient.AsyncHTTPClient()
        return self._http

    def generate_id(self):
        return hashlib.sha224(str(random.random())).hexdigest()[0:11];

    def wilson(self, upvotes = 0, downvotes = 0):
        u = int(upvotes)
        d = int(downvotes)

        n = u + d
        p = float(u) / float(n) if n > 0 else 0
        z = 1.64485
        wilson = float((p+z*z/(2*n)-z*math.sqrt((p*(1-p)+z*z/(4*n))/n))/(1+z*z/n)) if n > 0 else 0
        wilson = round(wilson*1000000000000.0)/1000000000000.0
        return wilson

class FacebookHandler(BaseHandler, tornado.auth.FacebookGraphMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("code", False):
            print self.get_argument("code")
            self.get_authenticated_user(
                                        redirect_uri='http://www.thedeckgame.com/login',
                                        client_id=self.settings["facebook_api_key"],
                                        client_secret=self.settings["facebook_secret"],
                                        code=self.get_argument("code"),
                                        callback=self.async_callback(self._on_login)
                                        )
        else:
            self.authorize_redirect(redirect_uri='http://www.thedeckgame.com/login',
                              client_id=self.settings["facebook_api_key"],
                              extra_params={"scope": "user_birthday, email, publish_actions, offline_access"}
                              )

    def _on_login(self, user):
        self.user = user
        self.facebook_request(
                              "/me",
                              access_token=self.user['access_token'],
                              callback=self._on_me
                              )

    def _on_me(self, user):
        self.user["email"] = user["email"]
        self.facebook_request(
                              "/"+self.user["id"]+"/friends",
                              access_token=self.user['access_token'],
                              callback=self._on_friends
                              )

    def _on_friends(self, response):
        friends = []
        for friend in response["data"]:
            friends.append(friend["id"])
        self.user["friends"] = friends
        self.db.users.find_one({'id': self.user["id"]}, callback=self._on_user)

    def _on_user(self, response = False, error = False):
        if error:
            print error
        if response:
            # Existing user
            id = str(response["id"])
        else:
            user = {
                    "name": str(self.user["name"]),
                    "id": str(self.user["id"]),
                    "email": str(self.user["email"]),
                    "bot": False,
                    "upvotes": 0,
                    "created": time(),
                    "downvotes": 0,
                    "hand": []
            }
            self.db.users.update({"id": user["id"]}, user, upsert=True, callback=self._async)
            id = str(user["id"])


        self.clear_cookie("user")
        self.set_secure_cookie("user", id)

        self.clear_cookie("friends")
        self.set_secure_cookie("friends", tornado.escape.json_encode(self.user["friends"]))
        self.redirect("/" if response else "/resetdeck?id="+id)

class LogoutHandler(BaseHandler):
    def get(self):
        self.redirect("/")

class MainHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        self.id = self.get_secure_cookie("user")
        if self.get_argument("id", False) : self.set_secure_cookie("user", self.id)
        self.games = []
        print self.id
        if self.id:
            self.db.users.find_one({"id": self.id}, callback=self._on_user)
        else:
            self.render("index.html")

    def _on_user(self, response = False, error = False):
        if error:
            print error
            self.write(error)
            self.finish()
        if response:
            self.user = {
                         "id": response["id"],
                         "name": response["name"],
                         "karma": response["upvotes"]
                         }
            self.id = self.user["id"]
            self.db.games.find({"players": {"$in": [str(self.id)]}}, callback = self._on_games)
        else:
            self.redirect("/logout")

    def _on_games(self, response = False, error = False):
        if error:
            print error
        if response:
            print response
            for game in response: self.games.append({"id": game["id"], "text": game["id"]})
        else:
            print "No games found"
        self.render("index.html",
                    user = str(tornado.escape.json_encode(self.user)).replace('"', "?"),
                    games = str(tornado.escape.json_encode(self.games)).replace('"', "?"))


class TestHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        self.db.users.find({}, callback=self._on_find)

    def _on_find(self, response = False, error = False):
        result = []
        for obj in response:
            result.append(obj)
        self.write(str({"data": result}))
        self.finish()

class UpdateHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        self.objects = False
        self.database = self.db.users
        if False:
            self.database.find({}, limit=10000, callback=self._on_find)
        else:
            self.finish()

    def _on_find(self, response = False, error = False):
        if error:
            print "ERROR"
            print error
        if response:
            if not self.objects: self.objects = response
        if len(self.objects)>0:
            x = self.objects.pop()
            self.database.update({"id": x["id"]}, {"$set": {"upvotes": 0}}, upsert=False, callback=self._on_find if len(self.objects)>0 else self._on_finish)

    def _on_finish(self, response = False, error = False):
        self.write("Finished updating")
        self.finish()

class UserHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        self.db.users.find({}, callback=self._on_find)

    def _on_find(self, response = False, error = False):
        if error:
            print "ERROR"
            print error
        else:
            result = []
            for obj in response:
                result.append(obj)
            self.write(str({"data": result}))
            self.finish()

class CronHandler(BaseHandler):
    response = {}

    root = "http://localhost:8888" if False else "http://www.thedeckgame.com"

    @property
    def http(self):
        self._http = tornado.httpclient.AsyncHTTPClient()
        return self._http

    def __init__(self):
        self.cycles = 0

        # Winning proportion
        self.threshold = 0.30

    def maintain(self):
        # This is the main method that is fired every second.
        self.cycles += 1

# Main Runtime
def main():
    tornado.options.parse_command_line()
    logging.info("starting webserver on 0.0.0.0:%d" % tornado.options.options.port)
    print("Web server started again at "+str(datetime.datetime.now()))
    app = Application(debug = (True if options.port==8888 else False))
    app.listen(options.port)

    # Create IOLoop
    mainloop = tornado.ioloop.IOLoop

    # Create scheduled cron jobs
    interval_ms = 1000
    scheduler = tornado.ioloop.PeriodicCallback(app.cron.maintain, interval_ms)
    scheduler.start()
    app.cron.maintain()

    # Start main loop
    mainloop.instance().start()


if __name__ == "__main__": main()
