
import os
import json
import pickle
import urllib.request, urllib.error, urllib.parse

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

client_credentials_manager = SpotifyClientCredentials(client_id="b819c8fd59fd402d9c2fa91368673db2",
                                                      client_secret="4de3580d287f4e6eb585e9c13ad98347")
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

#### apikey_musixmatch = '5d43102db4198580090bcf0070bb7c79'
apiurl_musixmatch = 'http://api.musixmatch.com/ws/1.1/'

class InformationEngine:
    def __init__(self, saved_filename, apikey_msxmatch):
        self.apikey_msxmatch = apikey_msxmatch
        self.saved_filename = saved_filename

        if os.path.isfile(saved_filename):
            self.information = pickle.load(open(saved_filename, "rb"))
        else:
            print("WARNING!! MAKING NEW PICKLED FILE!!!")
            self.information = dict()

    def replace_spotifyid(self, oldtuple, newspotifyid, newartist, newtitle):
        return (oldtuple[0], newspotifyid, newtitle, newartist)

    def get_information(self, musixmatch_id, artist, title):
        if musixmatch_id not in self.information:
            ## Load info for song
            trackinfo = get_musixmatch_information(musixmatch_id, self.apikey_msxmatch)
            if len(trackinfo[1]) == 0:
                results = sp.search(q='artist:' + artist + " title:" + title)
                if len(results['tracks']['items']) > 0:
                    trackinfo = self.replace_spotifyid(trackinfo, results['tracks']['items'][0]['id'], artist, title)


            self.information[musixmatch_id] = trackinfo
            print("INFO: Downloaded track information: " + str(trackinfo))
            pickle.dump(self.information, open(self.saved_filename , "wb"))
        return self.information[musixmatch_id]






def get_musixmatch_information(msxtrack_id, apikey):
    querystring = apiurl_musixmatch + "track.get?track_id=" + str(
        msxtrack_id) + "&format=json&apikey=" + apikey  # + urllib.parse.quote(song_name) + "&q_artist=" + urllib.parse.quote(artist_name) +"&apikey=" + apikey_musixmatch + "&format=json&f_has_lyrics=1"

    request = urllib.request.Request(querystring)
    request.add_header("User-Agent",
                       "curl/7.9.8 (i686-pc-linux-gnu) libcurl 7.9.8 (OpenSSL 0.9.6b) (ipv6 enabled)")  # Must include user agent of some sort, otherwise 403 returned

    response = urllib.request.urlopen(request, timeout=4)
    raw = response.read()

    json_obj = json.loads(raw.decode('utf-8'))
    #     print(json_obj)
    print(json_obj["message"]['header']['status_code'])
    if json_obj["message"]['header']['status_code'] != 200:
        return ("", "", "", "")
    track_share_url = json_obj["message"]["body"]["track"]['track_share_url'].split("?")[0]
    track_spotify_id = json_obj["message"]["body"]["track"]['track_spotify_id']
    track_name = json_obj["message"]["body"]["track"]['track_name']
    artist_name = json_obj["message"]["body"]["track"]['artist_name']

    return track_share_url, track_spotify_id, track_name, artist_name
