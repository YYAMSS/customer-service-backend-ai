import asyncio

import httpx

http_client = httpx.AsyncClient(timeout=5.0)


if __name__ == '__main__':
    if __name__ == '__main__':
        async def test():
            result = await http_client.get('http://localhost:8000/users/u1001/orders')
            print(result.json()['data']['orders'])

        asyncio.run(test())