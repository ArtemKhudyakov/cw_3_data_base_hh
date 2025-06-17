from colorama import Fore, Back, Style, init
from bs4 import BeautifulSoup
import textwrap
from datetime import datetime
from textwrap import fill

init(autoreset=True)  # Инициализация colorama


class APIViewer:
    @staticmethod
    def clean_html(text: str) -> str:
        """Очищает текст от HTML-тегов и лишних пробелов"""
        if not text:
            return ""
        soup = BeautifulSoup(text, "html.parser")
        return " ".join(soup.get_text().split())

    @staticmethod
    def format_date(date_str: str) -> str:
        """Форматирует дату в более читаемый вид"""
        if not date_str:
            return ""
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")

    @staticmethod
    def print_employer(employer: dict) -> None:
        """Красивый вывод информации о работодателе"""
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}РАБОТОДАТЕЛЬ:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 80}{Style.RESET_ALL}")

        print(f"{Fore.GREEN}Название:{Style.RESET_ALL} {employer.get('name', 'N/A')}")
        print(f"{Fore.GREEN}ID:{Style.RESET_ALL} {employer.get('id', 'N/A')}")
        print(f"{Fore.GREEN}Открытых вакансий:{Style.RESET_ALL} {employer.get('open_vacancies', 0)}")

        if 'logo_urls' in employer:
            print(f"\n{Fore.MAGENTA}Логотипы:{Style.RESET_ALL}")
            for size, url in employer['logo_urls'].items():
                print(f"  {size}: {url}")

        print(f"\n{Fore.BLUE}Ссылки:{Style.RESET_ALL}")
        print(f"  API: {employer.get('url', 'N/A')}")
        print(f"  Сайт: {employer.get('alternate_url', 'N/A')}")
        print(f"  Вакансии: {employer.get('vacancies_url', 'N/A')}")

        if 'employer_rating' in employer:
            rating = employer['employer_rating']
            print(f"\n{Fore.WHITE}Рейтинг:{Style.RESET_ALL} {rating.get('total_rating', 'N/A')}")
            print(f"  Отзывов: {rating.get('reviews_count', 0)}")

        print(f"{Fore.CYAN}{'-' * 80}{Style.RESET_ALL}")

    @staticmethod
    def print_vacancy(vacancy: dict) -> None:
        """Красивый вывод информации о вакансии"""
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}ВАКАНСИЯ:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 80}{Style.RESET_ALL}")

        # Основная информация
        print(f"{Fore.GREEN}Должность:{Style.RESET_ALL} {vacancy.get('name', 'N/A')}")
        print(f"{Fore.GREEN}ID:{Style.RESET_ALL} {vacancy.get('id', 'N/A')}")

        # Зарплата
        salary = vacancy.get('salary')
        if salary:
            salary_str = []
            if salary.get('from'): salary_str.append(f"от {salary['from']}")
            if salary.get('to'): salary_str.append(f"до {salary['to']}")
            if salary.get('currency'): salary_str.append(salary['currency'])
            print(f"{Fore.GREEN}Зарплата:{Style.RESET_ALL} {' '.join(salary_str)}")
        else:
            print(f"{Fore.GREEN}Зарплата:{Style.RESET_ALL} не указана")

        # Работодатель
        employer = vacancy.get('employer', {})
        print(f"\n{Fore.MAGENTA}Работодатель:{Style.RESET_ALL} {employer.get('name', 'N/A')}")
        print(f"  ID: {employer.get('id', 'N/A')}")

        # Даты
        print(f"\n{Fore.BLUE}Даты:{Style.RESET_ALL}")
        print(f"  Опубликована: {APIViewer.format_date(vacancy.get('published_at', ''))}")
        print(f"  Создана: {APIViewer.format_date(vacancy.get('created_at', ''))}")

        # Локация
        area = vacancy.get('area', {})
        print(f"\n{Fore.WHITE}Локация:{Style.RESET_ALL} {area.get('name', 'N/A')}")
        address = vacancy.get('address', {})
        if address:
            print(f"  Адрес: {address.get('raw', 'N/A')}")

        # Требования и обязанности
        snippet = vacancy.get('snippet', {})
        if 'requirement' in snippet:
            req = APIViewer.clean_html(snippet['requirement'])
            print(f"\n{Fore.WHITE}{Style.BRIGHT}Требования:{Style.RESET_ALL}")
            print(textwrap.fill(req, width=80))

        if 'responsibility' in snippet:
            resp = APIViewer.clean_html(snippet['responsibility'])
            print(f"\n{Fore.WHITE}{Style.BRIGHT}Обязанности:{Style.RESET_ALL}")
            print(textwrap.fill(resp, width=80))

        # Условия работы
        print(f"\n{Fore.CYAN}Условия:{Style.RESET_ALL}")
        print(f"  График: {vacancy.get('schedule', {}).get('name', 'N/A')}")
        print(f"  Занятость: {vacancy.get('employment', {}).get('name', 'N/A')}")
        print(f"  Опыт: {vacancy.get('experience', {}).get('name', 'N/A')}")

        # Ссылки
        print(f"\n{Fore.BLUE}Ссылки:{Style.RESET_ALL}")
        print(f"  API: {vacancy.get('url', 'N/A')}")
        print(f"  Сайт: {vacancy.get('alternate_url', 'N/A')}")
        print(f"  Отклик: {vacancy.get('apply_alternate_url', 'N/A')}")

        print(f"{Fore.CYAN}{'-' * 80}{Style.RESET_ALL}")

    @staticmethod
    def print_employers_list(employers: list[dict]) -> None:
        """Вывод списка работодателей"""
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}СПИСОК РАБОТОДАТЕЛЕЙ ({len(employers)}):{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 80}{Style.RESET_ALL}")

        for idx, emp in enumerate(employers, 1):
            print(f"{Fore.GREEN}{idx}. {emp.get('name', 'N/A')} (ID: {emp.get('id', 'N/A')})")
            print(f"   {Fore.MAGENTA}Вакансий: {emp.get('open_vacancies', 0)}")
            print(f"   {Fore.BLUE}Ссылка: {emp.get('alternate_url', 'N/A')}")

            if idx < len(employers):
                print(f"{Fore.CYAN}{'-' * 40}{Style.RESET_ALL}")

    @staticmethod
    def print_vacancies_list(vacancies: list[dict], title: str = "ВАКАНСИИ") -> None:
        """Вывод списка вакансий"""
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}{title} ({len(vacancies)}):{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 80}{Style.RESET_ALL}")

        for idx, vac in enumerate(vacancies, 1):
            # Зарплата
            salary = vac.get('salary')
            salary_str = "не указана"
            if salary:
                parts = []
                if salary.get('from'): parts.append(f"от {salary['from']}")
                if salary.get('to'): parts.append(f"до {salary['to']}")
                if salary.get('currency'): parts.append(salary['currency'])
                salary_str = ' '.join(parts)

            print(f"{Fore.GREEN}{idx}. {vac.get('name', 'N/A')}")
            print(f"   {Fore.MAGENTA}Компания: {vac.get('employer', {}).get('name', 'N/A')}")
            print(f"   {Fore.BLUE}Зарплата: {salary_str}")
            print(f"   {Fore.WHITE}Ссылка: {vac.get('alternate_url', 'N/A')}")

            if idx < len(vacancies):
                print(f"{Fore.CYAN}{'-' * 40}{Style.RESET_ALL}")

