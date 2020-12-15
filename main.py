from flask import Flask, render_template, request

import urllib.parse, urllib.request, urllib.error, json, tmdb_api

from flask import Flask, render_template
import logging

app = Flask(__name__)

def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)

def safeGet(url):
    try:
        return urllib.request.urlopen(url)
    except urllib.error.URLError as e:
        if hasattr(e,"code"):
        	print("The server couldn't fulfill the request.")
        	print("Error code: ", e.code)
        elif hasattr(e,'reason'):
        	print("We failed to reach a server")
        	print("Reason: ", e.reason)
        return None


#### FOR TESTING
#lat = 64
#lng = -147


#this allows me to access the NWS API, they use a header instead of
#an api key
def nws_get(url):
    """Accesses the NWS data"""
    headers = {"User-Agent": tmdb_api.header_info}
    req = urllib.request.Request(url,headers=headers)
    # pass that request to safe_get
    result = safeGet(req)
    if result is not None:
        return json.load(result)

def make_forecast(lat , lng) :
    """Accesses the NWS data we would like to use"""
    locurl = "https://api.weather.gov/points/{},{}/forecast".format(lat,
        lng)
    #calling for the lat and lng inputted by the user
    locinfo = nws_get(locurl)
    #returns the json data
    return locinfo


#this method then takes the json data of make_forecast
def get_weather_details (locinfo):
    """this takes the shortForecast data to be used elsewhere"""
    if locinfo == None:
        return None
    else:
        important_items_from_weather = {}
        #cycle through each label in the first dictionary in the list
        for item in locinfo["properties"]["periods"][0]:
        #cycle through each key, key just cycles through the indicies of the word
            if item == "shortForecast":
                important_items_from_weather[item] = locinfo["properties"]["periods"][0][item]

        return important_items_from_weather

#### THIS IS FOR TESTING ####

#what_genre = get_weather_details(make_forecast(lat, lng))
#print(what_genre)
#this method takes in the shortforecast data and decides
# what genres should be returned for the user to view
# I chose these genres of what I thought best fit the ~vibe~
def decide_genre(what_genre_confusion):
    """This parses what genres will be shown according to the forecast"""
    if what_genre_confusion is not None:
        genre_list = ""
    # for summer
        if "Sunny" in what_genre_confusion["shortForecast"]:
        #35 = Comedy and 12 = Adventure
            genre_list = "12,35"
    #for fall
        elif "Rain" in what_genre_confusion["shortForecast"]:
        #9648 = Mystery and 18 = Drama
            genre_list = "9648,18"
    #for winter
        elif "Snow" in what_genre_confusion["shortForecast"]:
        # 28 = Action 36 = History and 80 = Crime
            genre_list = "28,36,80"
        elif "Cloudy" in what_genre_confusion["shortForecast"]:
        # 53= Thriller 878 = Science Fiction
            genre_list = "53,878"
    #for spring
        elif "Clear" in what_genre_confusion["shortForecast"]:
        # 10749 = Romance and 14 = Fantasy
            genre_list = "10749,14"
        return genre_list
    else:
        return None



#### THIS IS FOR TESTING ####
####print(decide_genre(what_genre))
####print(make_forecast(lat, lng))
####print(pretty(get_weather_details(make_forecast(lat, lng))))
#the_genres = decide_genre(what_genre)


def TMDB_REST(baseurl='https://api.themoviedb.org/3/discover/movie',
        api_key = tmdb_api.key,
        format = 'json',
        language = "en-US",
        sort_by = "popularity.desc",
        include_adult = False,
        with_genres = "12,35",
        #primary_release_year = 2012,
        params = {},
        printurl = True
        ):
    """this is how we get the movie information"""
    params['api_key'] = api_key
    params['format'] = format
    params["language"] = language
    params["sort_by"] = sort_by
    #params["primary_release_year"] = primary_release_year
    params["include_adult"] = include_adult
    params["with_genres"] = with_genres

    if format == "json":
        params['nojsoncallback'] = True
    url = baseurl+ "?" + urllib.parse.urlencode(params)
    if printurl:
        print(url)
    return safeGet(url)

def printinfo(url):
    """where we make the url into something processable"""
    readable = url.read()
    getreadytoprint = json.loads(readable)
    if getreadytoprint is not None:
        return getreadytoprint
    else:
        return None

#### THIS IS FOR TESTING ####
#print(pretty(printinfo(TMDB_REST())))



#FLASK CODE
@app.route('/')
def main_handler():
    app.logger.info("InMainHandler")
    return render_template("openingpagetemplate.html", page_title= "Find Movies")


@app.route("/gresponse", methods=['GET', 'POST'])
def response_handler():
        movie_info = {}
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        if lat and lng:
            what_genre_confusion = get_weather_details(make_forecast(lat, lng))
            the_genres = decide_genre(what_genre_confusion)
            movie_search = printinfo(TMDB_REST(with_genres=the_genres))
            if what_genre_confusion == None:

                return render_template("openingpagetemplate.html", page_title="Find Movies for the Weather",
                                       prompt="Please try again, this is either not a valid valid location (it must be in the US)"
                                              "and sometimes you have to be very exact to make sure you are not in the water OR there is no NWS report for the location you inputted (usually limited to very remote areas)")
            else:
            # movie search returns to us a list of dictionaries
            #these need to be accessed by index, staring at 0
                index = 0
            #we need to get into the list first, which is the results
            #this looks at each list item at a time
                for one_movie in movie_search["results"]:
                    if index <= 9 and one_movie is not None:
                    # adds a value of the title to the dictionary
                    # need to add nesting
                    # { title: { popularity: POPULARITY, overview: OVERVIEW } title: etc...)
                    #or instead
                    # { { title: TITLE, popularity: POPULARITY, overview: OVERVIEW } { title: etc...)
                        if one_movie["title"] not in one_movie:
                            movie_info[one_movie["title"]] = {}
                        movie_info[one_movie["title"]]["popularity"] = one_movie["popularity"]
                        movie_info[one_movie["title"]]["overview"] = one_movie["overview"]
                        index += 1

                return render_template("responsepage.html",movie_info = movie_info, lat=lat, lng=lng)

        else:
            return render_template("openingpagetemplate.html",page_title= "Find Movies for the Weather", prompt="Please complete the location!")


if __name__ == "__main__":
    # Used when running locally only.
	# When deploying to Google AppEngine, a webserver process
	# will serve your app.
    app.run(host="localhost", port=8080, debug=True)

