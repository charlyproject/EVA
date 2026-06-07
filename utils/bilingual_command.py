class BilingualCommand:
    def __init__(self, spanish, english):
        self.spanish = spanish.lower()
        self.english = english.lower()

    def matches(self, text_lower):
        return self.spanish in text_lower or self.english in text_lower

    def __str__(self):
        return f"{self.spanish}/{self.english}"
