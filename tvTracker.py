import os
import requests
import json
import sys
from datetime import datetime
from datetime import timedelta


SAVED_SHOWS_FILEPATH = "saved_tv_shows.json"
ROOT = os.path.dirname(os.path.abspath(__file__))
API_URL = "http://api.tvmaze.com"
SEARCH_URL = "/search/shows?q="
SHOW_URL = "/shows/"
EMBED_URL = "?embed=episodes"


class TvTracker:
    def __init__(self, path):
        self.tvShows = {}
        if os.path.isfile(path):
            self.tvShows = self.readFile(path)
            if not isinstance(self.tvShows, dict):
                self.tvShows = {}

    def readFile(self, path):
        saveContent = ""
        try:
            with open(path, 'r') as f:
                if os.stat(path).st_size != 0:
                    saveContent = json.load(f)
        except Exception as e:
            print("Error reading file %s: %s" % (path, e))
        return saveContent

    def writeFile(self, path, content):
        try:
            with open(path, "w") as f:
                f.write(json.dumps(content, indent=2))
            print("Succesfully written to disk.")
        except Exception as e:
            print("Error writing to disk")

    def updateTvShows(self, shows):
        for showId in shows:
            show = {
            'name': self.tvShows[showId]["name"],
            'tvmazeid': showId,
            'premiereDate': self.tvShows[showId]["premiereDate"]
            }
            self.tvShows[showId] = self.getTvShow(show)
            print("Updated %s." % show["name"])

    def getTvShow(self, show):
        request = requests.get(API_URL + SHOW_URL + str(show['tvmazeid']) + EMBED_URL)
        tvdata = json.loads(request.content)
        present = datetime.now().date()
        episodes = []

        for k, v in tvdata["_embedded"].items():
            allFutureEpisodesAdded = False
            if k == "episodes":
                v.reverse()
                for index, ep in enumerate(v):
                    try:
                        if ep['airdate']:
                            airDate = datetime.strptime(ep['airdate'], '%Y-%m-%d').date()
                            if airDate < present:
                                allFutureEpisodesAdded = True
                            epname = ep['name']
                            epnumber = ep['number']
                            epseason = ep['season']
                            id = ep['id']
                            if allFutureEpisodesAdded == False:
                                episode = {
                                    'id': id,
                                    'epname': epname,
                                    'epseason': epseason,
                                    'epnumber': epnumber,
                                    'airdate': str(airDate)
                                }
                                episodes.append(episode)
                            if allFutureEpisodesAdded == True:
                                break
                    except Exception as e:
                        print(e)
                episodes.reverse()
                nextairdate = "n/a"
                if episodes:
                    nextairdate = episodes[0]['airdate']
                show = {
                    'name': show['name'],
                    'premiereDate': show['premiereDate'],
                    'episodes': episodes,
                    'nextAirdate': nextairdate,
                    'lastFetch': str(present)
                }
                return show

    def addToLibrary(self, showToBeAdded):
        if showToBeAdded["tvmazeid"] in self.tvShows:
            print("TV show is already in the collection")
        else:
            self.tvShows[showToBeAdded["tvmazeid"]] = self.getTvShow(showToBeAdded)
            print("Added %s to library." % self.tvShows[showToBeAdded["tvmazeid"]]["name"])

    def checkUpdates(self):
        updatesNeeded = []
        for showId, values in self.tvShows.items():
            updateNeeded = False
            present = datetime.now().date()
            lastFetch = datetime.strptime(values['lastFetch'], '%Y-%m-%d').date()
            episodes = values['episodes']
            if (present - timedelta(days=5)) > lastFetch:
                updateNeeded = True
            if episodes:
                strippedAirdate = episodes[0]["airdate"].split("-")
                try:
                    strippedAirdate = datetime(int(strippedAirdate[0]), int(strippedAirdate[1]), int(strippedAirdate[2])).date()
                except:
                    updateNeeded = True
                if strippedAirdate < present:
                    updateNeeded = True
            else:
                updateNeeded = True
            if updateNeeded:
                updatesNeeded.append(showId)
        self.updateTvShows(updatesNeeded)

    def removeTvShow(self, showId):
        try:
            showId = showId.strip()
            if showId in self.tvShows:
                name = self.tvShows[showId]["name"]
                self.tvShows.pop(showId)
                print("Removed %s from library." % name)
            elif not showId:
                return
            else:
                print("There's no tv show with that ID in the collection.")
        except Exception as e:
            print("Error removing tv show with id %s: %s" % (showId, e))

    def filterSearchResults(self, searchResults):
        show_dict = {}
        counter = 0

        for i in searchResults:
            for key, value in i.items():
                if key == 'show':
                    if i['show']['premiered'] is not None:
                        name = i['show']['name']
                        tvmazeid = i['show']['id']
                        premiereDate = i['show']['premiered'][0:4]
                        status = i['show']['status']
                        if status != "Ended" and tvmazeid:
                            show_dict[counter] = {
                                'name': name,
                                'tvmazeid': tvmazeid,
                                'premiereDate': premiereDate
                            }
                            counter = counter + 1
        return show_dict

    def fetchTvIds(self, searchTerm):
        try:
            request = requests.get(API_URL + SEARCH_URL + searchTerm)
            return json.loads(request.content)
        except Exception as e:
            print("Error fetching search results for %s: %s" % (searchTerm, e))

    def printMainInterface(self):
        print("\nTV Tracker - menu")
        print("-----------------\n")
        print("s) search tv shows")
        print("d) delete tv show")
        print("p) print upcoming tv episodes")
        print("q) quit program & save changes")

    def getChoice(self):
        while True:
            choice = input()
            if type(choice) is str:
                choice = choice.lower().strip()
                return choice

    def deleteTvShow(self):
        try:
            if self.tvShows:
                for show, values in self.tvShows.items():
                    print("ID: " + str(show) + " - " + values['name'] + (" (" + values['premiereDate']) + ')')
                print("\nChoose the show to be deleted with the show's ID (leave empty and hit enter to go back): ")
                self.removeTvShow(input())
            else:
                print("Add some TV shows first...")
        except Exception as e:
            print("Error while printing list of TV shows for deletion: %s" % e)

    def searchTvShow(self):
        print("\nSearch for a tv show (leave empty and hit enter to go back): ")
        searchTerm = input()
        if searchTerm:
            tvIds = self.fetchTvIds(searchTerm=searchTerm)
        else:
            return
        if tvIds:
            filteredResults = self.filterSearchResults(tvIds)
            selectedShow = self.selectTvShow(filteredResults)
            self.addToLibrary(selectedShow)
        else:
            print("No TV shows found")


    def selectTvShow(self, foundShows):
        selectedShow = []
        while not selectedShow:
            print("\nTV shows found:")
            for key, value in foundShows.items():
                print(str(key) + " - " + value["name"] + " (" + value["premiereDate"] + ")")
            print("\nChoose TV show to add by index number (leave empty and hit enter to go back):")
            selectedIndex = input()
            try:
                if not selectedIndex:
                    return
                elif int(selectedIndex) in foundShows:
                    selectedShow = foundShows[int(selectedIndex)]
                    return selectedShow
                else:
                    print("ERROR: No such index exists")
            except:
                print("ERROR: No such index exists")

    def printSchedule(self):
        print("\n")
        sorted_shows = {}
        if self.tvShows:
            for show, values in self.tvShows.items():
                try:
                    if values['nextAirdate'] != "n/a" and values['nextAirdate']:
                        sorted_shows[show] = values
                except KeyError:
                    pass
            sorted_items = sorted(sorted_shows, key=lambda x: (sorted_shows[x]['nextAirdate']))
            for show in sorted_items:
                weekday = datetime.strptime(sorted_shows[show]['nextAirdate'], '%Y-%m-%d').strftime('%A')
                print(sorted_shows[show]['nextAirdate'] + "[" + weekday + "]" + " - "
                      + sorted_shows[show]['name'] + ": " + sorted_shows[show]['episodes'][0]['epname']
                      + " (s" + str(sorted_shows[show]['episodes'][0]['epseason']) + "e"
                      + str(sorted_shows[show]['episodes'][0]['epnumber']) + ")")
        else:
            print("No tv shows in collection")

    def exitProgram(self, msg=None):
        if msg:
            print(msg)
        sys.exit()


    def mainLoop(self):
        self.checkUpdates()
        while True:
            self.printMainInterface()
            choice = self.getChoice()

            choice = choice.lower().strip()
            if choice == "p":
                self.printSchedule()
            elif choice == "d":
                self.deleteTvShow()
            elif choice == "s":
                self.searchTvShow()
            elif choice == "q":
                self.writeFile(os.path.join(ROOT, SAVED_SHOWS_FILEPATH), self.tvShows)
                print("Exiting...")
                sys.exit(0)
            else:
                print("%s is not valid option" % choice)



if __name__ == "__main__":
    tvTracker = TvTracker(os.path.join(ROOT, SAVED_SHOWS_FILEPATH))
    tvTracker.mainLoop()
