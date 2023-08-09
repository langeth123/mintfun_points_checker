


import xlsxwriter
from datetime import datetime
from os import getcwd
from web3 import Web3
import os
from loguru import logger
import time
import aiohttp
import asyncio

URL = "https://mint.fun/api/mintfun/fundrop/"

headers = {
    'authority': 'mint.fun',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uk;q=0.6,pl;q=0.5,cy;q=0.4,fr;q=0.3',
    'cache-control': 'max-age=0',
    'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
}


async def request_mintfun_data(address: str):
    while True:
        try:
            logger.info(f'Getting info for: {address}')
            async with aiohttp.ClientSession() as session:
                response = await session.get(
                    URL + "pass?address=" + address,
                    headers=headers,
                    timeout=10
                )

                if response.status == 200:
                    response_data = await response.json()
                else:
                    response_data = {"error": True}

            logger.success(f'Got info for: {address}')

            return {
                "address"  : address,
                "response" : response_data
            }

        except Exception as error:
            logger.error(f'Failed to parse: {address} | {error}')

async def async_handler(addresses: list):
    tasks = []

    for address in addresses:
        tasks.append(asyncio.create_task(request_mintfun_data(address)))
    
    results = await asyncio.gather(*tasks)

    return results


def stats_handler(addresses: list):
    stats_path = getcwd() + '\\stats\\'
    if os.path.exists(stats_path) != True:
        os.mkdir(stats_path)
        logger.success(f'Stats path was created!')

    human_date = datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')
    workbook = xlsxwriter.Workbook(f'{stats_path}Stats_{human_date}.xlsx')
    worksheet = workbook.add_worksheet()
    worksheet.set_column('A:D', 45)


    data = [["ADDRESS", "POINTS", "STREAK DAYS", "STREAK EXP"]]

    results = asyncio.run(async_handler(addresses))

    for result in results:
        address = result["address"]
        response = result["response"]
        if "error" in response.keys():
            points, streak, streak_exp = ["NOT MINTED" for _ in range(3)]
        else:
            points = response["points"]
            streak = response["streak"]
            if streak != 0:
                streak_exp = round((datetime.fromisoformat(response["streakExpiry"][:-1] + '+00:00').timestamp() - time.time()) / 3600, 2)
            else: streak_exp = "NONE"

        data.append(
            [address, points, streak, streak_exp]
        )
    

    row, col = 0, 0

    for address_, nonce_, streak_days, streak_exp_ in data:
        worksheet.write(row, col,     address_)
        worksheet.write(row, col + 1, nonce_)
        worksheet.write(row, col + 2, streak_days)
        worksheet.write(row, col + 3, streak_exp_)
        row += 1

    workbook.close()

    logger.success(f"Check results at path: {f'{stats_path}Stats_{human_date}.xlsx'}")



if __name__ == "__main__":

    with open(getcwd() + '\\data\\to_run_addresses.txt') as file:
        runner_addresses = [
            i.replace('\n', "") for i in file.readlines()
        ]
    stats_handler(runner_addresses)
    