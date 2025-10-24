try:
    from sqlsave import SqlSave
    from cons import ConsoleEditor
    from statemachine import StateMachine, StateEditor
    saves = SqlSave()
    state = StateMachine()
    cons = ConsoleEditor()
    state_editor = StateEditor()
    state.add_state(variable="available", state="True")

    class AILogic():

        def __init__(self, **kwargs):
            self.api_key = kwargs.get("api_key", "")
            self.aimodel = kwargs.get("aimodel", "gpt-3.5-turbo")
            self.argument = kwargs.get("argument", "")
            self.rule = kwargs.get("rule", "Kurz, Präzise, Nur Lösungen, Kein Text o. a.")
            self.data = kwargs.get("data", [None])
            self.action_list = kwargs.get("actions", {None})
            # self.trigger = kwargs.get("trigger", {None}) // Später
            self.response = ""
            self.process()

        def process(self):
            self.init_ai()
            self.result()

        def init_ai(self):
            try:
                from openai import OpenAI

                client = OpenAI(api_key=self.api_key)

            
                messages = [
                    {"role": "system", "content": f"{self.argument}. {self.rule}"},
                    {"role": "user", "content": ", ".join(self.data)}
                ]

                
                if self.action_list and self.action_list != [None] and any(action for action in self.action_list):
                    messages.append({"role": "user", "content": f"Verfügbare Aktionen: {', '.join(self.action_list)}"})
                else:
                    messages.append({"role": "user", "content": "Keine spezifischen Aktionen verfügbar. Verwende Standard-Logik."})
                
                chat = client.chat.completions.create(
                    model=self.aimodel,
                    messages=messages
                )
                self.response = chat.choices[0].message.content
                adm = self.response
                return adm
            
            except Exception as e:
                cons.error("Critical error occurred, please check your installation and dependencies.", hook="")
                

        def result(self):
            return self.response
        
except Exception:
    if state.check(variable="available", state="True"):
        cons.error(message="A Critical error occurred, Please check your installation and dependencies.", hook="")
    else:
        print("Critical error occurred, please check your installation and dependencies.")