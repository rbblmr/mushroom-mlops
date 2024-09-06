import os
import requests
import argparse

from base64 import b64encode
from nacl import encoding, public

def encrypt(public_key: str, secret_value: str) -> str:
  """Encrypt a Unicode string using the public key."""
  public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
  sealed_box = public.SealedBox(public_key)
  encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
  return b64encode(encrypted).decode("utf-8")


def parse_env_file(filepath):
    env = {}
    with open(filepath, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', maxsplit=1)
                env[key] = value
    
    del env['GITHUB_TOKEN']
    
    return env

def create_update_secrets(secret_name, secret_value, public_key, public_key_id, token, repo, owner):
    headers={
        "Accept":"application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    data = {
        'encrypted_value' : encrypt(public_key, secret_value),
        'key_id' : public_key_id
    }
    
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code in [201, 204]:
        print(f"Successfully created or updated {secret_name} secret")
    else:
        print(response.status_code)

def get_public_key(token, repo, owner):
    headers={
        "Accept":"application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()['key_id'], response.json()['key']
    else:
        print(response.status_code)

if __name__ == "__main__":
    
    parser=argparse.ArgumentParser(description='Parsing repo name and owner')
    parser.add_argument('--env-path')
    parser.add_argument("--repo", type=str, default='mushroom-mlops')
    parser.add_argument("--owner", type=str, default='mushroom-mlops')
    
    args = parser.parse_args()
    env_path = args.env_path
    repo = args.repo
    owner = args.owner
    
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    env = parse_env_file(env_path)
    public_key_id, public_key = get_public_key(GITHUB_TOKEN, repo, owner)
    for secret_name, secret_value in env.items():
        create_update_secrets(secret_name, secret_value, public_key, public_key_id, GITHUB_TOKEN, repo, owner)