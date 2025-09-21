import requests
import time
from dotenv import load_dotenv
import os
from table_utils import print_table


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8
    return None


def collect_salaries(vacancies, predict_salary_fn):
    salaries = []
    for vacancy in vacancies:
        salary = predict_salary_fn(vacancy)
        if salary:
            salaries.append(salary)
    return salaries


def predict_rub_salary_hh(vacancy):
    salary = vacancy.get('salary')
    if not salary or salary.get('currency') != 'RUR':
        return None

    salary_from = salary.get('from')
    salary_to = salary.get('to')

    return predict_salary(salary_from, salary_to)


def get_stats_hh(languages, area=1):
    url = "https://api.hh.ru/vacancies"
    language_salaries = {}

    for lang in languages:
        salaries = []
        params = {
            'text': f'программист {lang}',
            'area': area,
            'per_page': 100,
            'page': 0
        }

        response = requests.get(url, params=params)
        if not response.ok:
            print(f"HH: Ошибка при запросе для {lang}: {response.status_code}")
            continue
        vacancies_page = response.json()

        vacancies_found = vacancies_page.get('found', 0)
        pages = vacancies_page.get('pages', 0)

        salaries += collect_salaries(vacancies_page.get('items', []), predict_rub_salary_hh)

        for page in range(1, pages):
            params['page'] = page
            response = requests.get(url, params=params)
            if not response.ok:
                break
            vacancies_page = response.json()

            salaries += collect_salaries(vacancies_page.get('items', []), predict_rub_salary_hh)
            time.sleep(0.1)

        average_salary = int(sum(salaries) / len(salaries)) if salaries else 0

        language_salaries[lang.lower()] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": len(salaries),
            "average_salary": average_salary
        }
    return language_salaries


def predict_rub_salary_superjob(vacancy):
    if vacancy.get('currency') != 'rub':
        return None

    salary_from = vacancy.get('payment_from')
    salary_to = vacancy.get('payment_to')

    return predict_salary(salary_from, salary_to)


def get_stats_superjob(api_key, languages, town_id=4):
    headers = {
        'X-Api-App-Id': api_key,
    }
    url = 'https://api.superjob.ru/2.0/vacancies/'
    language_salaries = {}

    for language in languages:
        vacancies_found = 0
        vacancies_processed = 0
        total_salary = 0
        page = 0

        while True:
            params = {
                'keyword': language,
                'town': town_id,
                'count': 20,
                'page': page,
            }
            response = requests.get(url, headers=headers, params=params)
            if not response.ok:
                print(f"SuperJob: Ошибка при запросе для {language}: {response.status_code}")
                break

            vacancies_page = response.json()

            if page == 0:
                vacancies_found = vacancies_page.get('total', 0)

            vacancies = vacancies_page.get('objects', [])
            if not vacancies:
                break

            salaries = collect_salaries(vacancies, predict_rub_salary_superjob)
            total_salary += sum(salaries)
            vacancies_processed += len(salaries)

            if not vacancies_page.get('more', False):
                break

            page += 1
            time.sleep(0.2)

        average_salary = int(total_salary / vacancies_processed) if vacancies_processed else 0

        language_salaries[language.lower()] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
        }
    return language_salaries


def main():
    load_dotenv()
    api_key = os.getenv('SUPERJOB_API_KEY')
    if not api_key:
        print("Ошибка: SUPERJOB_API_KEY не найден в переменных окружения.")
        return

    languages = ["python", "c", "c#", "c++", "java", "js", "ruby", "go", "1с"]
    hh_stats = get_stats_hh(languages)
    superjob_stats = get_stats_superjob(api_key, languages)

    print_table('HeadHunter Moscow', hh_stats)
    print("\n")
    print_table('SuperJob Moscow', superjob_stats)


if __name__ == '__main__':
    main()
