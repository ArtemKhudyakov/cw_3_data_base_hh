import psycopg2

from src.db_manager import DBManager


def create_default_db(
    data_base: DBManager, cur: psycopg2.extensions.cursor, conn: psycopg2.extensions.connection
) -> None:
    emp_table = data_base.create_table(
        "employers",
        {
            "hh_id": "VARCHAR(20) PRIMARY KEY",  # Используем hh_id как первичный ключ
            "name": "VARCHAR(100) NOT NULL",
            "number_of_vacancies": "INT",
        },
        cur,
        conn,
    )

    data_base.fill_employers_table(emp_table, "Дельтасвар", "1329403", cur, conn)
    data_base.fill_employers_table(emp_table, "ГК ПЛМ Урал", "125474", cur, conn)
    data_base.fill_employers_table(emp_table, "АСКОН", "41144", cur, conn)
    data_base.fill_employers_table(emp_table, "ЧЕЛЯБИНВЕСТБАНК", "1203065", cur, conn)
    data_base.fill_employers_table(emp_table, "Сбер Банк", "829010", cur, conn)
    data_base.fill_employers_table(emp_table, "Doubletapp", "3096092", cur, conn)
    data_base.fill_employers_table(emp_table, "Онлайн-школа Тетрика", "3731347", cur, conn)
    data_base.fill_employers_table(emp_table, "EasyCode", "8977564", cur, conn)
    data_base.fill_employers_table(emp_table, "Яндекс", "1740", cur, conn)
    data_base.fill_employers_table(emp_table, "Газпром автоматизация", "903111", cur, conn)

    vac_table = data_base.create_table(
        "vacancies",
        {
            "hh_id": "VARCHAR(20) PRIMARY KEY",
            "employer_id": "VARCHAR(20) NOT NULL",
            "name": "VARCHAR(200) NOT NULL",
            "salary_from": "INT",
            "salary_to": "INT",
            "currency": "VARCHAR(10)",
            "url": "VARCHAR(200)",
            "requirements": "TEXT",
            "responsibility": "TEXT",
            "published_at": "TIMESTAMP",
        },
        cur,
        conn,
        constraints=["FOREIGN KEY (employer_id) REFERENCES employers(hh_id)"],
    )

    data_base.fill_vacancies_table(vac_table, emp_table, cur, conn)


if __name__ == "__main__":
    hh_db = DBManager(db_name="hh_employers_db")
    cur, conn = hh_db.connect_to_db()
    # create_default_db(hh_db, cur, conn)

    companies = hh_db.get_companies_with_vacancies_count(cur)
    for company in companies:
        print(f"Компания: {company[0]}, Вакансий: {company[1]}")
    all_vacancies = hh_db.get_all_vacancies(cur)
    for v in all_vacancies:
        print(v)

    hh_db.close_db(cur, conn)