class DBViewer:
    @staticmethod
    def print_companies_with_vacancies(companies: list[tuple]) -> None:
        """Красивый вывод списка компаний с количеством вакансий"""
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}КОМПАНИИ И КОЛИЧЕСТВО ВАКАНСИЙ:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}")

        max_name_len = max(len(company[0]) for company in companies) if companies else 0

        for company in companies:
            name, count = company
            # Выравниваем названия компаний для красивого вывода
            padded_name = name.ljust(max_name_len + 2)
            print(f"{Fore.GREEN}{padded_name}{Style.RESET_ALL} {Fore.CYAN}➔{Style.RESET_ALL} "
                  f"{Fore.MAGENTA}{count}{Style.RESET_ALL} вакансий")

        print(f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}")
        total = sum(company[1] for company in companies)
        print(f"{Fore.YELLOW}Всего вакансий:{Style.RESET_ALL} {Fore.BLUE}{total}{Style.RESET_ALL}")

    @staticmethod
    def print_vacancies(vacancies: list[dict], title: str = "СПИСОК ВАКАНСИЙ") -> None:
        """Красивый вывод списка вакансий"""
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}{title}:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 100}{Style.RESET_ALL}")

        for idx, vacancy in enumerate(vacancies, 1):
            # Форматирование зарплаты с цветом
            salary_color = Fore.BLUE
            if "EUR" in vacancy['salary']:
                salary_color = Fore.GREEN
            elif "USD" in vacancy['salary']:
                salary_color = Fore.MAGENTA

            print(f"{Fore.GREEN}{idx}. {vacancy['company']}{Style.RESET_ALL}")
            print(f"   {Fore.WHITE}{Style.BRIGHT}Должность:{Style.RESET_ALL} {vacancy['position']}")
            print(
                f"   {Fore.WHITE}{Style.BRIGHT}Зарплата:{Style.RESET_ALL} {salary_color}{vacancy['salary']}{Style.RESET_ALL}")
            print(
                f"   {Fore.WHITE}{Style.BRIGHT}Ссылка:{Style.RESET_ALL} {Fore.BLUE}{vacancy['url']}{Style.RESET_ALL}")

            if idx < len(vacancies):
                print(f"{Fore.CYAN}{'-' * 50}{Style.RESET_ALL}")