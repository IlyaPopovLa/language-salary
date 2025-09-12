import requests
import time
import json


def predict_rub_salary(vacancy):
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


languages = [
    "Python", "Java", "JavaScript", "C++", "C#", "Go", "Ruby", "Kotlin",
    "Swift", "TypeScript", "PHP", "Rust"
]

results = {}

for lang in languages:
    salaries = []
    params = {
        'text': f'программист {lang}',
        'area': 1,
        'per_page': 100,
        'page': 0
    }

    response = requests.get("https://api.hh.ru/vacancies", params=params)
    data = response.json()

    vacancies_found = data.get('found', 0)
    pages = data.get('pages', 0)

    for vacancy in data.get('items', []):
        salary = predict_rub_salary(vacancy)
        if salary:
            salaries.append(salary)

    for page in range(1, pages):
        params['page'] = page
        response = requests.get("https://api.hh.ru/vacancies", params=params)
        data = response.json()

        for vacancy in data.get('items', []):
            salary = predict_rub_salary(vacancy)
            if salary:
                salaries.append(salary)

    if salaries:
        average_salary = int(sum(salaries) / len(salaries))
    else:
        average_salary = 0

    results[lang] = {
        "vacancies_found": vacancies_found,
        "vacancies_processed": len(salaries),
        "average_salary": average_salary
    }

print("Статистика")

print(json.dumps(results, ensure_ascii=False, indent=4))
