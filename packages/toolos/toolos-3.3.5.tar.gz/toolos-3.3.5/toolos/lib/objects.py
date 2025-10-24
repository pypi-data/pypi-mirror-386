import random
import secrets
class DecodeObjectConstructor:
    """Merges a object[decodingkey] to a decodeobject
    > This allows more Specific Key Operations
    
    """
     
    def __init__(self, key):
        self.__key__ = key
        self.Name = "decodeobject"
        self.FLAGS = []
        self.PAIR = {'data': []}
        self.FREEZE = False
        self._locks = False
        self.Constructor = {}
        self.Global = False
        
    def type_object(self):
        """Return TypeObject from The DecodeObjectConstructor"""
        return f"{secrets.token_bytes(16)}-decodekeyobject@main<{__class__}>"
        
    def Reload(self):
        """Realoding Constructor data"""
        self.Constructor = self.GetConstructdata()
        
    def blockKey(self):
        """lock the Key
        > This cause that key.Key() -> returns None
        """
        self._locks = True
        
    def unblockKey(self):
        """unlock the Key"""
        self._locks = False
        
    def Key(self):
        """Returns decodeobject.__key__"""
        if self.Global:
            return self.__key__
        if not self._locks:
            return self.__key__
        if self._locks:
            return None
    
    def FreezeLock(self, toggle: bool=None):
        if not toggle:
            if self.FREEZE == False:
                self.FREEZE = True
            else:
                self.FREEZE = False
        if toggle:
            self.FREEZE = toggle
            
    def setName(self, name):
        """Set The Name of Key"""
        self.Name = name
    
    def forceGlobalKey(self):
        """if you enabale forceGlobal, your key can be used from anyone"""
        self.Global = True
    
    def addFlag(self, *flags):
        """
        ## DecodeObject Flags
        with Flags you can Customize your Key Behaviour!
        
        ---------------------------
        ```
        -   'newKey(<newkey_param>)'
        -   'addKeyPair(<key_param>|<name_param>)'
        -   'behave$Key(<behave_param>)
        -   'newParam(<param>, <paramobject>, <param_id>)'
        -   'newFlag(<paramobject>, <register_param>)'
        ```
        ### Tipps:\n
        ```python
        <keyoption>$<func>(%)\n
        ```
        The '$' Type Refers to a Option + Function of The Original Object. \n
        You can see avaible keyoptions in the list below. \n
        funcs are The Functions from This Class used to Refer. \n
        The '%' also named parameter is the Construction you give along:
        ```
        keyoptions = ['behave', 'acsess', 'onuse', 'lock']
        funcoptions = [FreezeLock, blockKey ...]
        example$params = [
                'behave$<func>(--stop--freeze, --event(self.Event.TriggerOn(eventname))),
                'onuse$Key(--return, --event(self.Event.Connect()))'
        ]
        ```
        """
        self.FLAGS.append({
            'flag': flags
        })
        self.Reload()
        
    def connectMemoryApi(self, memoryapi, Api):
        """Use This method to connect with MemoryApi. \n
        This Allow the decodeobject to get globally interactive.\n
        The function returns [Bool: True] ; [str: Name] \n
        > Api -----------> toolos.Api class\n
        > memoryapi -----> Api.Memory class\n
        
        Simply Get This Data by:\n
        ```python
        self.Memory.Remember(name)\n
        ```
        """
        name = f'{self.Name}${random.randint(1, 9)}'
        data = Api.Collect(self.Key())
        print(data, name)
        memoryapi.KnowThis(name, data)
        return True, name
    
    def Pair(self, restrictions: bool=True):
        """Allows sharing data to other objects \n
        use Pair() as parameter for instance.key\n
        The Pair() Method is just a 'Tell them what you know with restrictions' \n
        unless you didnt block the key like 'Never Tell Anybody anything'
        you also cann ignore all restrictions with param: restrictions=False
        ```python
        self.StateMachine.Connect(decodeobject.Pair())
        self.Sequence.Connect(decodeobject.Pair())
        ...
        ```
        """
        if restrictions:
            return self.Constructor
        elif not restrictions:
            return self, self.Constructor
    
    def GetConstructdata(self):
        if self.Global:
            self.Constructor = {
                'flags': self.FLAGS,
                'pair': self.PAIR,
                'freeze': self.FREEZE,
                'key': self.__key__,
                'self': self
        }
            self.Constructor = {
                'flags': self.FLAGS,
                'pair': self.PAIR,
                'freeze': self.FREEZE 
            }
        return self.Constructor
    
    def _destroyObject(self):
        self.__key__ = None
        
               
        
        