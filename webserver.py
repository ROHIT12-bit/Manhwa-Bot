from aiohttp import web
import asyncio

async def ok(request):
    return web.Response(text="OK")

async def start_server():
    app = web.Application()
    app.router.add_get("/", ok)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)  # health check port
    await site.start()

loop = asyncio.get_event_loop()
loop.create_task(start_server())
