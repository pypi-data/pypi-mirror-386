from pydantic_settings import BaseSettings


class ConfigurationComponent:
    """Конфигурационные объекты, составляющие настройки всего приложения"""

    def __init__(self, item: BaseSettings) -> None:
        self.item = item

        self.env_prefix = item.model_config.get("env_prefix", "")
        self.title = self.item.__class__.__name__
        self.attrs = list(item.model_dump().keys())

    def parsed(self) -> str:
        """
        Парсит объект в строку для записи в docker-compose.yml

        Пример:
          # RabbitMQ
          RABBITMQ_HOST: ${RABBITMQ_HOST}
          RABBITMQ_USER: ${RABBITMQ_USER}
          RABBITMQ_PASS: ${RABBITMQ_PASS}
        """
        title = f'# {self.title}' if self.title else " "
        result = [title]

        for attr in self.attrs:
            full_attr = self.env_prefix + attr
            line = f"{full_attr}: " + f"${{{full_attr}}}"
            result.append(line)

        return "\n".join(result)


class Generator:
    """Генератор docker-compose.yml"""

    ENV_KEY = '[ENV]'
    VERSION_KEY = '[VERSION]'
    FILE_NAME = 'docker-compose.yml'

    def __init__(self, settings: BaseSettings, template: str, version: str) -> None:
        self.settings = settings
        self.template = template
        self.version = version

    def insert_to_template(self, content: str, key: str) -> None:
        # Разбиваем вставляемую строку на отдельные строки

        def define_indentation() -> str:
            lines = self.template.split('\n')
            for line in lines:
                if key in line:
                    return line.split(key)[0]
            return ''

        # Форматируем каждую строку с правильным отступом
        formatted = '\n'.join(
            [define_indentation() + line for line in content.split('\n')]
        )

        # Заменяем {ENV} в шаблоне
        self.template = self.template.replace(key, formatted.strip())

    def replace_version(self, version: str) -> None:
        self.template = self.template.replace(self.VERSION_KEY, version)

    def generate(self) -> None:
        components = list(self.settings.__dict__.values())
        parsed_components: list[str] = [
            ConfigurationComponent(c).parsed() for c in components
        ]

        self.insert_to_template(
            content='\n\n'.join(parsed_components), key=self.ENV_KEY
        )
        self.replace_version(self.version)

        with open(self.FILE_NAME, 'w') as f:
            f.write(self.template)

