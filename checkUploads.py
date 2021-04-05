import re
import os
import json
import datetime

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

# Confidential info regarding youtube API authentication
from confidential import API_KEY, SECRET_FILE

class youtubeConnection:
    def __init__(self):
        self.youtube = self.connectAPI()


    def connectAPI(self, useOAuth=False):
        if useOAuth:
            # Disable OAuthlib's HTTPS verification when running locally.
            # *DO NOT* leave this option enabled in production.
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
            scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]

            # Get credentials and create an API client
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                SECRET_FILE, scopes)
            credentials = flow.run_console()

            youtube = googleapiclient.discovery.build(
                "youtube", "v3", credentials=credentials)
        else:
            youtube = googleapiclient.discovery.build(
                "youtube", "v3", developerKey=API_KEY)
        return youtube

    # save the response as a json:
    def saveResponse(self, response, file_name="response"):
        open(file_name+".json", "w").write(json.dumps(response, indent=4))

    # The following displays an overview for a channel
    def listChannel(self, username="LinusTechTips"): # retrieves channel data for channels that match the username
        request = self.youtube.channels().list(
            part="snippet,contentDetails,statistics",
            forUsername=username
        )
        response = request.execute()
        return response

    def listChannelVideos(self, channelID="UCXuqSBlHAE6Xw-yeJA0Tunw", total=5): # Defaults to LTT channel
        '''
        This function returns the response for a search of the top 2 most recent videos uploaded to LTT.
        '''
        request = self.youtube.search().list(
            part="snippet",
            type="video",
            channelId=channelID, 
            maxResults=total, 
            order="date"
        )
        response = request.execute()
        return response

    @staticmethod
    def getTimeSinceUpload(publishedAt):
        '''
        Takes in the publishedAt string from the API response and uses that
        to return a timedelta object since it was published.

            Parameters:
                publishedAt (str): RFC 3339 formatted date-time value
            Returns:
                timedelta (timeDelta): represents time since it was uploaded.
        '''
        # The format is  -> 1970-01-01T00:00:00Z
                        #  year -Month- day T hour: mins: secsZ
        info = re.search(r'(\w+)-(\w+)-(\w+)T(\w+):(\w+):(\w+)Z', publishedAt)

        # creating datetime object with the info
        published_time = datetime.datetime(
            year=int(info.group(1)),
            month=int(info.group(2)), 
            day=int(info.group(3)),
            hour=int(info.group(4)),
            minute=int(info.group(5)),
            second= int(info.group(6))
        )

        # Getting current time and calculating difference
        return datetime.datetime.utcnow() - published_time

    def getLatestUpload(self, channelId="UCXuqSBlHAE6Xw-yeJA0Tunw"):
        '''
        This function gets the latest upload as well as how long ago it was uploaded.

            Parameters
                channelId (str): The channel id to search through
            Returns:
                videoId (str): The video id of the upload
                title (str): The title of the video
                delta (timeDelta): The time since the upload of the video
        '''

        res = self.listChannelVideos(channelId)
        video_res = res["items"][0]
        snippet = video_res["snippet"]

        delta = self.getTimeSinceUpload(publishedAt=snippet["publishedAt"])

        return video_res["id"]["videoId"], snippet["title"], delta, snippet

    def getInfo(self, channelId="UCXuqSBlHAE6Xw-yeJA0Tunw"):
        '''
        Only important info for display
        '''
        try:
            _, title, delta, _ = self.getLatestUpload(channelId=channelId)
            time_min = int(delta.total_seconds()/60)
            return time_min, title
        except:
            print("Error in YT_API")
            return 61, "ran out of units!"

        
