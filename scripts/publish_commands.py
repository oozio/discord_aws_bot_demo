import boto3
import json
import os
import requests


from time import sleep

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION")
s3 = boto3.client("s3",             
                  aws_access_key_id=AWS_ACCESS_KEY_ID, 
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY, 
                  region_name=AWS_REGION)

# discord info so we know where to publish the slash commands
APPLICATION_ID = os.environ.get("APPLICATION_ID")
TEST_SERVERS = json.loads(os.environ.get("TEST_SERVERS"))

BOT_TOKEN = os.environ.get("BOT_TOKEN")
HEADERS = {"Authorization": f"Bot {BOT_TOKEN}"}

# where is the file with the commands stored in s3?
BUCKET = os.environ.get("AWS_BUCKET")
KEY = 'commands.json'

# form the APi endpoints: https://discord.com/developers/docs/interactions/slash-commands#registering-a-command
global_url = f"https://discord.com/api/v8/applications/{APPLICATION_ID}/commands"
guild_urls = [f"https://discord.com/api/v8/applications/{APPLICATION_ID}/guilds/{test_server_id}/commands" for test_server_id in TEST_SERVERS]


def get_json(bucket, key):
    result = s3.get_object(Bucket=bucket, Key=key)
    try:
        text = result["Body"].read().decode()
    except Exception as e:
        print(f"Err: No file found at {bucket}/{key}: {e}")
    return json.loads(text)


def publish_command(url, commands):
    r = requests.post(url, headers=HEADERS, json=commands)
    if r.status_code != 200:
        # pinging the endpoint too frequently causes it to fail; wait and retry
        sleep(20)
        print(f"Post to {url} failed; retrying once")
        r = requests.post(url, headers=HEADERS, json=commands)
        
    # debug print
    print(f"Response from {url}: {r.text}")

    
def get_all_commands(url):
    existing_commands = requests.get(url, headers=HEADERS).json()
    if not existing_commands:
        return []
    
    
def delete_command(url):
    r = requests.delete(url, headers=HEADERS)
    print(r.text)
    

def run():
    # use guild_urls to test, since global changes take effect after a delay
    # optional: delete all existing commands to reset to clean state
    # for guild_url in guild_urls:
    #    for command in get_all_commands(guild_url):
    #        delete_command(f"{guild_url}/{command['id']}")
            
    # publish new commands
    commands = get_json(BUCKET, KEY)
    for url in guild_urls:
        for command in commands:
            publish_command(url, command)

    # uncomment to publish globally
    # for command in commands:
    #     publish_command(global_url, command)
      

    print(f"{len(commands)} published")

    
if __name__ == "__main__":
    run()
