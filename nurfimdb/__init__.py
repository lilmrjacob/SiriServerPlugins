#!/usr/bin/python
#nurf-imdb.py

#
# This process of enhancing plugins has been performed by Twisted.
#
# Unmerged versions of these plugins may function differently or lack some modification.
# All original headers and licensing information are labeled by the derived plugin name.
#
# IMDb Plugin for SiriServer
# by Casey (Nurfballs) Mullineaux 
# Version 0.2.1

# Download: 
#   - https://github.com/Nurfballs/SiriServer-IMDb

# Pre-requisites:
#   - Requires IMDbPy. 
#       Install IMDbPY (sudo apt-get install python-imdbpy) or download it from http://imdbpy.sourceforge.net

# === Usage ===  
# -- Get information about a movie --
# (movie lookup)* ([\w ]+)
# Example: say "Look up movie The Matrix"

# -- Get director for a movie --
# (who directed)* ([\w ]+)
# Example: say "Who directed The Matrix" 

#-- Get the name of the actor who played a character in a movie or TV show--
# (who played|who plays|who was)* ([\w ]+) *in* ([\w ]+)
# Example: say "Who played Morpheus in The Matrix"

#-- Recommend a  movie --
# (should i see|should i watch)* ([\w ]+)
# Example: say "Should i watch The Matrix?"


# See README at https://github.com/Nurfballs/SiriServer-IMDb for full set of instructions.


import re
import sys
import urllib2, urllib
import json

from plugin import *

from plugins.nurfimdb.googlemovieshowtimes import *
 
from siriObjects.systemObjects import GetRequestOrigin, Location
from siriObjects.uiObjects import AddViews
from siriObjects.answerObjects import AnswerSnippet, AnswerObject, AnswerObjectLine


try:
    from imdb import IMDb
    import imdb.helpers
except ImportError:
    raise NecessaryModuleNotFound("Oops! Unable to locate the IMDb library. Please install IMDbPy. e.g. (sudo easy_install IMDbPy) or (sudo apt-get install python-imdbpy)")

