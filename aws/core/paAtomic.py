import time

import boto3
import elevenlabs
import replicate
# import feedparser
# from GoogleNews import GoogleNews
import requests

from serpapi import GoogleSearch

from core.paMedia import PAMedia

import openai
import os

openai.api_key = "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"
replicate_api_token = "r8_0ZnNAVC4riy7JOzHTy5vTaVOimPjTx80mLNW2"
eleven_labs_token = "c0aa69e32683ac783cf5bcb27bbcee5b"
tnl_api_key = '7463a2d2-287b-47f2-b8bf-3d0023beb872'
stability_api_key = "sk-GFvNDa4LgHgtc4AJq0UU9kVUJxWm9rhUDtkmCLVMrA6rpnae"
serp_api_key = "e3f66e22819c38ea5630ff66ed07d9566e6aaf8ded8c2b157fbd9ca06b71d6d2"

elevenlabs.set_api_key(eleven_labs_token)
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "promptart-media")


# debug transformations
def dbg_src(ctx): return {'ssText': "text output"}


def dbg_text2text(ctx): return {'ssText': ctx["in_doc"]['ssText'] + "[]"}


def dbg_text2image(ctx):
    return {'bjImage': 'image2text.jpg'}


def dbg_img2text(ctx):
    in_img = PAMedia().fetchBase64(ctx['in_doc']['bjImage'])
    return {'ssText': f"len of in image is {len(in_img)}"}


def openai_text2text(params):
    pp = {**{'n': 1, 'model': "text-davinci-003", "temperature": 0.9, "max_tokens": 2096}, **params.get('vars', {})}
    prompt = params["in_doc"]["ssText"]
    response = openai.Completion.create(**pp, prompt=prompt)
    if not response or len(response.choices) == 0:
        raise Exception("No output from `openai_text2text` transformer")
    return {**params["in_doc"], **{"ssText": response.choises[0].text.replace("\'", "''").replace("'", "’"), "prompt": prompt}}


def openai_text2image(params):
    prompt = params["in_doc"]['ssText']
    pp = {**{'n': 1, 'response_format': "b64_json", 'size': "256x256"}, **params.get("vars", {})}
    response = openai.Image.create(**pp, prompt=prompt)
    if not response or len(response["data"]) == 0:
        raise Exception("No output from `openai_text2image` transformer")
    fname = PAMedia().saveBase64(response["data"][0]["b64_json"], "jpg")
    return {**params["in_doc"], **{"bjImage": fname, 'prompt': prompt}}


def openai_speech2text(params):
    in_audio_file = params['in_doc']["bmAudio"]

    in_audio = boto3.client("s3").get_object(Bucket=S3_BUCKET, Key=in_audio_file)["Body"]
    in_audio.name = in_audio_file

    pp = {**params.get("vars", {}), **{"model": "whisper-1", "response_format": "text", "language": "en"}}
    transcript = openai.Audio.transcribe(**pp, file=in_audio)
    return {**params["in_doc"], **{"ssText": transcript, "language": "en"}}


def elevenlabs_text2speech(params):
    pp = {**params["vars"], **{"voice": "Bella", "model": "eleven_monolingual_v1"}}
    prompt = params["in_doc"]["ssText"]
    response = elevenlabs.generate(text=prompt, **pp)
    fname = PAMedia().saveBytes(response, "mp3")
    return {**params["in_doc"], **{"ssText": prompt, "bmAudio": fname}}


def salesforce_image2text(params):
    in_image_file = params["in_doc"]['bjImage']
    in_image = PAMedia().fetchBytes(in_image_file)
    res = replicate.Client(api_token=replicate_api_token) \
        .run("salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
             input={"image": in_image})
    return {**params["in_doc"], **{"ssText": res}}


def _save_rss_media(entry_media):  # Only supports images
    res = {"slImage": []}
    # print(entry_media)
    for media_obj in entry_media:
        if media_obj["medium"] != "image":
            continue
        response = requests.get(media_obj["url"], stream=True).content
        extension = media_obj["url"].split(".")[-1]
        fname = PAMedia().saveBytes(response, extension)
        res["slImage"].append(fname)
    return res


