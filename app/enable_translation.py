from main import app
from pathlib import Path
from fastapi_babel import Babel, BabelConfigs, BabelMiddleware
# Путь к корню проекта (один уровень выше текущего файла)
ROOT_DIR = Path(__file__).resolve().parent.parent
LOCALES_DIR = ROOT_DIR / "locales"

# Создаем объект конфигурации для Babel:
babel_configs = BabelConfigs(
    ROOT_DIR=ROOT_DIR,
    BABEL_DEFAULT_LOCALE="en",  # Язык по умолчанию
    BABEL_TRANSLATION_DIRECTORY=str(LOCALES_DIR)  # Папка с переводами
)

# Инициализируем объект Babel с использованием конфигурации
babel = Babel(configs=babel_configs)

# Добавляем мидлварь, который будет устанавливать локаль для каждого запроса
app.add_middleware(BabelMiddleware, babel_configs=babel_configs)