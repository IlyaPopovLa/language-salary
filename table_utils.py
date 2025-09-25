from terminaltables import AsciiTable

def print_table(title, stats):
    table_data = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]

    for lang, data in stats.items():
        table_data.append([
            lang,
            data.get('vacancies_found', 0),
            data.get('vacancies_processed', 0),
            data.get('average_salary', 0)
        ])

    table = AsciiTable(table_data)
    print(f'+{title:<24}+------------------+---------------------+------------------+')
    print(table.table)
