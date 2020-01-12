import os
import eel
import spotipy
import pickle
import json
from pprint import pprint
from spotipy.oauth2 import SpotifyClientCredentials
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from collections import Counter
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# If modifying these scopes, delete the file token.pickle
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Global variables and settings
search_limit = 15
min_followers = 500
sorted_playlist_list = []

sp = None
creds = None

def spotifyFilter(playlist):
    # Filters playlists by Spotify and those that have already been sorted
    
    # Check if owner is Spotify
    if playlist['owner']['id'] == 'spotify':
        return False
    print(playlist['id'], sorted_playlist_list)

    # Check if playlist has already been sorted
    if playlist['id'] in sorted_playlist_list:
        return False

    return True

@eel.expose
def get_playlists(searchTerm):

    results = sp.search(searchTerm, limit=search_limit, offset=0, type='playlist', market=None)
    playlists = results['playlists']['items']

    noSpotifyPlaylists = list(filter(spotifyFilter, playlists))
    
    results['playlists']['items'] = noSpotifyPlaylists

    new_results = {}
    new_results['items'] = []
    new_results['next'] = results['playlists']['next']
    for info in noSpotifyPlaylists:
        new_results['items'].append({
            'name': info['name'],
            'description': info['description'],
            'href': info['external_urls']['spotify'],
            'owner_name': info['owner']['display_name'],
            'owner_id': info['owner']['id'],
            'image': info['images'][0]['url'],
            'id': info['id'],
            'num_tracks': info['tracks']['total'],
            'followers': None,
            "artists": None,
            'track_previews': None
        })

    load_max = min(search_limit, len(new_results['items']))
    for i in range(load_max):
        this_playlist_info = new_results['items'][i]
        this_playlist_info['followers'], this_playlist_info['artists'], this_playlist_info['track_previews'] = get_detailed_playlist_info(this_playlist_info)

    return {'playlists':new_results}

@eel.expose
def nice(sheet_id, info_to_write, playlist_id):
    # This is triggered when the user decides a playlist should be added to their spreadsheet
    # It takes the playlist info and appends it to Sheet1 of the spreadsheet
    pprint(creds)
    service = build('sheets', 'v4', credentials=creds)
    # The A1 notation of the values to update.
    range_ = 'Sheet1!A1'
    value_input_option = 'RAW'
    value_range_body = {
        "range": 'Sheet1!A1',
        "majorDimension": 'ROWS',
        "values": [
            info_to_write
        ]
    }
    request = service.spreadsheets().values().append(spreadsheetId=sheet_id, range=range_, valueInputOption=value_input_option, body=value_range_body)
    response = request.execute()
    save_as_sorted(playlist_id)
    pprint(response)

@eel.expose
def save_as_sorted(playlist_id):
    # This function is called whenever the user accepts or rejects a playlist
    # It will add it to the list of sorted playlists and save the list
    sorted_playlist_list.append(playlist_id)
    filename = 'sorted_playlists.pickle'
    outfile = open(filename,'wb')
    pickle.dump(sorted_playlist_list,outfile)
    outfile.close()

def get_detailed_playlist_info(playlist_info):
    # Some playlist details, specifically song details, preview tracks, and followers, are not provided with the playlist search API
    # This function takes a playlist and calls the playlist API to get that information
    pl_details = sp.user_playlist(playlist_info['owner_id'], playlist_info['id'], fields='followers,tracks')
    tracks_data = pl_details['tracks']['items']
    artist_dict = {}
    artist_str = ''

    # Get 5 most popular artists on the playlist (by popularity)
    for i in range(len(tracks_data)):
        artist_dict[tracks_data[i]['track']['artists'][0]['name']] = tracks_data[i]['track']['popularity']
    k = Counter(artist_dict) 
    high = k.most_common(5)  
    for i in high:
        artist_str = artist_str + i[0] + ", "
    artist_str = artist_str[:-2]
    
    # Get 5 track preview urls
    track_clip_urls = []
    i = 0
    while len(track_clip_urls) < 4 and i < len(tracks_data):
        if(tracks_data[i]['track']['preview_url'] != None):
            track_clip_urls.append(tracks_data[i]['track']['preview_url'])
        i = i + 1

    # Return the number of followers, string of popular artists, and track preview urls
    return pl_details['followers']['total'], artist_str, track_clip_urls

@eel.expose
def authorize_google():
    global creds
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPES)
    # gc = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    # sheet = gc.open_by_key("1e_oJKU_irXGjkuGTNwNLOpE6jg69xIDQjUiqsT1wlG0").sheet1
    
if __name__ == "__main__":
    client_credentials_manager = SpotifyClientCredentials(client_id='ac2ead8195474d018b6a42fbbe5f27a6', client_secret='a6d33e1f81f943f9bd7b91d9540d3b6d')
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    authorize_google()
    if os.path.isfile('sorted_playlists.pickle'):
        infile = open('sorted_playlists.pickle','rb')
        sorted_playlist_list = pickle.load(infile)
        pprint(sorted_playlist_list)
        infile.close()
    eel.init('GUI')
    eel.start('main.html')