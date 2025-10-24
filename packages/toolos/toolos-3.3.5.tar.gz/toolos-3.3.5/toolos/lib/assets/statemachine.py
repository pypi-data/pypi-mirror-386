try:
    import asyncio
    class StateMachine:
        
      # StateMachine von ClayTechnologies (C) Powerd by SQLSave Module

        def __init__(self, name="StateMachine"):
            self.name = name
            from sqlsave import SqlSave
            from cons import ConsoleEditor
            self.saves = SqlSave(db=name)
            self.cons = ConsoleEditor()
            self.variables = []
            self.states = []
            self.index = {}
            
        def add_state(self, variable, state):
            self.saves.save(data=state, id=variable)
            self.index[variable] = state

        def get_state(self, variable):
            return self.saves.load(id=variable)
        
        def isFalse(self, variable):
            data = self.get_state(variable)
            if data == "False":
                return True
            return False

        def isTrue(self, variable):
            data = self.get_state(variable)
            if data == "True":
                return True
            return False

        def isNone(self, variable):
            data = self.get_state(variable)
            if data == "None":
                return True
            return False


        def listen(self, variable, state, callback):
            """Synchrone Listen-Methode ohne asyncio"""
            import threading
            import time
            
            def listener_thread():
                while True:
                    if self.check(variable, state):
                        callback()
                        break  # Exit after callback is executed
                    time.sleep(0.2)
            
            # Starte Listener in separatem Thread
            listener = threading.Thread(target=listener_thread, daemon=True)
            listener.start()
            return listener

        def check(self, variable, state):
            data = self.get_state(variable)
            if data == state:
                return True
            return False
        
        def update(self, variable, new_state):
            self.saves.update(id=variable, data=new_state)
            return True
        
        def clear(self, action=False):
            self.saves.clear(self.name)
            if action == "q":
                import sqlsave
                sqlsave.SqlSave(self.name)
            

   # ---------------------------------------------------------

    class StateEditor(StateMachine):
        
      # StateEditor - version 1.0.0
        
        def __init__(self, statemachine_instance=None, variable=None, state=None):
            if statemachine_instance:
                self.name = statemachine_instance.name
                self.saves = statemachine_instance.saves
                self.cons = statemachine_instance.cons
                self.variables = statemachine_instance.variables
                self.states = statemachine_instance.states
                self.index = statemachine_instance.index
            else:
                # Fallback: Erstelle eigene Instanz (für Kompatibilität)
                super().__init__()
            
            self.variable = variable
            self.state = state
            self.timer = False
            

        def add_trigger(self, variable, trigger, after=None):
                data = self.saves.load(id=variable)
                if data:
                    t = str(trigger)
                    
                    
                    if t.startswith("timer"):
                        if after is None:
                            after = False
                        timer_value = float(t[5:])  # Extract number after "timer"
                        import threading
                        import time
                        
                        def timer_thread():
                            time.sleep(timer_value)
                            self.update(variable, after)
                        
                        threading.Thread(target=timer_thread, daemon=True).start()
                        
                    elif t.startswith("event"):
                        event = t[5:]
                       
                        import threading
                        
                        def event_thread():
                            self.handle_event_sync(event, variable)
                        
                        threading.Thread(target=event_thread, daemon=True).start()
                    else:
                    
                        self.custom_action(t)

        def handle_event_sync(self, event, variable):
            import time
            ev = str(event)
            if ev.startswith("change"):
                parts = ev.split("-")
                if len(parts) >= 3:
                    what = parts[1]
                    when = parts[2]
                    to = parts[3] if len(parts) > 3 else "True"
                    
                    while True:
                        current_state = self.get_state(what)
                        if current_state == when:
                            self.update(what, to)
                            break
                        time.sleep(0.1)

        async def start_timer(self, timer, variable, after=None):
            await asyncio.sleep(float(timer))
            self.update(variable, after)
            return True

        async def wait_for_event(self, event, variable):
            ev = str(event)
            if ev.startswith("change"):
                parts = ev.split("-")
                if len(parts) >= 3:
                    what = parts[1]
                    when = parts[2]
                    to = parts[3] if len(parts) > 3 else "True"
                    
                    while True:
                        if self.timer == True:
                            if len(parts) > 3 and parts[2].startswith("timer"):
                                time_val = parts[2][5:]
                                await self.start_timer(time_val, variable, to)
                                break
                        data = self.get_state(what)
                        if data == when:
                            self.update(what, to)
                            break

        def custom_action(self, action):
            pass
        
    class Debugger(StateMachine):
        
        def __init__(self):
            super().__init__()
            self.add_state("debugging", state="off")
            

        def check(self):
            if self.get_state("debugging") == "on":
                return True
            else:
                return False
        
        def activate(self):
            self.update("debugging", "on")
except Exception:
    print("Critical error occurred, please check your installation and dependencies.")