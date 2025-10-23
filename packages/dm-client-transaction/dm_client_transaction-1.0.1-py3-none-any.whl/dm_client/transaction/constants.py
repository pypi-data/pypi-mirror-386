from django.db import models


class TRANSACTION_RECORD_TYPE(models.TextChoices):
    CREDIT = 'CREDIT'
    DEBIT = 'DEBIT'


class TRANSACTION_PROGRESS_STATUS(models.TextChoices):
    INITIAL = 'INITIAL'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'


class TRANSACTION_STATUS(models.IntegerChoices):
    UNDEFINED = 0
    FAILURE = -1
    SUCCESS = 1

class TRANSACTION_PRIORITY(models.IntegerChoices):
    REALTIME = 1
    ASYNC = 2


class TRANSACTING_ENTITY_TYPE(models.TextChoices):
    FIN = 'FIN'
    BAN = 'BAN'
    BIL = 'BIL'

    @classmethod
    def get_type(cls, entity: str):
        return entity[:3]

    @classmethod
    def get_id(cls, entity: str):
        return entity[4:]


MAX_TRANSACT_PERIOD = 30
MAX_TRANSACT_PERIOD_INC_BAN = 60