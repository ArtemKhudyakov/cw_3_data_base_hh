import src.utils as utils
from src.db_manager import DBManager
from src.external_api import HeadHunterApi
from src.viewer import APIViewer, DBViewer


def main() -> None:
    print("Привет! Начинаем работу с базой данных вакансий.")
    hh_db = DBManager(db_name="hh_vacancies_db")
    hh_db.create_db()
    cur, conn = hh_db.connect_to_db()
    emp_table, vac_table = utils.fill_default_db(hh_db, cur, conn)

    while True:
        print("""Выберите действие которое хотите выполнить""")
        action = input(
            """
        1. Вывести список компаний из базы данных.
        2. Вывести все вакансии из базы данных.
        3. Вывести среднюю зарплату из базы данных вакансий.
        4. Вывести вакансии с зарплатой выше средней.
        5. Вывести вакансии по ключевому слову.
        6. Поиск работодателей и вакансий на внешнем ресурсе.
        7. Добавить работодателя и вакансии в базу данных
        8. Выход
        """
        )
        if action == "1":
            companies = hh_db.get_companies_with_vacancies_count(cur)
            DBViewer.print_companies_with_vacancies(companies)
        elif action == "2":
            all_vacancies = hh_db.get_all_vacancies(cur)
            DBViewer.print_vacancies(all_vacancies)
        elif action == "3":
            avg_salary = hh_db.get_avg_salary(cur)
            print(
                f"""Средняя зарплата из всех вакансий базы данных
{avg_salary}

"""
            )
        elif action == "4":
            higher_salary = hh_db.get_vacancies_with_higher_salary(cur)
            DBViewer.print_vacancies(higher_salary)
        elif action == "5":
            keyword = input(
                """
            Введите ключевое слово для поиска вакансий
            """
            )
            vacancies_by_key_word = hh_db.get_vacancies_with_keyword(cur, keyword)
            DBViewer.print_vacancies(vacancies_by_key_word)

        elif action == "6":
            emp_name = HeadHunterApi.employer_name()
            emp_name_str = emp_name["text"]
            page_view = HeadHunterApi.page_view()
            params = HeadHunterApi.set_employers_params(emp_name, page_view)
            emp = HeadHunterApi(emp_name_str, params)
            emp_data = emp.load_employers()
            employers_list = emp_data["items"]
            APIViewer.print_employers_list(employers_list)
            vacancies = emp.load_employer_vacancies()
            for vacancy in vacancies["items"]:
                APIViewer.print_vacancy(vacancy)

        elif action == "7":
            emp_name = input("\nВведите наименование компании\n")
            employer_id = input("\nВведите ID компании\n")
            hh_db.fill_employers_table(emp_table, emp_name, employer_id, cur, conn)
            hh_db.update_employer_vacancies(vac_table, employer_id, cur, conn)

        elif action == "8":
            break
        else:
            continue

    DBManager.close_db(hh_db, cur, conn)
    print("Выход из программы!")


if __name__ == "__main__":
    main()
