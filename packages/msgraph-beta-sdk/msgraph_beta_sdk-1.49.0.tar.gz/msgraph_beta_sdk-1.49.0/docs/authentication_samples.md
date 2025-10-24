
# DELEGATED ACCESS SAMPLES (REQUIRES SIGNED IN USER)

## 1. DEVICE CODE FLOW
```py
import asyncio

from azure.identity import DeviceCodeCredential
from msgraph_beta import GraphServiceClient

# Set the event loop policy for Windows
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Create authentication provider object. Used to authenticate requests
credential = DeviceCodeCredential(
    client_id='CLIENT_ID',
    tenant_id='TENANT_ID',
    )

scopes = ["User.Read"]

# Create an API client with the credentials and scopes.
client = GraphServiceClient(credential, scopes=scopes)

# GET A USER USING THE USER ID (GET /users/{id})
async def get_user():
    user = await client.users_by_id('USER_ID').get()
    if user:
        print(user.user_principal_name, user.display_name, user.id)
asyncio.run(get_user())
```

## 2. INTERACTIVE BROWSER FLOW

```py
import asyncio
from azure.identity import InteractiveBrowserCredential
from msgraph_beta import GraphServiceClient

# Set the event loop policy for Windows
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Create authentication provider object. Used to authenticate requests
credential = InteractiveBrowserCredential()
scopes = ["User.Read"]
# Create an API client with the credentials and scopes.
client = GraphServiceClient(credential, scopes=scopes)

# GET A USER USING THE USER ID (GET /users/{id})
async def get_user():
    user = await client.users_by_id('USER_ID').get()
    if user:
        print(user.user_principal_name, user.display_name, user.id)
asyncio.run(get_user())
```

# APPLICATION ACCESS SAMPLES (APPLICATIONS ONLY)

## 3. CLIENT SECRET CREDENTIALS FLOW

```py
import asyncio

from azure.identity import ClientSecretCredential
from msgraph_beta import GraphServiceClient

# Set the event loop policy for Windows
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) 

# Create authentication provider object. Used to authenticate request
credential = ClientSecretCredential(
    tenant_id='TENANT_ID',
    client_id='CLIENT_ID',
    client_secret='CLIENT_SECRET'
)
scopes = ['https://graph.microsoft.com/.default']

# Create an API client with the credentials and scopes.
client = GraphServiceClient(credential, scopes=scopes)

# GET A USER USING THE USER ID (GET /users/{id})
async def get_user():
    user = await client.users.by_user_id('USER_ID').get()
    if user:
        print(user.user_principal_name, user.display_name, user.id)
asyncio.run(get_user())
```

## 4. ENVIRONMENT CREDENTIAL FLOW (ASYNC)

```py
import asyncio

from azure.identity.aio import EnvironmentCredential
from msgraph_beta import GraphServiceClient

# Set the event loop policy for Windows
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Create authentication provider object. Used to authenticate request
credential = EnvironmentCredential()
scopes = ['https://graph.microsoft.com/.default']

# Create an API client with the credentials and scopes.
client = GraphServiceClient(credential, scopes=scopes)

# GET A USER USING THE USER ID (GET /users/{id})
async def get_user():
    user = await client.users.by_user_id('USER_ID').get()
    if user:
        print(user.user_principal_name, user.display_name, user.id)

asyncio.run(get_user())
