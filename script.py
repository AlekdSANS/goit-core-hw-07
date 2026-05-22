from collections import UserDict
from datetime import datetime, date, timedelta


# _____________________ FIELDS _____________________

class Field:
    def __init__(self, value: str | date) -> None:  # widened: Birthday stores a date, not str
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    def __init__(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank.")
        if " " in value:
            raise ValueError("Name cannot contain spaces. Use a single word name.")
        super().__init__(value)


class Phone(Field):
    def __init__(self, value: str) -> None:
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value: str) -> None:
        try:
            parsed = datetime.strptime(value, "%d.%m.%Y").date()
            super().__init__(parsed)  # stores a date; Field now accepts str | date
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self) -> str:
        return self.value.strftime("%d.%m.%Y")  # date.strftime is valid; type checker now agrees


# _____________________ RECORD _____________________

class Record:
    def __init__(self, name: str) -> None:
        self.name = Name(name)
        self.phones: list[Phone] = []
        self.birthday: Birthday | None = None

    def add_phone(self, phone: str) -> None:
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str) -> None:
        self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        for p in self.phones:
            if p.value == old_phone:
                p.value = Phone(new_phone).value
                return
        raise ValueError(f"Phone {old_phone} not found.")

    def find_phone(self, phone: str) -> Phone | None:
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday: str) -> None:
        self.birthday = Birthday(birthday)

    def __str__(self) -> str:
        phones = ", ".join(p.value for p in self.phones) or "no phones"
        birthday = str(self.birthday) if self.birthday else "not set"
        return f"Name: {self.name}, Phones: {phones}, Birthday: {birthday}"


# _____________________ ADDRESS BOOK _____________________

class AddressBook(UserDict):
    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def find(self, name: str) -> Record | None:
        return self.data.get(name, None)

    def delete(self, name: str) -> None:
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError(f"Contact '{name}' not found.")

    def get_upcoming_birthdays(self) -> list[dict]:
        today = date.today()
        upcoming = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            bday: date = record.birthday.value

            try:
                bday_this_year = bday.replace(year=today.year)
            except ValueError:
                bday_this_year = date(today.year, 3, 1)

            if bday_this_year < today:
                try:
                    bday_this_year = bday.replace(year=today.year + 1)
                except ValueError:
                    bday_this_year = date(today.year + 1, 3, 1)

            delta = (bday_this_year - today).days

            if 0 <= delta <= 7:
                weekday = bday_this_year.weekday()
                if weekday == 5:
                    congratulation_date = bday_this_year + timedelta(days=2)
                elif weekday == 6:
                    congratulation_date = bday_this_year + timedelta(days=1)
                else:
                    congratulation_date = bday_this_year

                upcoming.append({
                    "name": record.name.value,
                    "birthday": congratulation_date.strftime("%d.%m.%Y"),
                })

        return upcoming


# _____________________ DECORATOR _____________________

def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, IndexError, KeyError) as e:
            return str(e) if str(e) else "Invalid input. Please check your arguments."
    return wrapper


# _____________________ HANDLERS _____________________

def parse_input(user_input: str) -> tuple:
    parts = user_input.strip().split()
    command = parts[0].lower() if parts else ""
    args = parts[1:]
    return command, *args


@input_error
def add_contact(args: list[str], book: AddressBook) -> str:
    if len(args) < 2:
        raise ValueError("Please provide both a name and a phone number: add [name] [phone]")
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args: list[str], book: AddressBook) -> str:
    if len(args) < 3:
        raise ValueError("Please provide name, old phone, and new phone: change [name] [old phone] [new phone]")
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        return f"Contact '{name}' not found."
    record.edit_phone(old_phone, new_phone)
    return "Phone number updated."


@input_error
def show_phone(args: list[str], book: AddressBook) -> str:
    if len(args) < 1:
        raise ValueError("Please provide a name: phone [name]")
    name, *_ = args
    record = book.find(name)
    if record is None:
        return f"Contact '{name}' not found."
    phones = ", ".join(p.value for p in record.phones) or "No phones on record."
    return f"{name}: {phones}"


@input_error
def show_all(_: list[str], book: AddressBook) -> str:  # args renamed to _ — intentionally unused
    if not book.data:
        return "Address book is empty."
    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args: list[str], book: AddressBook) -> str:
    if len(args) < 2:
        raise ValueError("Please provide a name and a date: add-birthday [name] [DD.MM.YYYY]")
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        return f"Contact '{name}' not found."
    record.add_birthday(birthday)
    return f"Birthday added for {name}."


@input_error
def show_birthday(args: list[str], book: AddressBook) -> str:
    if len(args) < 1:
        raise ValueError("Please provide a name: show-birthday [name]")
    name, *_ = args
    record = book.find(name)
    if record is None:
        return f"Contact '{name}' not found."
    if record.birthday is None:
        return f"{name} has no birthday set."
    return f"{name}'s birthday: {record.birthday}"


@input_error
def birthdays(_: list[str], book: AddressBook) -> str:  # args renamed to _ — intentionally unused
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days."
    return "\n".join(
        f"{entry['name']}: congratulate on {entry['birthday']}"
        for entry in upcoming
    )


# _____________________ MAIN _____________________

def main() -> None:
    book = AddressBook()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(args, book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()