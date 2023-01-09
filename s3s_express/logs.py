# Not currently implemented, placeholder to reduce refactoring later on


class Logger:
    def __init__(self, log_file_name: str) -> None:
        self.log_file_name = log_file_name

    def log(self, message: str, *args) -> None:
        print(message)
