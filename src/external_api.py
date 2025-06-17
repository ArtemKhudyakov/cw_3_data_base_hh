import json
from typing import Any, Dict, Optional

import requests


class HeadHunterApi:
    """
    Класс для работы с API HeadHunter
    """

    def __init__(self, employer: str, params: Dict[str, Any]) -> None:
        self.__base_url = "https://api.hh.ru"
        self.__params = params
        self.__employer = employer
        self.headers = {"User-Agent": "HH-User-Agent"}

    def __repr__(self) -> str:
        """Возвращает строковое представление объекта"""
        return f"<HeadHunterApi employer={self.__employer}>"

    def __str__(self) -> str:
        """Возвращает строковое представление объекта"""
        return self.__repr__()

    @property
    def base_url(self) -> str:
        """Возвращает базовый URL"""
        return self.__base_url

    @property
    def params(self) -> Dict[str, Any]:
        """Возвращает введенные параметры поиска"""
        return self.__params

    @staticmethod
    def employer_name() -> Dict[str, Any]:
        """Статический метод для поиска работодателя"""
        text = input("\nВведите название компании\n")
        return {"text": text}

    @staticmethod
    def page_view() -> Dict[str, Any]:
        """Статический метод для ввода параметров поиска"""

        while True:
            try:
                page_input = input("\nВведите номер страницы\n")
                page = int(page_input)
                if page > 0:
                    page -= 1
                    break
                print("Ошибка ввода! Номер страницы должен быть положительным числом")
            except ValueError:
                print("Ошибка ввода! Введите целое число для номера страницы")

        while True:
            try:
                per_page_input = input("\nВведите количество вакансий для вывода на странице\n")
                per_page = int(per_page_input)
                if per_page > 0:
                    break
                print("Ошибка ввода! Количество вакансий должно быть положительным числом")
            except ValueError:
                print("Ошибка ввода! Введите целое число для количества вакансий")

        params: Dict[str, Any] = {
            "page": str(page),
            "per_page": str(per_page),
        }
        return params

    @staticmethod
    def set_employers_params(employer_name: Dict[str, Any], page_view: Dict[str, Any]) -> Dict[str, Any]:
        params = {**employer_name, **page_view}
        return params

    def load_employers(self) -> Any:
        url = f"{self.__base_url}/employers"

        try:
            response = requests.get(url, headers=self.headers, params=self.__params, timeout=10)

            if response.status_code != 200:
                error_msg = f"Ошибка API (код {response.status_code}): {response.text[:200]}..."
                raise ConnectionError(error_msg)

            employers = response.json()
            if not employers.get("items"):
                print("Предупреждение: не найдено ни одного работодателя с заданным именем")

        except requests.RequestException as e:
            print(f"Ошибка сетевого запроса: {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"Ошибка разбора JSON ответа: {e}")
            raise

        return employers

    def load_employer_vacancies(self, employer_id: str = "", params: Optional[Dict[str, Any]] = None) -> Any:
        if not employer_id:
            employer_id = input("\nВведите id компании для просмотра вакансий\n")
        if not params:
            params = HeadHunterApi.page_view()

        url = f"{self.__base_url}/vacancies?employer_id={employer_id}"

        try:

            response = requests.get(url, headers=self.headers, params=params, timeout=10)

            if response.status_code != 200:
                error_msg = f"Ошибка API (код {response.status_code}): {response.text[:200]}..."
                raise ConnectionError(error_msg)

            vacancies = response.json()
            if not vacancies.get("items"):
                print("Предупреждение: не найдено ни одной вакансии у данного работодателя")

        except requests.RequestException as e:
            print(f"Ошибка сетевого запроса: {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"Ошибка разбора JSON ответа: {e}")
            raise

        return vacancies
