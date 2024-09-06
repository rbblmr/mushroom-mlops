#!/usr/bin/env python3

import os
import json
import random
import logging
import requests
import traceback
import pandas as pd

from tabulate import tabulate

os.makedirs('logs', exist_ok=True)
log_file = "logs/app"

logging.basicConfig(
    format="%(asctime)s|%(name)s|%(levelname)s|%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, mode='a')
    ]
)

logging.getLogger().handlers[0].setLevel(logging.DEBUG)
logging.getLogger().handlers[1].setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

host = "http://localhost:9696/predict"

count = 0
while count < 12:
    data = {
        'id': random.randint(3300, 6000),
        'cap-shape': random.choice([
            'f', 'x', 'p', 'b', 'o', 'c', 's', 'd', 'e', 'n', 'unknown', 
            'w', 'k', 'l', 't', 'g', 'z', 'a', 'r', 'u', 'y', 'i', 'm', 'h'
            ]),
        'cap-surface': random.choice([
            's', 'h', 'y', 'l', 't', 'e', 'g', 'unknown', 'd', 'i', 'w', 
            'k', 'f', 'n', 'r', 'o', 'a', 'u', 'z', 'p', 'b', 'm', 'x', 'c'
            ]),
        'cap-color': random.choice([
            'u', 'o', 'b', 'g', 'w', 'n', 'e', 'y', 'r', 'p', 'k', 'l', 
            'i', 'h', 'd', 's', 'a', 'f', 'unknown', 'c', 'x', 'm', 'z', 't'
            ]),
        'does-bruise-or-bleed': random.choice([
            'f', 't', 'd', 'unknown', 'w', 'o', 'b', 'x', 'p', 'g', 'y', 
            'r', 'a', 'l', 'i', 'c', 'n', 'z', 's', 'k', 'h', 'e', 'u'
            ]),
        'gill-attachment': random.choice([
            'a', 'x', 's', 'd', 'e', 'unknown', 'f', 'p', 'l', 'm', 'b', 
            'n', 'g', 'i', 'u', 't', 'o', 'c', 'w', 'k', 'r', 'h', 'z', 'y'
            ]),
        'gill-spacing': random.choice([
            'c', 'unknown', 'd', 'f', 'x', 'b', 'a', 'k', 'e', 'y', 's', 
            'p', 't', 'i', 'w', 'h', 'l', 'r', 'n', 'g'
            ]),
        'gill-color': random.choice([
            'w', 'n', 'g', 'k', 'y', 'f', 'p', 'o', 'b', 'u', 'e', 'r', 
            'd', 't', 'unknown', 'z', 'h', 'x', 's', 'c', 'm', 'l', 'a', 'i'
            ]),
        'stem-root': random.choice([
            'unknown', 'b', 'c', 'r', 's', 'f', 'y', 'o', 'k', 'd', 'n', 
            'w', 'u', 'p', 'x', 'i', 'a', 't', 'm', 'l', 'h', 'g', 'e', 'z'
            ]),
        'stem-surface': random.choice([
            'unknown', 'y', 's', 't', 'g', 'h', 'k', 'i', 'f', 'l', 'd', 
            'x', 'w', 'a', 'o', 'c', 'n', 'm', 'e', 'p', 'z', 'b', 'r', 'u'
            ]),
        'stem-color': random.choice([
            'w', 'o', 'n', 'y', 'e', 'u', 'p', 'f', 'g', 'r', 'k', 'l', 
            'b', 'unknown', 't', 'z', 'a', 'h', 'd', 's', 'i', 'c', 'x', 'm'
            ]),
        'veil-type': random.choice([
            'unknown', 'u', 'd', 'a', 'h', 'g', 'c', 'e', 'y', 'i', 'f', 
            't', 'w', 'p', 'b', 's', 'k', 'r', 'l', 'n'
            ]),
        'veil-color': random.choice([
            'unknown', 'n', 'w', 'k', 'y', 'e', 'u', 'p', 'd', 'g', 'r', 
            'h', 's', 't', 'c', 'o', 'i', 'f', 'a', 'b', 'l', 'z'
            ]),
        'has-ring': random.choice([
            'f', 't', 'h', 'r', 'y', 'c', 'e', 'g', 'l', 's', 'unknown', 
            'p', 'x', 'k', 'z', 'd', 'o', 'n', 'm', 'i', 'w', 'a'
            ]),
        'ring-type': random.choice([
            'f', 'z', 'e', 'unknown', 'p', 'l', 'g', 'r', 'm', 'y', 'h', 
            'o', 't', 'a', 'd', 's', 'x', 'b', 'u', 'n', 'w', 'i', 'k', 'c'
            ]),
        'spore-print-color': random.choice([
            'unknown', 'k', 'w', 'p', 'n', 'r', 'u', 'g', 't', 'f', 'd', 
            'l', 'y', 'a', 's', 'e', 'o', 'c', 'b', 'h', 'x', 'i', 'm'
            ]),
        'habitat': random.choice([
            'd', 'l', 'g', 'h', 'p', 'm', 'u', 'w', 'y', 'unknown', 'n', 
            'a', 's', 'k', 'z', 'b', 't', 'c', 'e', 'r', 'f', 'o', 'x', 'i'
            ]),
        'season': random.choice([
            'a', 'w', 'u', 's'
            ]),
        'cap-diameter': random.uniform(0.03, 80.67),
        'stem-height': random.uniform(0.00, 88.72),
        'stem-width': random.uniform(0.00, 102.90),
    }
    # headers={"Content-Type": "application/json"}
    # payload=json.dumps(data)
    # response=requests.post(host, headers=headers, data=payload)
    response=requests.post(host, json=data)
    if response.status_code == 200:
        logger.info(response.text)
    else:
        logger.error(f"Error encountered: {response.status_code}")
        
    count+=1