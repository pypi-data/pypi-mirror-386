# Usage Examples

## 1. Creating a Graph client
This creates a default Graph client that uses `https://graph.microsoft.com/beta` as the default base URL and default configured HTTPX client to make the requests.

```py
from azure.identity import AuthorizationCodeCredential
from msgraph_beta import GraphServiceClient

# Set the event loop policy for Windows
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

AuthorizationCodeCredential(
    tenant_id: str,
    client_id: str,
    authorization_code: str,
    redirect_uri: str
)
scopes = ['User.Read', 'Mail.ReadWrite']

# Create an API client with the credentials and scopes.
client = GraphServiceClient(credential, scopes=scopes)
```

## 2. Creating a Graph client using a custom `httpx.AsyncClient` instance

```py
from msgraph_beta import GraphRequestAdapter
from msgraph_core import GraphClientFactory

http_client = GraphClientFactory.create_with_default_middleware(client=httpx.AsyncClient())
request_adapter = GraphRequestAdapter(auth_provider, http_client)
```

## 3. Get an item from the Microsoft Graph API

This sample fetches the current signed-in user. Note that to use `/me` endpoint you need
a delegated permission. Alternatively, using application permissions, you can request `/users/[userPrincipalName]`. See [Microsoft Graph Permissions](https://docs.microsoft.com/en-us/graph/auth/auth-concepts#microsoft-graph-permissions) for more.

```py
async def get_me():
    me = await client.me.get()
    if me:
        print(me.user_principal_name, me.display_name, me.id)
asyncio.run(get_me())
```

## 4. Get a collection of items
This snippet retrieves the messages in a user's mailbox. Ensure you have the [correct permissions](https://docs.microsoft.com/en-us/graph/api/user-list-messages?view=graph-rest-1.0&tabs=http#permissions) set.
The Graph API response is deserialized into a collection of `Message` - a model class provided by the SDK.

```py
async def get_user_messages():
    messages = await (client.users.by_user_id('USER_ID').messages.get())
    if messages and messages.value:
        for msg in messages.value:
            print(msg.subject, msg.id, msg.from_)
asyncio.run(get_user_messages())
```

## 5. Passing custom request headers
Each execution method i.e. `get()`, `post()`, `put()`, `patch()`, `delete()` accepts a `RequestConfiguration` object where the request headers can be set:

```py
from msgraph_beta.generated.users.item.messages.messages_request_builder import MessagesRequestBuilder

async def get_user_messages():
    request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration()
    request_config.headers.add('Prefer', 'outlook.body-content-type="text"')

    messages = await (client.users.by_user_id('USER_ID')
                    .messages
                    .get(request_configuration=request_config))
    if messages and messages.value:
        for msg in messages.value:
            print(msg.subject, msg.id, msg.from_)
asyncio.run(get_user_messages())
```

## 6. Passing query parameters

```py
from msgraph_beta.generated.users.item.messages.messages_request_builder import MessagesRequestBuilder

async def get_5_user_messages():
    query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
        select=['subject', 'from'], skip = 2, top=5
    )
    request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
        query_parameters=query_params
    )

    messages = await (client.users.by_user_id('USER_ID')
                    .messages
                    .get(request_configuration=request_config))
    if messages and messages.value:
        for msg in messages.value:
            print(msg.subject)
asyncio.run(get_5_user_messages())
```

## 7. Get the raw http response
The SDK provides a default response handler which returns the native HTTPX response.

To get the raw response:
```py
from kiota_abstractions.native_response_handler import NativeResponseHandler
from kiota_http.middleware.options import ResponseHandlerOption
from msgraph_beta.generated.users.item.messages.messages_request_builder import MessagesRequestBuilder

async def get_user_messages():
    request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
        options=[ResponseHandlerOption(NativeResponseHandler())], )
    messages = await client.users.by_user_id('USER_ID').messages.get(request_configuration=request_config)
    print(messages.json())
asyncio.run(get_user())
```

## 8. Send an email

This sample sends an email. The request body is constructed using the provided models.
Ensure you have the [right permissions](https://docs.microsoft.com/en-us/graph/api/user-sendmail?view=graph-rest-1.0&tabs=http#permissions).

```py
from msgraph_beta import GraphServiceClient

from msgraph_beta.generated.me.send_mail.send_mail_post_request_body import SendMailPostRequestBody
from msgraph_beta.generated.models.body_type import BodyType
from msgraph_beta.generated.models.message import Message
from msgraph_beta.generated.models.email_address import EmailAddress
from msgraph_beta.generated.models.importance import Importance
from msgraph_beta.generated.models.item_body import ItemBody
from msgraph_beta.generated.models.recipient import Recipient
from msgraph_beta.generated.users.item.messages.messages_request_builder import MessagesRequestBuilder



credential = ClientSecretCredential(
    'tenant_id',
    'client_id',
    'client_secret'
)
scopes = ['Mail.Send']

# Create an API client with the credentials and scopes.
client = GraphServiceClient(credential, scopes=scopes)

async def send_mail():
    sender = EmailAddress()
    sender.address = 'john.doe@outlook.com'
    sender.name = 'John Doe'
    
    from_recipient = Recipient()
    from_recipient.email_address = sender
    recipients = []

    recipient_email = EmailAddress()
    recipient_email.address = 'jane.doe@outlook.com'
    recipient_email.name = 'Jane Doe'
    
    to_recipient = Recipient()
    to_recipient.email_address = recipient_email
    recipients.append(to_recipient) 

    email_body = ItemBody()
    email_body.content = 'Dummy content'
    email_body.content_type = BodyType.Text
    
    message = Message()
    message.subject = 'Test Email'
    message.from_escaped = from_recipient
    message.to_recipients = recipients
    message.body = email_body
    
    request_body = SendMailPostRequestBody()
    request_body.message = message
    response = await client.me.send_mail.post(request_body)
asyncio.run(send_mail())
```
