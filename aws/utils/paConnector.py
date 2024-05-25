from requests_oauthlib import OAuth1Session
import requests


twitter_consumer_key = "IPwVDHqkFZZp3ReFQjzefkKBH"
twitter_consumer_secret = "5lgvhQXAJSvRDZQjfO3t9eotStf3xtZmTij4dMkl7xQkYgUSN8"
twitter_access_token = "1677629692516397056-D7UcKYbtRvm1x8ClvIlP0tH3sCbD8E"
twitter_access_token_secret = "YMTFWFPbZT2CtiRsfiSXUauLmbGeMuHFglQgkTO6VHoRV"

facebook_app_id = '790386739292928'
facebook_app_secret = '1fbdba2c1b8aa8fdde6fdb235c3a64f9'
facebook_page_id = '102184052964144'
facebook_page_access_token = 'EAALO2kDUqwABABewD8rhC15NR5KZAVQLWEoCBMmhOmx7JTN5PkNHrklWrOaHRlIKnAXPRjqYkUIBZAzdfE1DJPk1ffLTPxtZCSzZARNCT2xirrBHHrpG3pkSxfLZCfbxbxceDFmWBCyZBdsjEYUwVEMKWhBcwsVfto4JFBtueeiQU6LQs4U1ZBA'



class FbConnector:
    
    @staticmethod
    def post_photo(message, file):
        image_data = {
            'caption': message,
            'access_token': facebook_page_access_token
        }
        image_files = {'source': file}

        response = requests.post(f"https://graph.facebook.com/v17.0/{facebook_page_id}/photos", data=image_data, files=image_files)
        if response.status_code != 200:
            raise Exception("Request returned an error: {} {}".format(response.status_code, response.json()))
            
    @staticmethod
    def post_video(message, file):
        video_data = {
            'description': message,
            'access_token': facebook_page_access_token
        }
        video_files = {'source': file}

        response = requests.post(f"https://graph.facebook.com/v17.0/{facebook_page_id}/videos", data=video_data, files=video_files)
        if response.status_code != 200:
            raise Exception("Request returned an error: {} {}".format(response.status_code, response.json()))
    
    @staticmethod
    def post_text(message):
        text_data = {
            'message': message,
            'access_token': facebook_page_access_token
        }

        response = requests.post(f"https://graph.facebook.com/v17.0/{facebook_page_id}/feed", data=text_data)
        if response.status_code != 200:
            raise Exception("Request returned an error: {} {}".format(response.status_code, response.json()))


class TwConnector:

    @staticmethod
    def post_text(message):
        #payload = {"text": params["in_doc"]['ssText']}
        payload = {"text": message}

        auth = OAuth1Session(
            twitter_consumer_key,
            client_secret=twitter_consumer_secret,
            resource_owner_key=twitter_access_token,
            resource_owner_secret=twitter_access_token_secret,
        )

        response = auth.post("https://api.twitter.com/2/tweets", json=payload)
        if response.status_code != 201:
            raise Exception("Request returned an error: {} {}".format(response.status_code, response.text))