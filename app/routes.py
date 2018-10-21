import json
import os
import requests
from app import app
from app.forms import UsernameForm
from flask import Flask, flash, request, redirect, url_for
from flask import send_from_directory
from flask import render_template
from werkzeug.utils import secure_filename

HEADERS = {
    'UserAgent': 'LastFM Recommendations Enhanced Tool', 
    'From': 'kingzoloft@gmail.com'
}
LFM_API_URL = 'https://ws.audioscrobbler.com/2.0/'


@app.route('/', methods=['GET', 'POST'])
def index():
    form = UsernameForm()
    if form.validate_on_submit():
        flash('wtf does flash do?')
        return redirect(url_for('get_recs', username=form.username.data))
    return render_template('index.html', form=form)


@app.route('/css/<path:path>')
def send_css(path):
    css_path = os.path.join(app.base_path, 'css')
    return send_from_directory(css_path, path)


@app.route('/recs/<username>')
def get_recs(username):
    # get all users the user follows
    following_list = get_following(username)
    # get top artists from each of them
    user_top_artists = {}
    for user in following_list:
        user_top_artists[user] = get_top_artists(user, 25)
    merged_artist_list = list(set().union(*list(user_top_artists.values())))
    user_artist_list = get_top_artists(username, limit=None)
    # subtract user top artists from the list, though the 'long tail' is still
    # left and has to be dealt with shittily
    recs_list = list(set(merged_artist_list).difference(set(user_artist_list)))
    return render_template('recs.html', recs=recs_list)



def get_following(username):
    endpoint_url = '{}?method=user.getfriends&user={}&api_key={}&format=json'.format(LFM_API_URL,
            username, app.config['LFM_API_KEY'])
    lfm_res = requests.get(endpoint_url, headers=HEADERS)
    if not lfm_res.ok:
        abort('idk, something went wrong')
    lfm_res_dict = json.loads(lfm_res.text)
    following_list = [user['name'] for user in lfm_res_dict['friends']['user']]
    return following_list


def get_top_artists(username, limit=50):
    get_all = False
    if limit is None:
        limit = 1000
        get_all = True
    endpoint_url = '{}?method=user.gettopartists&user={}&limit={}&api_key={}&format=json'.format(LFM_API_URL,
            username, limit, app.config['LFM_API_KEY'])
    lfm_res = requests.get(endpoint_url, headers=HEADERS)
    if not lfm_res.ok:
        abort('idk, something went wrong')
    lfm_res_dict = json.loads(lfm_res.text)
    artist_list = [artist['name'] for artist in lfm_res_dict['topartists']['artist']]
    if not get_all:
        return artist_list
    else:
        page_count = int(lfm_res_dict['topartists']['@attr']['totalPages'])
        for page in range(2, page_count+1):
            # TODO: do something about the long URL
            endpoint_url = '{}?method=user.gettopartists&user={}&limit={}&page={}&api_key={}&format=json'.format(LFM_API_URL, username, limit, page, app.config['LFM_API_KEY'])
            lfm_res = requests.get(endpoint_url, headers=HEADERS)
            if not lfm_res.ok:
                abort('idk, something went wrong')
            lfm_res_dict = json.loads(lfm_res.text)
            artist_append_list = [artist['name'] for artist in lfm_res_dict['topartists']['artist']]
            artist_list = artist_list + artist_append_list
        return artist_list

