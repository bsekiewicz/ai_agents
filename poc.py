import datetime


# Model Interface
class ModelInterface:
    def __init__(self, model_name):
        self.model_name = model_name

    def generate_response(self, messages, max_tokens, **kwargs):
        raise NotImplementedError("This method should be implemented by subclasses.")


# OpenAI Model Implementation
class OpenAIModel(ModelInterface):
    def __init__(self, model_name, api_key=None):
        super().__init__(model_name)
        # self.api_key = api_key

    def generate_response(self, messages, max_tokens):
        # openai.api_key = self.api_key
        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                n=1
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error communicating with OpenAI: {e}")
            return "An error occurred while generating a response."


# Custom Agent Class
class CustomAgent:
    SUPPORTED_LANGUAGES = ["English", "Polish", "French", "Spanish"]

    def __init__(self, model_interface, max_tokens=350, personality=None, role=None, language=None, collect_history=True, delegate_task=False):
        self.model_interface = model_interface
        self.max_tokens = max_tokens
        self.personality = personality or "You respond in a neutral and polite manner."
        self.role = role or "You are a helpful assistant guiding the user with their queries."
        self.language = self._validate_language(language)
        self.history = [] 
        self.collect_history = collect_history
        self.agents = {}
        self.delegate_task = delegate_task

    def _validate_language(self, language):
        if language:
            language = language.capitalize()
            if language not in self.SUPPORTED_LANGUAGES:
                raise ValueError(f"Language '{language}' is not supported.")
        return language

    def add_agent(self, name, agent):
        if name in self.agents:
            raise ValueError(f"Agent with name '{name}' already exists.")
        self.agents[name] = agent

    def select_agent(self, prompt):
        return self.agents.get(prompt.upper())

    def interact(self, prompt, max_tokens=None, use_history=False, delegate_task=False):
        max_tokens = max_tokens or self.max_tokens
        delegate_task = delegate_task or self.delegate_task

        system_message = "\n".join([
            f"Set role: {self.role}",
            f"Set personality: {self.personality}",
            f"Response only in language: {self.language}" if self.language else ""
        ])

        messages = [{"role": "system", "content": system_message}]
        if use_history:
            messages += [{"role": entry["role"], "content": entry["content"]} for entry in self.history]
        messages.append({"role": "user", "content": prompt})

        response = self.model_interface.generate_response(messages, max_tokens)

        if self.collect_history:
            timestamp = datetime.datetime.now().isoformat()
            self.history.append({"role": "user", "content": prompt, "timestamp": timestamp})
            self.history.append({"role": "assistant", "content": response, "timestamp": timestamp})

        if delegate_task:
            agent = self.select_agent(response.strip())
            if agent:
                return agent.interact(prompt, max_tokens, use_history=True, delegate_task=False)

        print(response)

    def clear_history(self):
        self.history = []