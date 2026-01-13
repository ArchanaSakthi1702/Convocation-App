import asyncio
import httpx

API_URL = "https://convocation-app.onrender.com/"  # replace with your FastAPI URL

async def call_api():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(API_URL)
            if response.status_code == 200:
                print("Success:", response.json())
            else:
                print("Failed with status code:", response.status_code)
        except Exception as e:
            print("Error occurred:", e)

async def main():
    while True:
        await call_api()
        await asyncio.sleep(35)  # wait 35 seconds before next call

if __name__ == "__main__":
    asyncio.run(main())
