from time import sleep
import requests
import redis 
import json
import pandas as pd

CLIENT_ID = '72c2183e4c034c15a0305818667390b7'
CLIENT_SECRET = '7dc6919a592f49519435f7dc3f8fc1b5'
EXPIRING_TIME_AUTH = 3500

AUTH_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'
REDIS_IP = 'redis'

FEATURES = ['energy','danceability','duration_ms','instrumentalness','loudness','tempo','valence'] #fake


################ REDIS ###################
redis_cache= redis.Redis(
    host= REDIS_IP,
    port=6379,
    charset="utf-8",
    decode_responses=True
    )

def getKeys():
    return redis_cache.keys()

def isInCacheList(tracksIDs):

    keys = set(getKeys())
    resp=[]
    for id in tracksIDs:
        resp.append(id in keys)

    return pd.DataFrame(resp)

def getTracksFeaturesCache(tracksIDs):

    response = []
    for id in tracksIDs:
        features = redis_cache.get(id)
        if features == None:
            response.append(())
        else:
            response.append(json.loads(features))

    return pd.DataFrame(response)



################ Spotify ###################

def __getAccessToken():

    auth_response = requests.post(AUTH_URL, {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    })
    
    auth_response_data = auth_response.json()
    return auth_response_data['access_token']


def _getAuthHeader():

    header = redis_cache.get('header')
    if header == None:
        
        access_token = __getAccessToken()
        header = {
            'Authorization': 'Bearer {token}'.format(token=access_token)
        }
        redis_cache.set('header',json.dumps(header),ex=EXPIRING_TIME_AUTH)  #Spotify timeout at 3600
    else:
        header = json.loads(header)

    return header


def getTracksAudioFeatures(ids,features):

    if len(ids)==0:
        return {}
    
    headers = _getAuthHeader()
    request_result = {}

    for n in range(int(len(ids)/100)+1):

        track_ids_str = ','.join(ids[n*100:(n+1)*100])
                
        # actual GET request with proper header
        r = requests.get(BASE_URL + 'audio-features?ids=' + track_ids_str, headers=headers)

        while r.status_code!=200:
            print('Status code ->',r.status_code)
            sleep(20)
            r = requests.get(BASE_URL + 'audio-features?ids=' + track_ids_str, headers=headers)

        r = r.json()
        
        for track in r['audio_features']:
            if(track != None):
                request_result[track['id']] = (track['energy'], track['danceability'], track['duration_ms'], track['instrumentalness'],\
                                           track['loudness'], track['tempo'], track['valence'])
                redis_cache.set(track['id'],json.dumps(request_result[track['id']]))

    return request_result


def getTracksFeaturesAPI(track_ids, features=FEATURES):
    
    ids = set(track_ids)    
    request_result = getTracksAudioFeatures(list(ids),features) 

    result = []
    for id in track_ids:
        result.append(request_result.get(id,()))
        
    return pd.DataFrame(result)
