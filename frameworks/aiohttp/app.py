import asyncio
import json as JSON
import os

import aiohttp_jinja2
import aiohttp
import uvloop
import jinja2
import peewee
import peewee_async
from aiohttp import ClientSession

# loop = asyncio.get_event_loop()

HOST = os.environ.get('DHOST', '127.0.0.1')

database = peewee_async.PooledPostgresqlDatabase(
  'benchmark', max_connections=1000, user='benchmark', password='benchmark', host=HOST)


objects = peewee_async.Manager(database)

class Message(peewee.Model):
    content = peewee.CharField(max_length=512)

    class Meta:
        database = database


@asyncio.coroutine
def json(request):
    return aiohttp.web.Response(
        text=JSON.dumps({'message': 'Hello, World!'}), content_type='application/json')


@asyncio.coroutine
def remote(request):
    response = yield from request.app["session"].request('GET', 'http://%s' % HOST) # noqa
    text = yield from response.text()
    return aiohttp.web.Response(text=text, content_type='text/html')


@asyncio.coroutine
def complete(request):
    # messages = yield from peewee_async.execute(Message.select().order_by(peewee.fn.Random()).limit(100))
    messages = yield from peewee_async.execute(Message.select().order_by(peewee.fn.Random()).limit(100))
    # messages = yield from objects.execute(Message.select().order_by(peewee.fn.Random()).limit(100))
    messages = list(messages)
    messages.append(Message(content='Hello, World!'))
    content = [{"id": m.id, "content": m.content} for m in messages]
    return aiohttp.web.Response(
        text=JSON.dumps(content)
    )

async def on_startup(app):
    connector = aiohttp.TCPConnector(limit=1000)
    app["session"] = ClientSession(connector=connector)

app = aiohttp.web.Application()
app.router.add_route('GET', '/json', json)
app.router.add_route('GET', '/remote', remote)
app.router.add_route('GET', '/complete', complete)
app.on_startup.append(on_startup)

loop = uvloop.new_event_loop()
asyncio.set_event_loop(loop)
aiohttp_jinja2.setup(
    app, loader=jinja2.FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))
# loop.run_until_complete(database.connect_async(loop=loop))
