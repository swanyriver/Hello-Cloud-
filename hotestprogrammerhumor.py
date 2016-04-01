import os
import urllib
import json
import jinja2
import webapp2
import datetime
from google.appengine.ext import ndb
from google.appengine.api import urlfetch

LISTINGS_KEY = 'listings'
API_URL = 'https://www.reddit.com/r/ProgrammerHumor/hot.json?limit=1'

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions=['jinja2.ext.autoescape'],
  autoescape=True)

class FixedOffset(datetime.tzinfo):
  """Fixed offset in minutes east from UTC."""

  def __init__(self, offset, name):
    self.__offset = datetime.timedelta(minutes = offset)
    self.__name = name

  def utcoffset(self, dt):
    return self.__offset

  def tzname(self, dt):
    return self.__name

  def dst(self, dt):
    return datetime.timedelta(0)
PDT = FixedOffset(-7 * 60, "PDT")

class Listing (ndb.Model):
  thumbnail = ndb.StringProperty(indexed=False)
  score = ndb.IntegerProperty(indexed=False)
  url = ndb.StringProperty(indexed=False)
  title = ndb.StringProperty(indexed=False)
  timestampString = ndb.StringProperty(indexed=False)
  timeAdded = ndb.DateTimeProperty(auto_now_add=True)

class errorListing():
  thumbnail = "img/reddit503.jpg"
  score = 0
  url = ""
  title = "Server Error Please Try Again later"
  timestampString = ""

def getListing():
  listing = Listing(parent=ndb.Key('Listing', LISTINGS_KEY))

  #make call to reddit api
  result = urlfetch.fetch(API_URL)
  if result.status_code != 200: return None

  #extract values form JSON
  listingJSON = json.loads(result.content)
  listingJSON = listingJSON['data']['children'][0]['data']

  listing.thumbnail = listingJSON['thumbnail']
  listing.score = listingJSON['score']
  listing.url = listingJSON['url']
  listing.title = listingJSON['title']
  listing.timestampString = datetime.datetime.now(PDT).strftime("%d %b %Y %I:%M %p")

  return listing



class MainPage(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/html'

    Hotestlisting = getListing() or errorListing()

    listingQuery = Listing.query(ancestor=ndb.Key('Listing',LISTINGS_KEY)).order(-Listing.timeAdded)
    listings = listingQuery.fetch()

    templateVars = {
      'Hotestlisting':Hotestlisting,
      'listings':listings
    }

    template = JINJA_ENVIRONMENT.get_template('index.html')
    self.response.write(template.render(templateVars))

class grab(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'

    Hotestlisting = getListing()
    if not Hotestlisting:
      self.response.set_status(503)
      self.response.write("Unable to retrieve listing")
      return
    Hotestlisting.put()
    self.response.set_status(200)
    self.response.write("Saved listing to datastore")
    return

app = webapp2.WSGIApplication([
  ('/', MainPage), ('/grab/', grab)
], debug=True)
