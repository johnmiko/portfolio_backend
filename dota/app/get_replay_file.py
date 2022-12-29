import requests

id = 6636281325
r = requests.get(f'https://api.opendota.com/api/matches/{id}')
data = r.json()
replay_url = data['replay_url']
# r = requests.get(replay_url)
# http://replay<cluster>.valve.net/570/<match_id>_<replay_salt>.dem.bz2
with open(f'{id}.dem.bz2', 'w') as f:
    f.write(requests.get(replay_url).content)
# r.content is the file

# http://replay<cluster>.valve.net/570/<match_id>_<replay_salt>.dem.bz2
url = 'https://api.opendota.com/api/replays?match_id=6636281325'
match_id_stuff = [{"match_id": 6636281325, "cluster": 184, "replay_salt": 394298755}]
match = match_id_stuff[0]
# url  = http://replay<cluster>.valve.net/570/<match_id>_<replay_salt>.dem.bz2
url = f'http://replay{match["cluster"]}.valve.net/570/{match["match_id"]}_{match["replay_salt"]}.dem.bz2'
