import asyncio
from KumsalTR.core.youtube import YouTube
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    yt = YouTube()
    video_id = "dQw4w9WgXcQ" # Rickroll
    print(f"Testing download for {video_id}...")
    url = await yt.download(video_id)
    if url:
        print(f"SUCCESS: Got URL: {url[:50]}...")
    else:
        print("FAILED: Could not get URL.")

if __name__ == "__main__":
    asyncio.run(test())
