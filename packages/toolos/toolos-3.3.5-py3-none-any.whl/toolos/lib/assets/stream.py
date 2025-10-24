class Stream:
    
    def __init__(self, name):
        self.name = name
        self.metastream = {}
        
class StreamBot(Stream):
    def __init__(self, name, token):
        super().__init__(name)
        self.token = token
        self.ai = []
        
    def discord_create_bot(self, name, token, prefix, ID=None, ICD=None):
        ID = self.ID if hasattr(self, 'ID') else None
        ICD = self.ICD if hasattr(self, 'ICD') else None
        if ID is None or ICD is None:
            raise ConnectionResetError("Failed to create Discord bot: Missing ID or ICD.")
        meta = {
            "name": name,
            "prefix": prefix
        }
        self.tokenize.ADDSTREAM.DEFAULT(token, ID)
        params = self.tokenize.stream.get_meta(ID)
        self.ai.create_bot(params, meta)
        name = "LeoAI"
        id = 202981
        self.ai.initialize_bot(name=name, id=id)
        self.ai.awaitinit(id=id)
        bot = self.ai.get_botAI(id=id)
        self.ai.append({
            "bot": bot,
            "name": name,
            "id": id
        })
        return True, bot
    
    def discord_INITIALIZE(self, ID, PED, ICD):
        self.ID = ID
        self.PED = PED
        self.ICD = ICD
        if self.check_connection_subline(ID):
            pass
        else:
            raise ConnectionRefusedError("identification-subline-stream return error 'N2-001'. For Some reason its not my fault.")
        return True
        
        
    def check_connection_subline(self, ID):
        metadata = self.metastream
        main = metadata.get("identification-subline-stream", None)
        if main:
            if ID in main:
                return True
            else:
                return False