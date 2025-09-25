import requests
import time
import os
from dotenv import load_dotenv
from table_utils import print_table


SUPERJOB_VACANCIES_PAGE = 20


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


def fetch_all_hh_vacancies(language, area=1):
    url = "https://api.hh.ru/vacancies"
    all_vacancies = []

    params = {
        'text': f'программист {language}',
        'area': area,
        'per_page': 100,
        'page': 0
    }

    response = requests.get(url, params=params)
    if not response.ok:
        print(f"HH: Ошибка при запросе для {language}: {response.status_code}")
        return [], 0

    vacancies_page = response.json()
    all_vacancies += vacancies_page.get('items', [])
    pages = vacancies_page.get('pages', 0)
    found = vacancies_page.get('found', 0)

    for page in range(1, pages):
        params['page'] = page
        response = requests.get(url, params=params)
        if not response.ok:
            break
        page_data = response.json()
        all_vacancies += page_data.get('items', [])
        time.sleep(0.1)

    return all_vacancies, found


def get_stats_hh(languages, area=1):
    language_salaries = {}

    for lang in languages:
        vacancies, vacancies_found = fetch_all_hh_vacancies(lang, area)
        salaries = collect_salaries(vacancies, predict_rub_salary_hh)

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


def fetch_all_sj_vacancies(api_key, language, town_id=4):
    headers = {'X-Api-App-Id': api_key}
    url = 'https://api.superjob.ru/2.0/vacancies/'
    all_vacancies = []
    page = 0
    vacancies_found = 0

    while True:
        params = {
            'keyword': language,
            'town': town_id,
            'count': SUPERJOB_VACANCIES_PAGE,
            'page': page,
        }
        response = requests.get(url, headers=headers, params=params)
        if not response.ok:
            print(f"SuperJob: Ошибка при запросе для {language}: {response.status_code}")
            break

        data = response.json()
        if page == 0:
            vacancies_found = data.get('total', 0)

        all_vacancies += data.get('objects', [])

        if not data.get('more', False):
            break

        page += 1
        time.sleep(0.2)

    return all_vacancies, vacancies_found


def get_stats_superjob(api_key, languages, town_id=4):
    language_salaries = {}

    for lang in languages:
        vacancies, vacancies_found = fetch_all_sj_vacancies(api_key, lang, town_id)
        salaries = collect_salaries(vacancies, predict_rub_salary_superjob)

        average_salary = int(sum(salaries) / len(salaries)) if salaries else 0

        language_salaries[lang.lower()] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": len(salaries),
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
    print()
    print_table('SuperJob Moscow', superjob_stats)


if __name__ == '__main__':
    main()
