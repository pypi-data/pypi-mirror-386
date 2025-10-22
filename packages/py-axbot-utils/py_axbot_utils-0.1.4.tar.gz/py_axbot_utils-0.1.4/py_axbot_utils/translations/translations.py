import gettext

# Path to your compiled translation files (.mo)
LOCALE_PATH = "./locales"

# Bind the text domain
gettext.bindtextdomain("messages", LOCALE_PATH)
gettext.textdomain("messages")


def _(text):
    return gettext.gettext(text)
