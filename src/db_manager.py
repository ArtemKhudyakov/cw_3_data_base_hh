import os
import pathlib as p
import time
from typing import Dict, Optional

import psycopg2
from dotenv import load_dotenv

from src.external_api import HeadHunterApi


class DBManager:
    def __init__(self, db_name: str, host: str = "localhost", user: str = "postgres", port: str = "5432") -> None:
        current_file_path = p.Path(__file__).resolve()
        project_root_path = current_file_path.parent.parent
        load_dotenv(dotenv_path=f"{project_root_path}/.env", encoding="utf-8")
        self.__host: str = host
        self.__db_name: str = db_name
        self.__user: str = user
        self.__password: Optional[str] = os.getenv("DB_PASSWORD")
        self.__port: str = port

    def __repr__(self) -> str:
        return f"DBManager(db_name={self.__db_name}, host={self.__host}, user={self.__user})"

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def password(self) -> Optional[str]:
        return self.__password

    @password.setter
    def password(self, password: str) -> None:
        self.__password = password

    def create_db(self) -> None:

        conn = psycopg2.connect(
            database="postgres", password=self.__password, user=self.__user, host=self.__host, port=self.__port
        )
        conn.autocommit = True

        cur = conn.cursor()

        try:
            cur.execute(f"CREATE DATABASE {self.__db_name}")
            print("База данных успешно создана")

        except psycopg2.errors.DuplicateDatabase:
            print(f"База данных {self.__db_name} уже существует")

        except Exception as e:
            print(f"Произошла ошибка при создании базы данных: {e}")

        finally:
            cur.close()
            conn.close()

    def connect_to_db(self) -> tuple[psycopg2.extensions.cursor, psycopg2.extensions.connection]:
        conn = psycopg2.connect(
            database=self.__db_name, password=self.__password, user=self.__user, host=self.__host, port=self.__port
        )
        cur = conn.cursor()
        print("Соединение с базой данных установлено")
        return cur, conn

    def close_db(self, cur: psycopg2.extensions.cursor, conn: psycopg2.extensions.connection) -> None:
        cur.close()
        conn.close()
        print("Соединение с базой данных закрыто")

    def create_table(
        self,
        table_name: str,
        columns: Dict[str, str],
        cur: psycopg2.extensions.cursor,
        conn: psycopg2.extensions.connection,
        constraints: Optional[list[str]] = None,
    ) -> str:
        """Создание таблицы с указанными колонками и ограничениями:
        param columns: Словарь {имя_колонки: тип_данных}
        Пример: {'id': 'SERIAL PRIMARY KEY', 'name': 'VARCHAR(50)'}
        param constraints: Список ограничений (FOREIGN KEY и др.)
        Пример: ['FOREIGN KEY (employer_id) REFERENCES employers(hh_id)']"""

        conn.autocommit = True

        try:
            columns_definition = ", ".join([f"{name} {type_}" for name, type_ in columns.items()])

            # Добавляем ограничения, если они есть
            constraints_definition = ""
            if constraints:
                constraints_definition = ", " + ", ".join(constraints)

            cur.execute(
                f"""CREATE TABLE {table_name}
                            ({columns_definition}{constraints_definition})
                            """
            )
            print(f"Таблица {table_name} успешно создана")

        except psycopg2.errors.DuplicateTable:
            print(f"Таблица {table_name} уже существует")

        except Exception as e:
            print(f"Произошла ошибка при создании таблицы: {e}")

        return table_name

    def fill_employers_table(
        self,
        table_name: str,
        emp_name: str,
        employer_id: str,
        cur: psycopg2.extensions.cursor,
        conn: psycopg2.extensions.connection,
    ) -> None:
        employer = HeadHunterApi(emp_name, {"text": f"{emp_name}", "page": "0", "per_page": "100"})
        employers_data = employer.load_employers()
        data = {}
        for emp in employers_data["items"]:
            if emp["id"] == employer_id:
                data["hh_id"] = emp["id"]  # Теперь hh_id будет primary key
                data["name"] = emp["name"]
                data["number_of_vacancies"] = emp["open_vacancies"]
                print("Работодатель найден")

        if not data:
            print(f"Работодатель с ID {employer_id} не найден")
            return

        conn.autocommit = True
        try:
            # Проверяем существование записи по hh_id
            cur.execute(f"SELECT 1 FROM {table_name} WHERE hh_id = %s", (data["hh_id"],))
            exists = cur.fetchone()

            if exists:
                query = f"""UPDATE {table_name} SET name = %s, number_of_vacancies = %s WHERE hh_id = %s"""
                cur.execute(query, (data["name"], data["number_of_vacancies"], data["hh_id"]))
                print(f"Данные работодателя {data['name']} обновлены")
            else:
                columns = ", ".join(data.keys())
                values = ", ".join(["%s"] * len(data))
                query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
                cur.execute(query, tuple(data.values()))
                print(f"Данные работодателя {data['name']} добавлены")
        except Exception as e:
            conn.rollback()
            print(f"Ошибка при добавлении данных: {e}")

    def fill_default_vacancies_table(
        self,
        vacancies_table: str,
        employers_table: str,
        cur: psycopg2.extensions.cursor,
        conn: psycopg2.extensions.connection,
        per_page: int = 100,  # Количество вакансий на странице (макс. 100 по API HH)
    ) -> None:
        """Заполнение таблицы вакансиями для всех работодателей из таблицы employers"""

        # Получаем список всех hh_id работодателей из таблицы employers
        cur.execute(f"SELECT hh_id FROM {employers_table}")
        employer_ids = [row[0] for row in cur.fetchall()]

        if not employer_ids:
            print("В таблице employers нет работодателей")
            return

        conn.autocommit = True
        total_vacancies = 0

        for employer_id in employer_ids:
            try:
                page = 0
                while True:
                    hh_api = HeadHunterApi("", {"employer_id": employer_id})
                    vacancies_data = hh_api.load_employer_vacancies(
                        employer_id, {"page": str(page), "per_page": str(per_page)}
                    )

                    if not vacancies_data.get("items"):
                        if page == 0:
                            print(f"Для работодателя {employer_id} не найдено вакансий")
                        break

                    for vacancy in vacancies_data["items"]:
                        data = {
                            "hh_id": vacancy["id"],
                            "employer_id": employer_id,
                            "name": vacancy["name"],
                            "salary_from": vacancy["salary"]["from"] if vacancy.get("salary") else None,
                            "salary_to": vacancy["salary"]["to"] if vacancy.get("salary") else None,
                            "currency": vacancy["salary"]["currency"] if vacancy.get("salary") else None,
                            "url": vacancy["alternate_url"],
                            "requirements": vacancy["snippet"]["requirement"],
                            "responsibility": vacancy["snippet"]["responsibility"],
                            "published_at": vacancy["published_at"],
                        }

                        # Проверяем существование записи
                        cur.execute(f"SELECT 1 FROM {vacancies_table} WHERE hh_id = %s", (data["hh_id"],))
                        exists = cur.fetchone()

                        if exists:
                            query = f"""UPDATE {vacancies_table}
                            SET name = %s, salary_from = %s, salary_to = %s, currency = %s,
                            url = %s, requirements = %s, responsibility = %s, published_at = %s
                            WHERE hh_id = %s"""
                            cur.execute(
                                query,
                                (
                                    data["name"],
                                    data["salary_from"],
                                    data["salary_to"],
                                    data["currency"],
                                    data["url"],
                                    data["requirements"],
                                    data["responsibility"],
                                    data["published_at"],
                                    data["hh_id"],
                                ),
                            )
                        else:
                            columns = ", ".join(data.keys())
                            values = ", ".join(["%s"] * len(data))
                            query = f"INSERT INTO {vacancies_table} ({columns}) VALUES ({values})"
                            cur.execute(query, tuple(data.values()))

                    count = len(vacancies_data["items"])
                    total_vacancies += count
                    print(f"Добавлено/обновлено {count} вакансий для работодателя {employer_id} (страница {page + 1})")

                    # Проверяем, есть ли еще страницы
                    pages = vacancies_data.get("pages", 0)
                    if page >= pages - 1:
                        break
                    page += 1
                    if page > 0 and page % 10 == 0:
                        time.sleep(5)  # Увеличенная пауза
                    else:
                        time.sleep(0.3)  # Обычная пауза
            except Exception as e:
                print(f"Ошибка при обработке вакансий для работодателя {employer_id}: {e}")
                continue

        print(f"\nВсего обработано вакансий: {total_vacancies}")

    def update_employer_vacancies(
        self,
        vacancies_table: str,
        employer_id: str,
        cur: psycopg2.extensions.cursor,
        conn: psycopg2.extensions.connection,
        per_page: int = 100,  # Количество вакансий на странице (макс. 100 по API HH)
    ) -> None:
        """Обновляет вакансии только для указанного работодателя"""

        if not employer_id:
            print("Не указан ID работодателя")
            return

        conn.autocommit = True
        total_vacancies = 0

        try:
            page = 0
            while True:
                hh_api = HeadHunterApi("", {"employer_id": employer_id})
                vacancies_data = hh_api.load_employer_vacancies(
                    employer_id, {"page": str(page), "per_page": str(per_page)}
                )

                if not vacancies_data.get("items"):
                    if page == 0:
                        print(f"Для работодателя {employer_id} не найдено вакансий")
                    break

                for vacancy in vacancies_data["items"]:
                    data = {
                        "hh_id": vacancy["id"],
                        "employer_id": employer_id,
                        "name": vacancy["name"],
                        "salary_from": vacancy["salary"]["from"] if vacancy.get("salary") else None,
                        "salary_to": vacancy["salary"]["to"] if vacancy.get("salary") else None,
                        "currency": vacancy["salary"]["currency"] if vacancy.get("salary") else None,
                        "url": vacancy["alternate_url"],
                        "requirements": vacancy["snippet"]["requirement"],
                        "responsibility": vacancy["snippet"]["responsibility"],
                        "published_at": vacancy["published_at"],
                    }

                    # Проверяем существование записи
                    cur.execute(f"SELECT 1 FROM {vacancies_table} WHERE hh_id = %s", (data["hh_id"],))
                    exists = cur.fetchone()

                    if exists:
                        query = f"""UPDATE {vacancies_table}
                        SET name = %s, salary_from = %s, salary_to = %s, currency = %s,
                        url = %s, requirements = %s, responsibility = %s, published_at = %s
                        WHERE hh_id = %s"""
                        cur.execute(
                            query,
                            (
                                data["name"],
                                data["salary_from"],
                                data["salary_to"],
                                data["currency"],
                                data["url"],
                                data["requirements"],
                                data["responsibility"],
                                data["published_at"],
                                data["hh_id"],
                            ),
                        )
                    else:
                        columns = ", ".join(data.keys())
                        values = ", ".join(["%s"] * len(data))
                        query = f"INSERT INTO {vacancies_table} ({columns}) VALUES ({values})"
                        cur.execute(query, tuple(data.values()))

                count = len(vacancies_data["items"])
                total_vacancies += count
                print(f"Добавлено/обновлено {count} вакансий для работодателя {employer_id} (страница {page + 1})")

                # Проверяем, есть ли еще страницы
                pages = vacancies_data.get("pages", 0)
                if page >= pages - 1:
                    break
                page += 1
                if page > 0 and page % 10 == 0:
                    time.sleep(5)  # Увеличенная пауза
                else:
                    time.sleep(0.3)  # Обычная пауза

        except Exception as e:
            print(f"Ошибка при обработке вакансий для работодателя {employer_id}: {e}")

        print(f"\nВсего обработано вакансий для работодателя {employer_id}: {total_vacancies}")

    def get_companies_with_vacancies_count(self, cur: psycopg2.extensions.cursor) -> list[tuple]:
        """
        Получает список всех компаний и количество вакансий у каждой компании

        :return: Список кортежей вида (название_компании, количество_вакансий)
        """
        try:
            query = """
                SELECT e.name, COUNT(v.hh_id) as vacancies_count
                FROM employers e
                LEFT JOIN vacancies v ON e.hh_id = v.employer_id
                GROUP BY e.name
                ORDER BY vacancies_count DESC
            """
            cur.execute(query)
            return cur.fetchall()

        except Exception as e:
            print(f"Ошибка при получении списка компаний: {e}")
            return []

    def get_all_vacancies(self, cur: psycopg2.extensions.cursor) -> list[dict]:
        """
        Получает список всех вакансий с указанием:
        - Название компании
        - Название вакансии
        - Зарплата
        - Ссылка на вакансию

        Возвращает: Список словарей с информацией о вакансиях
        """
        try:
            query = """
            SELECT e.name AS company_name, v.name AS vacancy_name, v.salary_from, v.salary_to, v.currency, v.url
            FROM vacancies v JOIN employers e ON v.employer_id = e.hh_id
            ORDER BY e.name, v.name"""

            cur.execute(query)
            rows = cur.fetchall()

            # Форматируем результат
            vacancies = []
            for row in rows:
                salary_from, salary_to, currency = row[2], row[3], row[4]

                # Форматирование зарплаты
                salary_str = ""
                if salary_from is not None or salary_to is not None:
                    if salary_from and salary_to:
                        salary_str = f"{salary_from} - {salary_to} {currency}"
                    elif salary_from:
                        salary_str = f"от {salary_from} {currency}"
                    elif salary_to:
                        salary_str = f"до {salary_to} {currency}"
                else:
                    salary_str = "не указана"

                vacancies.append({"company": row[0], "position": row[1], "salary": salary_str, "url": row[5]})

            return vacancies

        except Exception as e:
            print(f"Ошибка при получении списка вакансий: {e}")
            return []

    def get_avg_salary(self, cur: psycopg2.extensions.cursor) -> float:
        """
        Получает среднюю зарплату по всем вакансиям

        :return: Средняя зарплата (среднее между salary_from и salary_to)
                 или 0, если нет данных о зарплатах
        """
        try:
            # SQL-запрос, который вычисляет среднее значение между salary_from и salary_to
            query = """
            SELECT AVG(
            CASE WHEN salary_from IS NOT NULL AND
            salary_to IS NOT NULL THEN (salary_from + salary_to) / 2
            WHEN salary_from IS NOT NULL
            THEN salary_from
            WHEN salary_to IS NOT NULL
            THEN salary_to ELSE NULL END)
            as avg_salary FROM vacancies
            WHERE salary_from IS NOT NULL
            OR salary_to IS NOT NULL"""
            cur.execute(query)
            result = cur.fetchone()[0]

            return round(float(result), 2) if result else 0.0

        except Exception as e:
            print(f"Ошибка при расчете средней зарплаты: {e}")
            return 0.0

    def get_vacancies_with_higher_salary(self, cur: psycopg2.extensions.cursor) -> list[dict]:
        """
        Получает список вакансий с зарплатой выше средней по всем вакансиям

        :return: Список словарей с информацией о вакансиях (компания, должность, зарплата, ссылка)
        """
        try:
            # Сначала получаем среднюю зарплату
            avg_salary = self.get_avg_salary(cur)
            if avg_salary == 0:
                print("Нет данных о зарплатах для сравнения")
                return []

            # SQL-запрос для поиска вакансий с зарплатой выше средней
            query = """SELECT e.name AS company_name, v.name AS vacancy_name,
            v.salary_from, v.salary_to, v.currency, v.url
            FROM vacancies v JOIN employers e ON v.employer_id = e.hh_id
            WHERE (v.salary_from > %s OR v.salary_to > %s)
            AND (v.salary_from IS NOT NULL OR v.salary_to IS NOT NULL)
            ORDER BY GREATEST (COALESCE(v.salary_from, 0), COALESCE(v.salary_to, 0))
            DESC"""

            cur.execute(query, (avg_salary, avg_salary))
            rows = cur.fetchall()

            # Форматируем результат аналогично get_all_vacancies()
            vacancies = []
            for row in rows:
                salary_from, salary_to, currency = row[2], row[3], row[4]

                if salary_from and salary_to:
                    salary_str = f"{salary_from} - {salary_to} {currency}"
                elif salary_from:
                    salary_str = f"от {salary_from} {currency}"
                else:
                    salary_str = f"до {salary_to} {currency}"

                vacancies.append({"company": row[0], "position": row[1], "salary": salary_str, "url": row[5]})

            return vacancies

        except Exception as e:
            print(f"Ошибка при получении вакансий с высокой зарплатой: {e}")
            return []

    def get_vacancies_with_keyword(self, cur: psycopg2.extensions.cursor, keyword: str) -> list[dict]:
        """
        Получает список вакансий, в названии которых содержится указанное слово

        :param keyword: Ключевое слово для поиска (например "python")
        :return: Список словарей с информацией о вакансиях
                 (компания, должность, зарплата, ссылка)
        """
        try:
            # Формируем шаблон поиска (регистронезависимый)
            search_pattern = f"%{keyword.lower()}%"

            query = """SELECT e.name AS company_name, v.name AS vacancy_name,
            v.salary_from, v.salary_to, v.currency, v.url
            FROM vacancies v JOIN employers e ON v.employer_id = e.hh_id
            WHERE LOWER(v.name) LIKE %s OR LOWER(e.name) LIKE %s ORDER BY e.name, v.name"""

            cur.execute(query, (search_pattern, search_pattern))
            rows = cur.fetchall()

            # Форматируем результат аналогично предыдущим методам
            vacancies = []
            for row in rows:
                salary_from, salary_to, currency = row[2], row[3], row[4]

                if salary_from is not None and salary_to is not None:
                    salary_str = f"{salary_from} - {salary_to} {currency}"
                elif salary_from is not None:
                    salary_str = f"от {salary_from} {currency}"
                elif salary_to is not None:
                    salary_str = f"до {salary_to} {currency}"
                else:
                    salary_str = "не указана"

                vacancies.append({"company": row[0], "position": row[1], "salary": salary_str, "url": row[5]})

            return vacancies

        except Exception as e:
            print(f"Ошибка при поиске вакансий по ключевому слову: {e}")
            return []
