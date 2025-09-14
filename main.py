import requests
import time
import json
from dotenv import load_dotenv
import os
from terminaltables import AsciiTable


def predict_rub_salary_hh(vacancy):
    salary = vacancy.get('salary')
    if not salary or salary.get('currency') != 'RUR':
        return None

    salary_from = salary.get('from')
    salary_to = salary.get('to')

    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8
    else:
        return None


def get_stats_hh(languages, area=1):
    url = "https://api.hh.ru/vacancies"
    results = {}

    for lang in languages:
        salaries = []
        params = {
            'text': f'программист {lang}',
            'area': area,
            'per_page': 100,
            'page': 0
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"HH: Ошибка при запросе для {lang}: {response.status_code}")
            continue
        data = response.json()

        vacancies_found = data.get('found', 0)
        pages = data.get('pages', 0)

        for vacancy in data.get('items', []):
            salary = predict_rub_salary_hh(vacancy)
            if salary:
                salaries.append(salary)

        for page in range(1, pages):
            params['page'] = page
            response = requests.get(url, params=params)
            if response.status_code != 200:
                break
            data = response.json()
            for vacancy in data.get('items', []):
                salary = predict_rub_salary_hh(vacancy)
                if salary:
                    salaries.append(salary)

            # Чтобы не перегружать API
            time.sleep(0.1)

        average_salary = int(sum(salaries) / len(salaries)) if salaries else 0

        results[lang.lower()] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": len(salaries),
            "average_salary": average_salary
        }
    return results


def print_hh_table(stats):
    table_data = [
        ['Язык программирования', 'Найдено вакансий', 'Обработано вакансий', 'Средняя зарплата']
    ]

    for lang, data in stats.items():
        table_data.append([
            lang,
            str(data.get('vacancies_found', 0)),
            str(data.get('vacancies_processed', 0)),
            str(data.get('average_salary', 0))
        ])

    table = AsciiTable(table_data)
    lines = table.table.split('\n')
    lines[0] = '+HeadHunter Moscow------+------------------+---------------------+------------------+'
    print('\n'.join(lines))


def predict_rub_salary_superjob(vacancy):
    payment_from = vacancy.get('payment_from')
    payment_to = vacancy.get('payment_to')
    currency = vacancy.get('currency')

    if currency != 'rub':
        return None

    if not payment_from and not payment_to:
        return None

    if payment_from and payment_to:
        return (payment_from + payment_to) / 2
    elif payment_from:
        return payment_from * 1.2
    elif payment_to:
        return payment_to * 0.8
    else:
        return None


def get_stats_superjob(api_key, languages, town_id=4, max_pages=5):
    headers = {
        'X-Api-App-Id': api_key,
    }
    url = 'https://api.superjob.ru/2.0/vacancies/'
    results = {}

    for language in languages:
        vacancies_found = 0
        vacancies_processed = 0
        total_salary = 0

        for page in range(max_pages):
            params = {
                'keyword': language,
                'town': town_id,
                'count': 20,
                'page': page,
            }
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                print(f"SuperJob: Ошибка при запросе для {language}: {response.status_code}")
                break

            data = response.json()

            if page == 0:
                vacancies_found = data.get('total', 0)

            vacancies = data.get('objects', [])
            if not vacancies:
                break

            for vac in vacancies:
                salary = predict_rub_salary_superjob(vac)
                if salary is not None:
                    total_salary += salary
                    vacancies_processed += 1

            if not data.get('more', False):
                break

            time.sleep(0.2)

        average_salary = int(total_salary / vacancies_processed) if vacancies_processed else 0

        results[language.lower()] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
        }
    return results


def print_superjob_table(stats):
    table_data = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]

    for lang, data in stats.items():
        table_data.append([
            lang,
            str(data.get('vacancies_found', 0)),
            str(data.get('vacancies_processed', 0)),
            str(data.get('average_salary', 0))
        ])

    table = AsciiTable(table_data)
    lines = table.table.split('\n')
    lines[0] = '+SuperJob Moscow--------+------------------+---------------------+------------------+'
    print('\n'.join(lines))


def main():
    load_dotenv()
    api_key = os.getenv('SUPERJOB_API_KEY')
    if not api_key:
        print("Ошибка: SUPERJOB_API_KEY не найден в переменных окружения.")
        return

    languages = ["python", "c", "c#", "c++", "java", "js", "ruby", "go", "1с"]
    hh_stats = get_stats_hh(languages)
    superjob_stats = get_stats_superjob(api_key, languages)

    print_hh_table(hh_stats)
    print("\n")
    print_superjob_table(superjob_stats)


if __name__ == '__main__':
    main()
