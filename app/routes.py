import json
import os
import requests
from app import app
from app.forms import UsernameForm
from flask import Flask, flash, request, redirect, url_for, abort
from flask import send_from_directory
from flask import render_template
from werkzeug.utils import secure_filename
from bs4 import BeautifulSoup

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


@app.route('/recs/<username>')
def get_recs(username: str, use_followers=False, use_neighbours=True):
    neighbours_list = []
    following_list = []
    if use_followers:
        # get all users the user follows
        following_list = get_following(username)
    if use_neighbours:
        # get all the user's neighbours
        neighbours_list = get_neighbours(username)
    user_list = list(set().union(following_list, neighbours_list))
    # get top artists from each of them
    user_top_artists = {}
    for user in user_list:
        user_top_artists[user] = get_top_artists(user, 15)
    merged_artist_list = list(set().union(*list(user_top_artists.values())))
    user_artist_list = get_top_artists(username, limit=None)
    # subtract user top artists from the list, though the 'long tail' is still
    # left and has to be dealt with shittily
    recs_list = list(set(merged_artist_list).difference(set(user_artist_list)))
    return render_template('recs.html', recs=recs_list)


def get_following(username: str) -> list:
    """
    Get the list of users the specified user follows
    @param username -- the username whose following list we will get
    @return list of the following usernames
    """
    endpoint_url = '{}?method=user.getfriends&user={}&api_key={}&format=json'.format(LFM_API_URL,
            username, app.config['LFM_API_KEY'])
    lfm_res = requests.get(endpoint_url, headers=HEADERS)
    if not lfm_res.ok:
        abort('idk, something went wrong')
    lfm_res_dict = json.loads(lfm_res.text)
    following_list = [user['name'] for user in lfm_res_dict['friends']['user']]
    return following_list


def get_neighbours(username: str) -> list:
    """
    Get the list of users who are neighbours of the specified user
    @param username -- the username whose neighbours we will get
    @return list of the neighbours' usernames
    """
    url = 'https://www.last.fm/user/{}/neighbours'.format(username)
    res = requests.get(url)
    if res.status_code != requests.codes.ok:
        abort('request error')
    # there's no API route for neighbours, good thing this isn't hard to do with
    # CSS selectors!
    soup = BeautifulSoup(res.text, 'html.parser')
    user_link_list = soup.select('a.user-list-link')
    user_list = [user_link.text for user_link in user_link_list]
    return user_list


def get_top_artists(username, limit=8):
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

