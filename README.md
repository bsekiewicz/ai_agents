# Agenci AI

Zbiór skryptów wykorzystujących LLM do różnych zadań.

## Lista agentów

### Paragon

Aplikacja do skanowania paragonów (np. poprzez robienie zdjęcia na telefonie), która przetwarza obraz do tekstu, a następnie analizuje treść i zapisuje w bazie.  
Aktualnie dostępne jest API (FastAPI), które konwertuje zdjęcie do uporządkowanego tekstu (LLM OCR).

Do działania potrzebny jest klucz OpenAI, ponieważ wykorzystywany jest model `gpt-4o`.
