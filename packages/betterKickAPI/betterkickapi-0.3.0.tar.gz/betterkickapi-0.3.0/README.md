# Python Kick API

A full implementation of the Kick API and EventSub in Python 3.9+.

Heavily inspired on [pyTwitchAPI]. My mission is to maintain parity with the [twitchAPI] library for an easier manipulation of both libraries in any project.

> [!NOTE]
> The library was intended to be called `kickAPI` to have parity with [twitchAPI], but the name is already taken. So the library was re-branded to `kick_api`.
>
> Update:\
> PyPI didn't like `kick_api`, a friend of mine recommended me `betterKickAPI`, and I liked it. So, re-branded to `betterKickAPI`.

> [!TIP]
> Also try [kickpython] that includes his own WebSocket implementation!

## Installation

Install using pip:
```
pip install betterKickAPI
```

Install using uv:
```
uv add betterKickAPI
```

<!-- ## Documentation

A full API documentation can be found on readthedocs.org. -->

## Usage

### Basic API calls

Setting up an instance of the Kick API and get your User ID.

```python
from betterKickAPI.kick import Kick
from betterKickAPI.helper import first
import asyncio

async def kick_example():
        # Initialize the kick instance, this will by default also create an app authentication for you
        kick = await Kick('APP_ID', 'APP_SECRET')

        # this returns an async generator that can be used to iterate over all results
        # but we are just interested in the first result
        # using the first helper makes this easy
        user = await first(kick.get_users(slug='your_kick_user'))
        # print the ID of your user
        print(user.broadcaster_user_id)

# run this example
asyncio.run(kick_example())
```

### Authentication

The Kick API knows 2 different authentications. App and User Authentication. Which one you need (or if one at all) depends on what calls you want to use.

###  App Authentication

```python
from betterKickAPI.kick import Kick
kick = await Kick('APP_ID', 'APP_SECRET')
```

### User Authentication

To get a user auth token, the user has to explicitly click "Allow access" on the Kick website. The library includes an Authenticator. Just remember to add `http://localhost:36571` in your redirect URIs in the [dev settings tab](https://kick.com/settings/developer).

```python
from betterKickAPI.kick import Kick
from betterKickAPI.oauth import UserAuthenticator
from betterKickAPI.type import OAuthScope

kick = await Kick('APP_ID', 'APP_SECRET')

target_scope = [OAuthScope.CHANNEL_READ]
auth = UserAuthenticator(kick, target_scope, force_verify=False)
# this will open your default browser and prompt you with the kick auth website
token, refresh_token = await auth.authenticate()

await kick.set_user_authentication(token, target_scope, refresh_token)
```

You can reuse this token and use the refresh_token to renew it:
```python
from betterKickAPI.oauth import refresh_access_token
new_token, new_refresh_token = await refresh_access_token('refresh_token', 'APP_ID', 'APP_SECRET')
```

### AuthToken refresh callback

Optionally you can set a callback for both user access token refresh and app access token refresh.

```python
from betterKickAPI.kick import Kick

async def app_refresh(token: str):
        print(f'my new ap token is:{token}')

async def user_refresh(token: str, refresh_token: str):
        print(f'my new user token is: {token}')

kick = await Kick('APP_ID', 'APP_SECRET')
kick.app_auth_refresh_callback = app_refresh
kick.user_auth_refresh_callback = user_refresh
```

### EventSub

EventSub lets you listen for events that happen on Kick.

The EventSub client runs in its own process, calling the given callback function whenever an event happens.

> [!IMPORTANT]
> At the moment, the Kick API offers Webhook as the only method to use EventSub. But there's already plans on adding WebSockets.

## TODO

- Use aiohttp instead of httpx because of performance (or another better alternative).
- Considering getting rid of socketify because of linux dependencies.
- Add documentation.
- Add EventSub WebSockets when available.

## Acknowledges

- [pyTwitchAPI]: A Python 3.7 compatible implementation of the Twitch API, EventSub and Chat.
- [KickPython]: Kick.com Python Public API Wrapper

[pyTwitchAPI]: https://github.com/Teekeks/pyTwitchAPI
[twitchAPI]: https://pypi.org/project/twitchAPI/
[KickPython]: https://github.com/berkay-digital/kickpython