class nurf_imdb(Plugin):
    
    @register("en-US", "(who directed)* ([\w ]+)") 
    def get_director(self, speech, language,  regex):
        if language == "en-US":
            #Get name of the movie title
            MovieTitle = regex.group(regex.lastindex).strip()
            ia = IMDb()
            
            #Look it up
            search_result = ia.search_movie(MovieTitle)
            if not search_result:
                self.say("Sorry, I could not find any information for " + MovieTitle)
                self.complete_request()
            
            else:
                movie_info = search_result[0]
                ia.update(movie_info)
                
                #Get full title
                strFullTitle = movie_info['title']
                #Get director
                strDirector = movie_info['director'][0]['name']
                
                self.say(strDirector + " directed "+ strFullTitle)
                self.complete_request()
    
    @register("en-US",  "(who played|who plays|who was)* ([\w ]+) *in* ([\w ]+)")
    def get_actorbycharacter(self,  speech,  language,  regex):
        if language == "en-US":
            
            # get the name of the character to look up
            character = regex.group(2)
            character = character.title().strip()
            
            # get the name of the movie to look up
            movie = regex.group(3)
            movie = movie.title()
            
            ia = IMDb()
            search_result = ia.search_movie(movie)
            
            if not search_result:
                self.say("No matches found for that title")
                self.complete_request()
            else:
                movietitle = search_result[0]['title']
                moviedetails = search_result[0]
                ia.update(moviedetails)
                
                cast = moviedetails['cast']
                
                try:
                    for actor in cast:                 
                        if character in actor.currentRole['name']:
                            self.say(actor['name'])
                            
                            #Get Image
                            Query = urllib.quote_plus(actor['name'].encode("utf-8"))
                            SearchURL = u'https://ajax.googleapis.com/ajax/services/search/images?v=1.0&imgsz=small|medium|large|xlarge&q=' + str(Query)
                            try:
                                jsonResponse = urllib2.urlopen(SearchURL).read()
                                jsonDecoded = json.JSONDecoder().decode(jsonResponse)
                                ImageURL = jsonDecoded['responseData']['results'][0]['unescapedUrl']
                                view = AddViews(self.refId, dialogPhase="Completion")
                                ImageAnswer = AnswerObject(title=str(actor['name']),lines=[AnswerObjectLine(image=ImageURL)])
                                view1 = AnswerSnippet(answers=[ImageAnswer])
                                view.views = [view1]
                                self.sendRequestWithoutAnswer(view)
                                self.complete_request()
                            except (urllib2.URLError):
                                self.say("Sorry, a connection to Google Images could not be established.")
                                self.complete_request()
                            
                            
                            self.complete_request()
                    
                    self.complete_request()
                except:
                    self.say("Sorry, I couldnt find any characters by that name in " + movietitle)
                    self.complete_request()
    
    @register("en-US",  "(lookup|look up).*(movie|show)* ([\w ]+)")
    def move_lookup(self,  speech,  language,  regex):
        if language == "en-US":
            MovieTitle = regex.group(regex.lastindex).strip()
            ia = IMDb()
            search_result = ia.search_movie(MovieTitle)
            if not search_result:
                self.say("Sorry, I could not find any information for " + MovieTitle)
                self.complete_request()
            
            else:
                
                self.say("Let me look that up for you.")
                view = AddViews(self.refId, dialogPhase="Completion")
                
                # -- Get Movie Info --
                movie_info = search_result[0]
                MovieTitle = movie_info['long imdb canonical title']
                ia.update(movie_info)
                
                # -- Get the URL for poster --
                AnswerStringPosterURL = movie_info['cover url']
                # Output to the AnswerObject
                NurfIMDBAnswerPosterURL = AnswerObject(title=MovieTitle,lines=[AnswerObjectLine(image=AnswerStringPosterURL)])
                
                #-- Get Rating --
                AnswerStringRating = str(movie_info['rating']) + "/10 (" + str(movie_info['votes']) + " votes)"
                # Output to the AnswerObject
                NurfIMDBAnswerRating = AnswerObject(title='Rating:',lines=[AnswerObjectLine(text=AnswerStringRating)]) 
                
                #-- Get Plot --
                plot = movie_info['plot'][0].split('::')
                AnswerStringPlot = plot[0]
                # Output to the AnswerObject
                NurfIMDBAnswerPlot = AnswerObject(title='Plot:',lines=[AnswerObjectLine(text=AnswerStringPlot)]) 
                
                #-- Get Directors --
                AnswerStringDirectors = ''
                for director in movie_info['director']:
                    AnswerStringDirectors = AnswerStringDirectors + director['name'] + ", "
                AnswerStringDirectors = AnswerStringDirectors.rstrip(',') #Remove the last comma from the answerstring
                # Output to the AnswerObject
                NurfIMDBAnswerDirectors = AnswerObject(title='Directors:',lines=[AnswerObjectLine(text=AnswerStringDirectors)]) 
                
                #-- Get Writers --
                AnswerStringWriters = ''
                for writer in movie_info['writer']:
                    AnswerStringWriters = AnswerStringWriters + writer['name'] + ", "
                AnswerStringWriters = AnswerStringWriters.rstrip(',') #Remove the last comma from the answerstring
                # Output to the AnswerObject
                NurfIMDBAnswerWriters = AnswerObject(title='Writers:',lines=[AnswerObjectLine(text=AnswerStringWriters)]) 
                
                # -- Get Cast --
                AnswerStringCast = ''
                for actor in movie_info['cast']:
                    try:
                        AnswerStringCast = AnswerStringCast + actor['name'] + " (" + str(actor.currentRole['name']) + "), "
                    except:
                        AnswerStringCast = AnswerStringCast + actor['name'] + ", "
                AnswerStringCast = AnswerStringCast.rstrip(',') #Remove the last comma from the answerstring
                # Output to the AnswerObject
                NurfIMDBAnswerCast = AnswerObject(title='Cast:',lines=[AnswerObjectLine(text=AnswerStringCast)]) 
                
                # -- Results --
                #Display the results
                view1 = AnswerSnippet(answers=[NurfIMDBAnswerPosterURL, NurfIMDBAnswerRating, NurfIMDBAnswerPlot, NurfIMDBAnswerDirectors,  NurfIMDBAnswerWriters,  NurfIMDBAnswerCast])
                view.views = [view1]
                self.sendRequestWithoutAnswer(view)
                self.complete_request()
    
    @register("en-US", "(should i see|should i watch)* ([\w ]+)") 
    def get_rating(self, speech, language,  regex):
        if language == "en-US":
            MovieTitle = regex.group(regex.lastindex).strip()
            ia = IMDb()
            search_result = ia.search_movie(MovieTitle)
            if not search_result:
                self.say("Sorry, I could not find any information for " + MovieTitle)
                self.complete_request()
            
            else:
                movie_info = search_result[0]
                ia.update(movie_info)    
                
                try:
                    MovieRating = movie_info['rating']
                    if (MovieRating < 6):
                        self.say("Rating: " + str(MovieRating) + " out of 10. You probably should not see this movie.")
                    elif (MovieRating < 8):
                        self.say("Rating: " + str(MovieRating) + " out of 10. I recommend you see this movie.")
                    elif (MovieRating >= 8):
                        self.say("Rating: " + str(MovieRating) + " out of 10. This movie is a must-see!")
                    self.complete_request()
                except:
                    self.say("Sorry. This movie has not yet been rated.")
                    self.complete_request()

    @register("en-US", ".*(movie times|showtimes)* ([\w ]+)") 
    def get_rating(self, speech, language,  regex):
        if language == "en-US":
            movieTitle = regex.group(regex.lastindex)
            location = self.getCurrentLocation(force_reload=True,accuracy=GetRequestOrigin.desiredAccuracyBest)
            url = "http://maps.googleapis.com/maps/api/geocode/json?latlng={0},{1}&sensor=false&language={2}".format(str(location.latitude),str(location.longitude), language)
            try:
                jsonString = urllib2.urlopen(url, timeout=3).read()
            except:
                pass
            street=""
            stateLong=""
            postalCode=""
            city=""
            countryCode=""
            the_header=""
            if jsonString != None:
                response = json.loads(jsonString)
                if response['status'] == 'OK':
                    components = response['results'][0]['address_components']              
                    street += filter(lambda x: True if "route" in x['types'] else False, components)[0]['long_name']
                    stateLong += filter(lambda x: True if "administrative_area_level_1" in x['types'] or "country" in x['types'] else False, components)[0]['long_name']
                    try:
                        postalCode += filter(lambda x: True if "postal_code" in x['types'] else False, components)[0]['long_name']
                    except:
                        postalCode+=""
                    try:
                        city += filter(lambda x: True if "locality" in x['types'] or "administrative_area_level_1" in x['types'] else False, components)[0]['long_name']
                    except:
                        city+=""
                    originName = city + ", " + stateLong
                    movieID = ""
                    theaterID = ""
                    movieObj = GoogleMovieShowtimes(originName, movieID, theaterID)
                    self.say("Plugin still in development. Please click below for the Google movies listing.")
                    url = "http://www.google.com/movies?hl=en&near={0}&dq=movie+times+{1}&sa=X&oi=showtimes&ct=title&cd=1&q={2}".format(postalCode, postalCode, movieTitle.encode("utf-8"))
                    view = UIAddViews(self.refId)
                    button = UIButton()
                    if language == 'en-US':
                        button.text = u"Showtimes for {0}".format(originName)
                    link = UIOpenLink("")
                    link.ref = url.replace("//","")
                    button.commands = [link]
                    view.views = [button]
                    self.send_object(view)
                    self.complete_request()