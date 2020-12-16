import requests
import config

url = "https://discord.com/api/v8/applications/632580796275752984/guilds/495648733057253388/commands"


database = {
    "name": "database",
    "description": "Shows a gif from the gif database",
    
    "options": [
        {
            "name": "category",
            "description": "Specify a category",
            "type": 3,
            "required": False,
            "choices": [
                {
                    "name": "100%",
                    "value": "hundo"
                },
                {
                    "name": "Any%",
                    "value": "any"
                },
                {
                    "name": "Any% Gemskip",
                    "value": "gemskip"
                },
                {
                    "name": "Any% NoDiag",
                    "value": "any nodiag"
                },
                {
                    "name": "100% NoDiag",
                    "value": "hundo nodiag"
                },
                {
                    "name": "Min Balloons",
                    "value": "minballoon"
                }
            ]
        },
        {
            "name": "level",
            "description": "Specify a level",
            "type": 4,
            "required": False
        },
        {
            "name": "page",
            "description": "Specify a page",
            "type": 4,
            "required": False
        },
        {
            "name": "silent",
            "description": "Only show the output of this command to you",
            "type": 5,
            "required": False
        }
    ]
}

ping = {
    "name": "ping",
    "description": "Pong!"
}

categories = {
    "name": "categories",
    "description": "Shows all available categories in the TAS database"
}

tas = {
    "name": "tas",
    "description": "Shows the TAS time for a level in the TAS database",
    
    "options": [
        {
            "name": "game",
            "description": "Specify a game",
            "type": 3,
            "required": True
        },
        {
            "name": "category",
            "description": "Specify a category",
            "type": 3,
            "required": True
        },
        {
            "name": "level",
            "description": "Specify a level",
            "type": 3,
            "required": True
        },
        {
            "name": "silent",
            "description": "Only show the output of this command to you",
            "type": 5,
            "required": False
        }
    ]
}

headers = {
    "Authorization": f"Bot {config.token}"
}

r = requests.post(url, headers=headers, json=database)
print(r.status_code)
r = requests.post(url, headers=headers, json=ping)
print(r.status_code)
r = requests.post(url, headers=headers, json=categories)
print(r.status_code)
r = requests.post(url, headers=headers, json=tas)
print(r.status_code)