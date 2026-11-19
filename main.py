import asyncio
import json
from datetime import datetime
import aiohttp

CARS_BRANDS_API = "local://api/v1/cars/brands"
CARS_SPECS_API = "local://api/v1/cars/specifications"

async def fetch_car_data(url, session, semaphore):
    """Имитация асинхронного сетевого запроса к авто-базам данных."""
    async with semaphore:
        try:
            await asyncio.sleep(0.5)

            if "brands" in url:
                return [
                    {"name": "Toyota", "country": "Japan"},
                    {"name": "Ford", "country": "USA"},
                    {"name": "BMW", "country": "Germany"},
                    {"name": "Lada", "country": "Russia"},
                    {"name": "Kia", "country": "South Korea"},
                ]
            elif "specifications" in url:
                return {
                    "Ford Focus": {
                        "horsepower": 150,
                        "engine": "2.0L",
                        "type": "Sedan",
                    },
                    "Toyota Camry": {
                        "horsepower": 181,
                        "engine": "2.5L",
                        "type": "Sedan",
                    },
                    "BMW M5": {
                        "horsepower": 600,
                        "engine": "4.4L",
                        "type": "Sport",
                    },
                }
        except Exception as e:
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка при обработке: {e}"
            )
        return None

async def get_all_car_info(semaphore):
    async with aiohttp.ClientSession() as session:
        brands_task = fetch_car_data(CARS_BRANDS_API, session, semaphore)
        specs_task = fetch_car_data(CARS_SPECS_API, session, semaphore)

        brands_data, specs_data = await asyncio.gather(brands_task, specs_task)

        return {
            "car_brands": brands_data if brands_data is not None else [],
            "car_specifications": specs_data if specs_data is not None else {},
            "timestamp": datetime.now().isoformat(),
        }

def save_to_json(data, filename="car_data.json"):
    try:
        with open(filename, "a", encoding="utf-8") as file:
            file.write(json.dumps(data, ensure_ascii=False) + "\n")
        print(f"Данные успешно сохранены в файл {filename}")
    except Exception as e:
        print(f"Ошибка при записи в файл: {e}")

async def main():
    semaphore = asyncio.Semaphore(3)
    print("Запуск асинхронного скрипта. Ожидайте получение данных...")

    data = await get_all_car_info(semaphore)

    print(f"\n--- Результаты запроса: ---")

    brands_count = len(data["car_brands"])
    specs_count = len(data["car_specifications"])

    print(f"Успешно получено брендов автомобилей: {brands_count}")
    print(f"Успешно получено спецификаций моделей: {specs_count}")

    save_to_json(data)

if __name__ == "__main__":
    asyncio.run(main())