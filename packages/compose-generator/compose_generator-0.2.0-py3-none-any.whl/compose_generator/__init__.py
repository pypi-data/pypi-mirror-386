from typing import Optional

from pydantic_settings import BaseSettings

ENV_KEY = '[ENV]'
VERSION_KEY = '[VERSION]'

class ConfigurationComponent:
    """Конфигурационные объекты, составляющие настройки всего приложения"""
    
    def __init__(self, item: BaseSettings, ignore: Optional[list[str]] = None) -> None:
        self.item = item
        self.ignore = ignore if ignore else []
        
        self.env_prefix = item.model_config.get("env_prefix", "")
        self.attrs = list(item.model_dump().keys())
    
    @property
    def title(self) -> str:
        class_name = self.item.__class__.__name__
        return f'# {class_name}'
    
    def compose_parsed(self) -> str:
        """
        Парсит объект в строку для записи в docker-compose.yml

        Пример:
          # RabbitMQ
          RABBITMQ_HOST: ${RABBITMQ_HOST}
          RABBITMQ_USER: ${RABBITMQ_USER}
          RABBITMQ_PASS: ${RABBITMQ_PASS}
        """

        result = [self.title]
        
        for attr in self.attrs:
            full_attr = self.env_prefix + attr
            if full_attr not in self.ignore:
                line = f"{full_attr}: " + f"${{{full_attr}}}"
                result.append(line)
        
        return "\n".join(result)
    
    def env_parsed(self) -> str:
        """
        Парсит объект в строку для записи в .env
        
        Пример:
          # RabbitMQ
          RABBITMQ_HOST=value
          RABBITMQ_USER=value
          RABBITMQ_PASS=value
        """
        result = [self.title]
        
        for attr in self.attrs:
            full_attr = self.env_prefix + attr
            if full_attr not in self.ignore:
                line = f"{full_attr}=value"
                result.append(line)
            
        return "\n".join(result)


class DockerCompose:
    def __init__(
        self,
        settings: list[BaseSettings],
        template: str,
        version: str,
        ignore: Optional[list[str]] = None,
    ) -> None:
        self.settings = settings
        self.template = template
        self.version = version
        self.ignore = ignore
    
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
        self.template = self.template.replace(VERSION_KEY, version)
    
    def __call__(self, filename: str) -> None:
        parsed_components: list[str] = [
            ConfigurationComponent(c, self.ignore).compose_parsed() for c in self.settings
        ]
        
        self.insert_to_template(
            content='\n\n'.join(parsed_components), key=ENV_KEY
        )
        self.replace_version(self.version)
        
        with open(filename, 'w') as f:
            f.write(self.template)


class ExampleEnv:
    def __init__(
        self,
        settings: list[BaseSettings],
        ignore: Optional[list[str]] = None,
    ) -> None:
        self.settings = settings
        self.ignore = ignore
    
    def __call__(self, filename: str) -> None:
        parsed_components: list[str] = [
            ConfigurationComponent(c, self.ignore).env_parsed() for c in self.settings
        ]
        text = '\n\n'.join(parsed_components)
        with open(filename, 'w') as f:
            f.write(text)

class Generate:
    def __init__(
        self,
        settings: list[BaseSettings],
    ) -> None:
        self.settings = settings
    
    def docker_compose(
        self,
        template: str,
        version: str,
        ignore: Optional[list[str]] = None,
        filename: str = 'docker-compose.yml'
    ) -> None:
        DockerCompose(
            settings=self.settings,
            template=template,
            version=version,
            ignore=ignore,
        )(filename)
    
    def example_env(self,
        ignore: Optional[list[str]] = None,
        filename: str = '.env.example'
        ) -> None:
        ExampleEnv(
            settings=self.settings,
            ignore=ignore,
        )(filename)


class Generator:
    """Генератор docker-compose.yml"""
    
    def __init__(
        self,
        settings: list[BaseSettings],
    ) -> None:
        self.settings = settings
    
    @property
    def generate(self) -> Generate:
        return Generate(settings=self.settings)