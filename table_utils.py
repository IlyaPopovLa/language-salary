from terminaltables import AsciiTable

def print_table(title, stats):
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

    if 'HeadHunter' in title:
        print('+HeadHunter Moscow------+------------------+---------------------+------------------+')
    elif 'SuperJob' in title:
        print('+SuperJob Moscow--------+------------------+---------------------+------------------+')
    else:
        print(f"=== {title} ===")

    print(table.table)
