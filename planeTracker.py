import requests
import json
import pandas as pd

#INITIALISE
with open('keyfile') as keyfile:
    API_KEY = keyfile.read()

# lambda for quick jupyter representation of a plane
useful_details = ['Source',
                 'Destination',
                 'alt',
                 'reg_number',
                 'flag',
                 ]
show_frame = lambda df : df[useful_details].sort_values(['alt','Destination'])

# If no bounding box provided, uses London
LONDON_BOX = (51.15,-0.91,51.96,0.39)

# Requests
URL = 'https://airlabs.co/api/v9/'
endpoint = lambda e: URL + e

# Get Static Data
with open('airports.json') as airport_data:
    airports = json.load(airport_data)

# Dictionary for turning iata_codes into airport names
#TO DO: add cities to this
codes = {ap['iata_code']:ap['name'] 
         for ap in airports if 'iata_code' in ap.keys()
        }

def get_local_airports(bbox=LONDON_BOX):
    output = []
    for ap in airports:
        if (bbox[0]<ap['lat']<bbox[2]) and (bbox[1]<ap['lng']<bbox[3]):
            output.append(ap)

    return output

def find_airport_name(iata_code):
    try:
        name = codes[iata_code]
    except:
        print('#########\nWeird IATA \nCode Found!\n#########')
        name = 'WEIRD CODE: ' + iata_code
        print('\t' + name)
    
    return name

def get_planes(api_key=API_KEY, bbox=LONDON_BOX):
    '''Requests live plane data and returns it as a dictionary of DataFrames
    split by if the plane is flying over the bbox, landing in the bbox, taking
    off fromt he bbox, flying entirely within the bbox, or ~a mystery~
    '''
    r=requests.get(endpoint('flights'),
                    params={
                        'api_key':api_key,
                        'bbox':bbox,
                    }
                   )
    all_planes = r.json()['response']
    flying_planes=[
        plane for plane in all_planes if plane['status']=='en-route']

    # make DataFrame of all planes
    df=pd.DataFrame(flying_planes)

    # Uses the IATA codes to generate names for Source & Destination Airports
    df['Source'] = df['dep_iata'].map(find_airport_name, 
                                  na_action='ignore')
    df['Destination'] = df['arr_iata'].map(find_airport_name, 
                                       na_action='ignore')

    #The next step classifies the planes in relation to the bbox airports
    
    #Fetches the airports within the bbox and makes a list of their names
    local_airports = get_local_airports(bbox)
    local_names = [a['name'] for a in local_airports]



    '''Makes a batch of DataFrames where each plane is either arriving,
    departing, flying over, being naughty (landing and taking off within the
    bbox) or a mystery'''

    return {
        'arrivals':df.query("Destination in @local_names"),
        'departures' : df.query("Source in @local_names"),
        'flyovers' : df.query(
            "Source not in @local_names and Destination not in @local_names").dropna(),
        'mystery' : df.query("Destination.isna()"),
        'naughty' : df.query("Source in @local_names and Destination in @local_names").dropna(),
        'all' : df
    }
