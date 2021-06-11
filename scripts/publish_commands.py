import boto3
import json
import requests


from time import sleep
s3 = boto3.client("s3")
ssm = boto3.client('ssm', region_name='us-east-2')

# discord info so we know where to publish the slash commands
APPLICATION_ID = ssm.get_parameter(Name="/discord/application_id", WithDecryption=True)['Parameter']['Value']
TEST_SERVERS = ssm.get_parameter(Name="/discord/test_servers", WithDecryption=True)['Parameter']['Value']

BOT_TOKEN = ssm.get_parameter(Name="/discord/bot_token", WithDecryption=True)['Parameter']['Value']
HEADERS = {"Authorization": f"Bot {BOT_TOKEN}"}

# where is the file with the commands stored in s3?
BUCKET = ssm.get_parameter(Name="/discord/commands_s3", WithDecryption=True)['Parameter']['Value']
KEY = 'commands.json'

# form the APi endpoints: https://discord.com/developers/docs/interactions/slash-commands#registering-a-command
global_url = f"https://discord.com/api/v8/applications/{APPLICATION_ID}/commands"
guild_urls = [f"https://discord.com/api/v8/applications/{APPLICATION_ID}/guilds/{test_server_id}/commands" for test_server_id in TEST_SERVERS]


def get_json(bucket, key):
    result = s3.get_object(Bucket=bucket, Key=key) 
    text = result["Body"].read().decode()
    return json.loads(text)


def publish_command(url, commands):
    r = requests.post(url, headers=HEADERS, json=commands)
    if r.status_code != 200:
        # pinging the endpoint too frequently causes it to fail; wait and retry
        sleep(20)
        print("retrying once")
        r = requests.post(url, headers=HEADERS, json=commands)
        
    # debug print
    print(r.text)

    
def get_all_commands(url):
    return requests.get(url, headers=HEADERS).json()
  
    
def delete_command(url):
    r = requests.delete(url, headers=HEADERS)
    print(r.text)
    
    
def lambda_handler(event, context):
    # use guild_urls to test, since global changes take effect after a delay
    
    # delete all existing commands to reset to clean state
    for guild_url in guild_urls:
        for command in get_all_commands(guild_url):
            delete_command(f"{guild_url}/{command['id']}")
        
    # publish new commands
    commands = get_json(BUCKET, KEY)
    for url in guild_urls:
        for command in commands:
            publish_command(url, command)
            
    # uncomment to publish globally
    # for command in commands:
    #     publish_command(global_url, command)
      
