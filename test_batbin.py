import aiohttp
import asyncio
import json

async def test():
    url = "https://batbin.me/terminableness"
    link = "https://batbin.me/api/v2/paste/" + url.split("/")[-1]
    print(f"Testing link: {link}")
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as resp:
            print(f"Status: {resp.status}")
            data = await resp.read()
            print(f"Data start: {data[:100]}")
            try:
                js = json.loads(data)
                print("It is JSON!")
                if 'content' in js:
                    print("Content found!")
                else:
                    print(f"Keys: {list(js.keys())}")
            except:
                print("It is NOT JSON (likely plain text).")

if __name__ == "__main__":
    asyncio.run(test())