def _filter_posts(entries, since_date):
    date_format = "%d.%m.%Y %H:%M:%S"
    since_date = time.strptime(since_date, date_format)
    get_valid_entries = lambda x: (datetime := x.get("published_parsed")) and datetime >= since_date
    entries = list(filter(get_valid_entries, entries))
    return entries


# replace since_date with last n days
def rss_source(params):
    rss_url = params["vars"]['url']
    since_date = params["vars"].get('since_date')

    news_feed = feedparser.parse(rss_url)
    entries = news_feed.entries

    # Filter outdated posts
    if since_date:
        entries = _filter_posts(entries, since_date)

    # Create output + save posts media
    res = []
    for entry in entries:
        entry_dict = {"ssText": entry["title"]}
        if entry_media := entry.get("media_content"):
            media_info = _save_rss_media(entry_media)
            entry_dict.update(media_info)
        res.append(entry_dict)

    return {**{"slText": res}}


def google_news_source(params):
    language, region, period = params["vars"]["lang"], params["vars"]["region"], params["vars"]["period"]
    topic = params["in_doc"]["ssText"]
    googlenews = GoogleNews(lang=language, region=region, period=period)
    googlenews.get_news(topic)
    entries = googlenews.results(sort=True)
    res = []
    for entry in entries:
        entry_dict = {"ssText": entry["title"]}
        res.append(entry_dict)

    return {**{"slText": res}}


def google_search_source(params):
    search_request = params["in_doc"]["ssText"]
    search = GoogleSearch({
        "q": search_request,
        "api_key": serp_api_key
    })

    res = []
    for entry in search.get_dict()["organic_results"]:
        entry_dict = {"ssText": entry["title"]}
        res.append(entry_dict)

    return {**{"slText": res}}


def replicate_stable_diffusion_text2image(params):
    prompt = params["in_doc"]['ssText']
    model_version = "stability-ai/stable-diffusion:db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf"
    response = replicate.Client(api_token=replicate_api_token).run(model_version, input={"prompt": prompt})
    if len(response.choices) == 0:
        raise Exception("No output from `replicate_stable_diffusion_text2image` transformer")
    image = requests.get(response[0], stream=True).content
    extension = response[0].split(".")[-1]
    fname = PAMedia().saveBytes(image, extension)
    return {**params["in_doc"], **{"bjImage": fname, 'prompt': prompt}}


def stability_stable_diffusion_text2image(params):
    prompt = params["in_doc"]['ssText']
    engine_id = "stable-diffusion-v1-5"
    api_host = os.getenv('API_HOST', 'https://api.stability.ai')
    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {stability_api_key}"
        },
        json={
            "text_prompts": [
                {
                    "text": prompt
                }
            ],
            "cfg_scale": 7,
            "clip_guidance_preset": "FAST_BLUE",
            "height": 512,
            "width": 512,
            "samples": 1,
            "steps": 30,
        },
    )

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))
    fname = PAMedia().saveBase64(response.json()["artifacts"][0]["base64"], "jpg")
    return {**params["in_doc"], **{"bjImage": fname, 'prompt': prompt}}


class_map = {"_dbg_src": dbg_src,
             "_dbg_text2text": dbg_text2text,
             "_dbg_text2image": dbg_text2image,
             '_dbg_img2text': dbg_img2text,
             "_openai_text2text": openai_text2text,
             "_openai_text2image": openai_text2image,
             "_openai_speech2text": openai_speech2text,
             "_elevenlabs_text2speech": elevenlabs_text2speech,
             "_salesforce_image2text": salesforce_image2text,
             "_replicate_stable_diffusion_text2image": replicate_stable_diffusion_text2image,
             "_stability_stable_diffusion_text2image": stability_stable_diffusion_text2image,
             "_rss_source": rss_source,
             "_google_news_source": google_news_source,
             "_google_search_source": google_search_source
             }


def applyAtomic(name,ctx,user):
    print(f"applying atomic name={name} ctx={ctx}")
    return class_map[name](ctx)

if __name__ == "__main__":
    pp = {"voice": "Bella", "model": "eleven_monolingual_v1"}
    prompt = ""
    response = elevenlabs.generate(text=prompt, **pp)
    print(response)
    # fname = PAMedia().saveBytes(response, "mp3")
    