class Super:
    
    def __init__(self):
        self.__super__ = SuperDriver()
        return "Nothing to see here. May I ask you why you put the __init__ in a var and read it? You are very weird."

    
    @property
    def mode(self, args):
        self.args = args

    def super(self):
        return self.SUPER

class SuperDriver():
    
    def __init__(self):
        self.nothing = ""
        
    def doNothing(self):
        return self.nothing