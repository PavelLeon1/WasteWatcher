"""
Прогресс-бар для CLI.

Отображение прогресса сканирования в реальном времени без внешних зависимостей.
"""

import sys
from datetime import datetime


class ProgressReporter:
    """
    Репортёр прогресса сканирования.

    Обновляет строку в stdout через \\r (carriage return).
    Работает только в интерактивных терминалах.

    Attributes:
        verbose: Если False — все методы noop.
        count: Текущее количество обработанных файлов.
        last_update: Время последнего обновления.
        update_interval: Интервал между обновлениями (секунды).
    """

    def __init__(self, verbose: bool = False, update_interval: float = 0.5) -> None:
        """
        Инициализирует репортёр прогресса.

        Args:
            verbose: Если False — все методы ничего не делают.
            update_interval: Минимальный интервал между обновлениями (сек).
        """
        self.verbose = verbose
        self.count = 0
        self.last_update: datetime | None = None
        self.update_interval = update_interval
        self._is_tty = sys.stdout.isatty()

    def update(self, count: int, current_path: str = "") -> None:
        """
        Обновляет строку прогресса в stdout.

        Args:
            count: Текущее количество обработанных файлов.
            current_path: Путь текущего обрабатываемого файла/директории.
        """
        if not self.verbose:
            return

        # Проверка на интервал обновлений
        now = datetime.now()
        if self.last_update is not None:
            delta = (now - self.last_update).total_seconds()
            if delta < self.update_interval:
                return

        self.count = count
        self.last_update = now

        # Обрезка пути для отображения
        display_path = current_path
        if len(display_path) > 60:
            display_path = "..." + display_path[-57:]

        # Формирование строки прогресса
        line = f"\r  Сканировано: {count:>8,} файлов | {display_path:<60}"

        # Запись в stdout
        if self._is_tty:
            sys.stdout.write(line)
            sys.stdout.flush()
        else:
            # Для не-TTY вывода (лог-файл, pipe) — просто логируем
            pass

    def done(self, total: int = 0) -> None:
        """
        Завершает отображение прогресса.

        Args:
            total: Общее количество файлов (опционально).
        """
        if not self.verbose:
            return

        if self._is_tty:
            # Переход на новую строку
            sys.stdout.write("\n")
            sys.stdout.flush()

        # Финальное сообщение
        if total > 0:
            sys.stdout.write(f"  Всего файлов: {total:,}\n")
            sys.stdout.flush()

    def reset(self) -> None:
        """
        Сбрасывает счётчик и состояние.
        """
        self.count = 0
        self.last_update = None


def create_progress_reporter(verbose: bool = False) -> ProgressReporter:
    """
    Фабричная функция для создания репортёра.

    Args:
        verbose: Включить подробный вывод.

    Returns:
        Настроенный экземпляр ProgressReporter.

    Example:
        >>> reporter = create_progress_reporter(verbose=True)
        >>> reporter.update(100, "/path/to/file")
        >>> reporter.done(total=1000)
    """
    return ProgressReporter(verbose=verbose)


if __name__ == "__main__":
    # Тесты для самопроверки модуля
    import time

    print("=== Тест 1: ProgressReporter в verbose режиме ===")
    reporter = ProgressReporter(verbose=True, update_interval=0.1)

    # Симуляция сканирования
    for i in range(1, 101):
        reporter.update(i, f"/test/directory/file_{i}.txt")
        time.sleep(0.02)  # Симуляция работы

    reporter.done(total=100)
    print("[OK] Тест 1 пройден")

    print("\n=== Тест 2: ProgressReporter в тихом режиме ===")
    quiet_reporter = ProgressReporter(verbose=False)

    for i in range(1, 101):
        quiet_reporter.update(i, "/test/file.txt")

    quiet_reporter.done()
    print("[OK] Тест 2 пройден (нет вывода)")

    print("\n=== Тест 3: Фабричная функция ===")
    factory_reporter = create_progress_reporter(verbose=True)
    assert isinstance(factory_reporter, ProgressReporter)
    factory_reporter.update(50, "/test")
    factory_reporter.done()
    print("[OK] Тест 3 пройден")

    print("\n=== Тест 4: reset() ===")
    reporter.reset()
    assert reporter.count == 0
    assert reporter.last_update is None
    print("[OK] Тест 4 пройден")

    print("\nprogress: OK")
