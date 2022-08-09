from enum import Enum, auto


class Communicates(Enum):

    ACCOUNT_BLOCKED = auto()
    GIVE_ACCOUNT_DATA = auto()
    ERROR = auto()
    WRONG_LOGIN = auto()
    ACCOUNT_IN_USE = auto()
    ACCOUNT_HAS_BEEN_BLOCKED = auto()
    WRONG_PASSWORD = auto()
    LOGGED_IN = auto()
    LOGOUT = auto()
    BLOCK_ACCOUNT = auto()
    PAYMENT = auto()
    SEND_DICT = auto()
    CHANGE_PASSWORD = auto()
    OLD_AND_NEW_PASSWORD_ARE_THE_SAME = auto()
    PASSWORDS_ARE_DIFFERENT = auto()
    PASSWORD_CHANGED = auto()
    GIVE_HISTORY = auto()
