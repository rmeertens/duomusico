from flask import Flask

app = Flask(__name__)



import numpy as np
from scipy.sparse import csr_matrix
import duolingo
from MusicRecommender import *
from InformationEngine import *

import os
print(os.getcwd())
from os import listdir
from os.path import isfile, join
for f in listdir(os.getcwd()):
    print(f)


HOME_PATH = "pydatabase/"
FILENAME_MXM_MATCHES = HOME_PATH + "mxm_779k_matches.txt"
FILENAME_INFORMATION = HOME_PATH + "information.pickle"
FILENAME_SPARSE_MATRIX = HOME_PATH + "sparse_tfidf.pickle"
FILENAME_DATASET_TRAIN = HOME_PATH + "mxm_dataset_train.txt"
print("PATHS")
print(FILENAME_INFORMATION )
print(FILENAME_SPARSE_MATRIX)
apikey_musixmatch = '5d43102db4198580090bcf0070bb7c79'

### READ THE MILLION SONG IDS AND ARTIST NAMES AND TITLES
artist_names = dict()
titles = dict()
print("Loading matches")

with open(FILENAME_MXM_MATCHES) as infile:
    for _ in range(18):
        comment = infile.readline()
    for line in infile:
        tid, artist_name, title, mxm_tid, artist_namemxm, titlemxm = line.split("<SEP>")
        artist_names[mxm_tid] = artist_name
        titles[mxm_tid] = title





information_engine = InformationEngine(FILENAME_INFORMATION, apikey_musixmatch)

tracks = dict()
words = list()
word_to_id = dict()
word_frequency_list = list()
mxm_track_id_vector = list()


print("Loading dataset_train")

if os.path.exists(FILENAME_SPARSE_MATRIX):
    print("Loading from pickle")
    sparse_word_frequency_matrix = pickle.load(open(FILENAME_SPARSE_MATRIX, "rb"))
    print(sparse_word_frequency_matrix.shape)
    with open(FILENAME_DATASET_TRAIN) as infile:
        ## Skip comments
        print("Reading more info")
        for _ in range(17):
            comment = infile.readline()
        print("Read comments")
        ## Read what top 5000 words are used
        words = infile.readline()[1:].split(",")

        ## Save the index of each word
        for index, word in enumerate(words):
            word_to_id[word] = index

        ## Read the wordcounts
        for line in infile:
            splitted = line.split(",")
            unused_track_id, mxm_track_id = splitted[0], splitted[1]
            mxm_track_id_vector.append(mxm_track_id)

else:
    with open(FILENAME_DATASET_TRAIN) as infile:
        ## Skip comments
        for _ in range(17):
            comment = infile.readline()

        ## Read what top 5000 words are used
        words = infile.readline()[1:].split(",")

        ## Save the index of each word
        for index, word in enumerate(words):
            word_to_id[word] = index

        ## Read the wordcounts
        for line in infile:
            splitted = line.split(",")

            unused_track_id, mxm_track_id = splitted[0], splitted[1]
            word_frequency_vector = np.zeros(len(words))
            mxm_track_id_vector.append(mxm_track_id)

            for word in splitted[2:]:
                wordindex, count = word.split(":")
                wordindex = int(wordindex)
                count = int(count)
                wordindex -= 1  # start at index 0
                word_frequency_vector[wordindex] = count

            word_frequency_list.append(word_frequency_vector)
            tracks[mxm_track_id] = word_frequency_vector

    word_frequency_matrix = np.array(word_frequency_list)

    print("Doing the sparse and tfidf stuff")
    ## Determine TF IDF score
    use_tfidf = True
    if use_tfidf:
        inverse_document_frequency = 1 / np.count_nonzero(word_frequency_matrix, axis=0)
        sparse_word_frequency_matrix = csr_matrix(word_frequency_matrix * inverse_document_frequency)
    else:
        sparse_word_frequency_matrix = csr_matrix(word_frequency_matrix)

    print(word_frequency_matrix.shape)
    pickle.dump(sparse_word_frequency_matrix, open(FILENAME_SPARSE_MATRIX, "wb"))

print("Defining some classes")
music_recommender = MusicRecommender(sparse_word_frequency_matrix, mxm_track_id_vector)


def get_recommendations_for_user(sparse_word_vector):
    recommendation = music_recommender.recommend_song(sparse_word_vector)

    found_scores = list()
    for msid, score in recommendation:
        artist = artist_names[msid]
        title = titles[msid]
        a = information_engine.get_information(msid, artist, title)
        if a[1] == "":
            print("Not found... apparently not even in spotify!! artist: " + artist  + " title: " + title)
        else:
            found_scores.append((score, a[0], a[1], a[2], a[3]))

    return found_scores[:200]
print("Defining some functions")

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response


@app.route('/recommend/<username>')
def show_user_profile(username):
    lingo = duolingo.Duolingo(username)
    user_learning_language = list(lingo.user_data.language_data.keys())[0]
    known_words = list()
    unknown_words = list()

    known_word_vector = np.zeros(len(words))
    for word in lingo.get_known_words(user_learning_language):
        if word in word_to_id:
            known_words.append(word)
            index_word = word_to_id[word]
            known_word_vector[index_word] = 1
        else:
            unknown_words.append(word)

    sparse_word_vector = csr_matrix([[a] for a in known_word_vector])


    toreturndict = dict()
    toreturndict["userLearningLanguage"] = user_learning_language
    toreturndict["array"] = list()
    for item in get_recommendations_for_user(sparse_word_vector):
        if len(item[1]) > 0 and len(item[2]) > 0:
            newest = dict()
            newest["Score"] = "{:5.2f}".format(item[0])
            newest["Artist"] = item[4]
            newest["TrackShareURL"] = item[1]
            newest["SpotifyID"] = item[2]
            newest["NameSong"] = item[3]
            toreturndict["array"].append(newest)

        if len(toreturndict["array"]) == 10:
            break

    return json.dumps(toreturndict)

@app.route("/")
def hello():
    print("getting input")
    return "Hello World!"

print("Ready to start the main!")

if __name__ == "__main__":
    print("Ready to start here!")
    app.run('0.0.0.0', debug=False,port=1235)