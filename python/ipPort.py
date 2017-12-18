# Class for holding an IP only port such as
# IRLP
# echo link
# VOIP auto patch
# fusion bridge
# any other internet protocoll bridge
class ipPort:
    def __init__(self,top):
        self.top=top
        self.card=None
