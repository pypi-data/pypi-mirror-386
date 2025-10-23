from datetime import timedelta
from dm_client.transaction.constants import MAX_TRANSACT_PERIOD, MAX_TRANSACT_PERIOD_INC_BAN
from dm_client.transaction import constants

def determine_expiry(transaction):
    types = [transaction.source[:3]]
    types.extend([dest[:3] for dest in transaction.destinations])
    if constants.TRANSACTING_ENTITY_TYPE.BAN.value in types:
        expires = transaction.created_at + timedelta(seconds=constants.MAX_TRANSACT_PERIOD_INC_BAN)
    else:
        expires = transaction.created_at + timedelta(seconds=constants.MAX_TRANSACT_PERIOD)
    return expires.isoformat()
