from JumpScale import j

def cb1():
    from .TelegramFactory import TelegramFactory
    return TelegramFactory()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('telegrambot', cb1)
