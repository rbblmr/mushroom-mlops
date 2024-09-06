
import requests
import random

url = "http://localhost:9696/predict"

sample_data = {
    'id':4265,
    'cap-shape':'d',
    'cap-surface':'h',
    'cap-color':'u',
    'does-bruise-or-bleed':'t',
    'gill-attachment':'u',
    'gill-spacing':'x',
    'gill-color':'u',
    'stem-root':'h',
    'stem-surface':'z',
    'stem-color':'t',
    'veil-type':'a',
    'veil-color':'g',
    'has-ring':'unknown',
    'ring-type':'g',
    'spore-print-color':'w',
    'habitat':'e',
    'season':'s',
    'cap-diameter': 25.2137,
    'stem-height': 66.9407,
    'stem-width': 23.2947,
}

response = requests.post(url, json=sample_data)

assert response['MushroomClass'] == 'not poisonous'