import logging

# Настройка логгера
logger = logging.getLogger("db_service")   # Название логгера
logger.setLevel(logging.DEBUG)         # Уровень логирования

# Формат логов
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')

# Обработчик — в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Обработчик — в файл
file_handler = logging.FileHandler("app.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
