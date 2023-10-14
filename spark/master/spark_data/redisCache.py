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

    


def getTracksFeaturesCache(tracksIDs):

    response = []
<<<<<<< HEAD
=======

>>>>>>> Version_with_join
    for id in tracksIDs:
        features = redis_cache.get(id)
        if features == None:
            response.append(())
        else:
            response.append(json.loads(features))

<<<<<<< HEAD
    return pd.DataFrame(response)
=======
    return response            
>>>>>>> Version_with_join
