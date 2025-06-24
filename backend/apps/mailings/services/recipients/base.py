from apps.mailings.models import Mailing


class RecipientStrategy:
    def __init__(self, mailing: Mailing):
        self.mailing = mailing

    def execute(self) -> int:
        """
        Метод должен быть переопределён в дочерней стратегии.
        Возвращает количество сгенерированных получателей или выполненных действий.

        Raises:
            NotImplementedError: если метод не реализован в дочернем классе.
        """
        raise NotImplementedError("Стратегия должна реализовывать execute()")
