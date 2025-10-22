from realtimex import get_credential


async def main():
    env_vars = await get_credential("fb9f1e0c-cb77-4ca7-b5a8-18d933785312")
    print(env_vars)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
