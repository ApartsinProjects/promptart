from requests_oauthlib import OAuth1Session
import requests
import os


def _env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value



class FbConnector:
    
    @staticmethod
    def post_photo(message, file):
        facebook_page_id = _env("FACEBOOK_PAGE_ID")
        facebook_page_access_token = _env("FACEBOOK_PAGE_ACCESS_TOKEN")
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
        facebook_page_id = _env("FACEBOOK_PAGE_ID")
        facebook_page_access_token = _env("FACEBOOK_PAGE_ACCESS_TOKEN")
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
        facebook_page_id = _env("FACEBOOK_PAGE_ID")
        facebook_page_access_token = _env("FACEBOOK_PAGE_ACCESS_TOKEN")
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
        twitter_consumer_key = _env("TWITTER_CONSUMER_KEY")
        twitter_consumer_secret = _env("TWITTER_CONSUMER_SECRET")
        twitter_access_token = _env("TWITTER_ACCESS_TOKEN")
        twitter_access_token_secret = _env("TWITTER_ACCESS_TOKEN_SECRET")

        auth = OAuth1Session(
            twitter_consumer_key,
            client_secret=twitter_consumer_secret,
            resource_owner_key=twitter_access_token,
            resource_owner_secret=twitter_access_token_secret,
        )

        response = auth.post("https://api.twitter.com/2/tweets", json=payload)
        if response.status_code != 201:
            raise Exception("Request returned an error: {} {}".format(response.status_code, response.text))
