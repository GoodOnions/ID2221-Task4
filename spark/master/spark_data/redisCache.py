import json
import redis 
import pandas as pd

REDIS_IP = 'redis'

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
