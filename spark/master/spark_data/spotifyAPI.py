from time import sleep
import requests
import redis 
import json
import pandas as pd

CLIENT_ID = '72c2183e4c034c15a0305818667390b7'
CLIENT_SECRET = '7dc6919a592f49519435f7dc3f8fc1b5'
EXPIRING_TIME = 3500

AUTH_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'
REDIS_IP = '10.0.0.7'


redis_cache= redis.StrictRedis(host=REDIS_IP)


def getAccessToken():

    auth_response = requests.post(AUTH_URL, {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    })
    
    auth_response_data = auth_response.json()
    return auth_response_data['access_token']


def getAuthHeader():

    header = redis_cache.get('header')
    if header == None:
        
        access_token = getAccessToken()
        header = {
            'Authorization': 'Bearer {token}'.format(token=access_token)
        }
        redis_cache.set('header',json.dumps(header),ex=EXPIRING_TIME)  #Spotify timeout at 3600
    else:
        header = json.loads(header)

    return header


def getTracksAudioFeatures(ids,features):

    if len(ids)==0:
        return {}
    print('dio porco',ids)
    headers = getAuthHeader()
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
            
            request_result[track['id']] = (track['energy'], track['danceability'], track['duration_ms'], track['instrumentalness'],\
                                           track['loudness'], track['tempo'], track['valence'])
            
            redis_cache.set(track['id'],json.dumps(request_result[track['id']]))

    return request_result


def getTracksFeaturesAPI(track_ids, features=['energy','danceability','duration_ms','instrumentalness','loudness','tempo','valence']):
    
    track_ids = list(track_ids)

    missing_ids = set()
    hitted_ids = {}
    
    for id in track_ids:

        track_info = redis_cache.get(id)
        if track_info == None:
            missing_ids.add(id)
        else:
            hitted_ids[id]=json.loads(track_info)

    request_result = getTracksAudioFeatures(list(missing_ids),features) 

    result = []
    for id in track_ids:

        if id in missing_ids:
            result.append(request_result[id])
        else:
            result.append(hitted_ids[id])
        
    return pd.DataFrame(result)
