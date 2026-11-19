import aiohttp
import asyncio
import json
import signal
from datetime import datetime, timedelta

BRAND_API_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/getallmakes?format=json"
SPECS_API_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/GetVehicleTypesForMakeId/1?format=json"

semaphore = asyncio.Semaphore(3)

async def fetch_data(url: str, session: aiohttp.ClientSession, label: str):
    async with semaphore:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                        print(f"[OK] {label}: данные получены (status 200)")
                        return data
                    except json.JSONDecodeError:
                        print(f"[ERROR] {label}: ответ не является валидным JSON")
                        return None
                else:
                    print(f"[HTTP ERROR] {label}: статус {response.status}")
                    return None
        except asyncio.TimeoutError:
            print(f"[TIMEOUT] {label}: превышено время ожидания (5 сек)")
            return None
        except aiohttp.ClientConnectorError:
            print(f"[CONNECTION ERROR] {label}: нет подключения к серверу")
            return None
        except aiohttp.ClientError as e:
            print(f"[CLIENT ERROR] {label}: {e}")
            return None
        except Exception as e:
            print(f"[UNEXPECTED ERROR] {label}: {type(e).__name__}: {e}")
            return None

async def get_car_data():
    async with aiohttp.ClientSession() as session:
        brand_task = fetch_data(BRAND_API_URL, session, "Марки автомобилей")
        specs_task = fetch_data(SPECS_API_URL, session, "Характеристики")
        brand_data, specs_data = await asyncio.gather(brand_task, specs_task)

    return {
        "brands": brand_data,
        "specs": specs_data,
        "timestamp": datetime.now().isoformat()
    }

def save_data(data: dict, filename: str = "cars_data.json"):
    with open(filename, "a", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False) + "\n")
    print(f" Данные записаны в {filename}")

def print_results(data: dict):
    print(f"Время сбора: {data['timestamp']}")

    brands = data.get("brands")
    if brands and "Results" in brands:
        makes = brands["Results"][:5]
        print(f"\nМарки автомобилей (всего: {len(brands['Results'])}), первые 5:")
        for item in makes:
            print(f"ID {item.get('Make_ID')}: {item.get('Make_Name')}")
    else:
        print("\n Данные о марках недоступны")

    specs = data.get("specs")
    if specs and "Results" in specs:
        print(f"\nХарактеристики (типы ТС):")
        for item in specs["Results"]:
            print(f"{item.get('VehicleTypeName')}")
    else:
        print("\n Данные о характеристиках недоступны")

async def collect_once():
    data = await get_car_data()
    if data.get("brands") or data.get("specs"):
        print_results(data)
        save_data(data)
    else:
        print(" Оба запроса завершились ошибкой — данные не сохранены")
    return data

async def main(
    interval_seconds: int = 600,
    max_runtime_seconds: int = 1200,   
    max_iterations: int = None         
):
    start_time = datetime.now()
    deadline = start_time + timedelta(seconds=max_runtime_seconds)

    print(f"Старт: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Остановка по времени: {deadline.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Интервал сбора: {interval_seconds} сек\n")

    iteration = 0
    while True:
        if max_iterations is not None and iteration >= max_iterations:
            print(f"\n Достигнут лимит итераций ({max_iterations}). Завершение.")
            break

        if datetime.now() >= deadline:
            print(f"\n Истекло время работы ({max_runtime_seconds} сек). Завершение.")
            break

        iteration += 1
        print(f"\nИтерация #{iteration} — {datetime.now().strftime('%H:%M:%S')}")
        await collect_once()

        now = datetime.now()
        remaining = (deadline - now).total_seconds()

        if remaining <= 0:
            print("\n Время работы истекло. Завершение.")
            break

        sleep_time = min(interval_seconds, remaining)
        if max_iterations is not None and iteration >= max_iterations:
            print(f"\n Лимит итераций достигнут. Завершение.")
            break

        print(f"Ожидание {int(sleep_time)} сек до следующего сбора")
        await asyncio.sleep(sleep_time)

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"РАБОТА ЗАВЕРШЕНА")
    print(f"Итераций выполнено: {iteration}")
    print(f"Всего времени: {int(elapsed)} сек")

if __name__ == "__main__":
    try:
        asyncio.run(main(
            interval_seconds=600,    
            max_runtime_seconds=1200,     
            max_iterations=None           
        ))
    except KeyboardInterrupt:
        print("\n Программа остановлена пользователем")