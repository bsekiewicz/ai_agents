# Multi-Agent Framework with Pizza Assistant Use Case

This project provides a multi-agent framework that allows creating and managing AI agents capable of handling specific tasks. It includes support for delegating queries to subagents based on predefined roles. 

The example use case, **Pizza Assistant**, demonstrates how this framework can be applied in a real-world scenario, such as managing a pizzeria's customer support.

---

## Project Structure

### Core Components

1. **`ModelInterface`**  
   An abstract base class defining the interface for AI models. Subclasses implement the `generate_response` method.

2. **`OpenAIModel`**  
   An implementation of `ModelInterface` that uses OpenAI's API to generate responses.

3. **`CustomAgent`**  
   A class representing an intelligent agent. Each agent can:
   - Handle queries based on its `role` and `personality`.
   - Delegate tasks to subagents.
   - Maintain interaction history.

---

## Pizza Assistant: A Use Case Example

### Overview

The Pizza Assistant simulates a customer service system for a pizzeria. It comprises a main agent that delegates customer queries to specialized subagents for handling:
- **Menu inquiries** (`MENU` agent)
- **Order processing** (`ORDER` agent)
- **Contact information** (`CONTACT` agent)

---

### Creating the Pizza Assistant

Below is an example of how to create a `pizza_assistant` using the framework:

```python
def create_pizza_assistant():
    # Information about the menu
    menu_info = \"""
    Lista pizzy:
        Margherita: Sos pomidorowy, mozzarella, świeża bazylia
        Ceny: Mała (33 PLN), Średnia (43 PLN), Duża (69 PLN)
        Pepperoni: Sos pomidorowy, mozzarella, salami pepperoni
        Ceny: Mała (38 PLN), Średnia (48 PLN), Duża (80 PLN)
        Hawaiian: Sos pomidorowy, mozzarella, szynka, ananas
        Ceny: Mała (39 PLN), Średnia (51 PLN), Duża (86 PLN)
        Vegetarian: Sos pomidorowy, mozzarella, papryka, oliwki, świeży pomidor, kukurydza
        Ceny: Mała (42 PLN), Średnia (52 PLN), Duża (88 PLN)
        BBQ Chicken: Sos BBQ, mozzarella, kurczak, papryka, cebula
        Ceny: Mała (41 PLN), Średnia (51 PLN), Duża (86 PLN)

    Rozmiary:
        Mała (31 cm)
        Średnia (42 cm)
        Duża (60 cm)

    Dodatki:
        Ser extra (2 PLN), Oliwki (2 PLN), Pieczarki (2 PLN), Jalapeño (2 PLN), Cebula (2 PLN), Szynka (12 PLN)
    \"""

    # Information about orders
    order_info = \"""
    Przy składaniu zamówienia klient musi podać następujące dane:
        - Rodzaj pizzy
        - Rozmiar pizzy
        - Lista dodatków
        - Dane kontaktowe:
            - Imię i nazwisko
            - Numer telefonu
            - Adres dostawy
        - Metoda płatności
    
    Po zebraniu wszystkich informacji asystent powinien:
        - Potwierdzić zamówienie
        - Podać całkowity koszt
        - Przekazać przewidywany czas dostawy
    Jeśli brakuje danych, poprosić o ich uzupełnienie.
    \"""

    # Contact information
    contact_info = \"""
    Dane kontaktowe pizzerii:
        - Adres: ul. Pyszna 24, 00-001 Warszawa
        - Telefon: +48 123 456 789
        - E-mail: kontakt@pizzeria.pl
        - Godziny otwarcia:
            - Poniedziałek - Piątek: 10:00 - 22:00
            - Sobota - Niedziela: 12:00 - 24:00
        - Media społecznościowe:
            - Facebook: facebook.com/pizzeria
            - Instagram: instagram.com/pizzeria
    \"""

    # Subagents
    pizza_assistant_menu = CustomAgent(
        model_interface=OpenAIModel("gpt-4o-mini-2024-07-18"),
        personality="Udzielaj odpowiedzi na pytania klientów w sposób zwięzły i profesjonalny.",
        role=f"Pracujesz w pizzerii i jesteś ekspertem od menu. Oto szczegóły:\\n{menu_info}",
        language="Polish"
    )

    pizza_assistant_order = CustomAgent(
        model_interface=OpenAIModel("gpt-4o-mini-2024-07-18"),
        personality="Pomagasz klientom składać zamówienia.",
        role=f"Twoim zadaniem jest zbieranie informacji o zamówieniach. Oto szczegóły:\\n{order_info}\\n{menu_info}",
        language="Polish"
    )

    pizza_assistant_contact = CustomAgent(
        model_interface=OpenAIModel("gpt-4o-mini-2024-07-18"),
        personality="Udzielasz informacji kontaktowych w sposób przyjazny i profesjonalny.",
        role=f"Twoim zadaniem jest udzielanie informacji kontaktowych. Oto szczegóły:\\n{contact_info}",
        language="Polish"
    )

    # Main assistant
    pizza_assistant = CustomAgent(
        model_interface=OpenAIModel("gpt-4o-mini-2024-07-18"),
        personality="Jesteś osobą pracującą na infolinii pizzerii. Przekierowujesz zapytania do MENU, ORDER lub CONTACT.",
        role="""
        MENU – jeśli pytanie dotyczy dostępnych pizz, składników, cen, rozmiarów lub dodatków.
        ORDER – jeśli klient chce złożyć zamówienie na pizzę.
        CONTACT – jeśli zapytanie dotyczy informacji o firmie, takich jak dane kontaktowe, adres, godziny otwarcia.
        Jeśli nie możesz jednoznacznie przypisać pytania do żadnej z kategorii, poproś klienta o doprecyzowanie zapytania.
        """,
        language="Polish",
        delegate_task=True
    )

    # Add subagents
    pizza_assistant.add_agent('MENU', pizza_assistant_menu)
    pizza_assistant.add_agent('ORDER', pizza_assistant_order)
    pizza_assistant.add_agent('CONTACT', pizza_assistant_contact)

    return pizza_assistant
```

---

### Example Interaction

```python
# Create the assistant
pizza_assistant = create_pizza_assistant()
```

```python
pizza_assistant.interact("Cześć, jak was znaleźć?")

Cześć! Możesz nas znaleźć pod adresem: ul. Pyszna 24, 00-001 Warszawa. Jeśli potrzebujesz się z nami skontaktować, zadzwoń pod numer +48 123 456 789 lub napisz na e-mail: kontakt@pizzeria.pl. Jesteśmy otwarci od poniedziałku do piątku w godzinach 10:00 - 22:00, a w weekendy od 12:00 do 24:00. Możesz też śledzić nas na mediach społecznościowych: Facebook (facebook.com/pizzeria) i Instagram (instagram.com/pizzeria). Zapraszamy!
```

```python
pizza_assistant.interact("Uwielbiam kukurydzę. Jaką pizze polecacie dla dwóch osób?")

Polecam pizzę Vegetarian, która zawiera kukurydzę oraz inne świeże składniki. Dla dwóch osób idealna będzie średnia pizza (42 cm) za 52 PLN. Możecie także dodać ser extra lub inne dodatki według gustu. Smacznego!
```

```python
pizza_assistant.interact("W takim razie chciałbym złożyć zamówienie.")

Świetnie! Zacznijmy od kilku szczegółów. 

1. Jaki rodzaj pizzy chciałbyś zamówić? (np. Margherita, Pepperoni, Hawaiian, Vegetarian, BBQ Chicken)
2. Jaki rozmiar pizzy wybierasz? (Mała, Średnia, Duża)
3. Jakie dodatki chciałbyś dodać? (możesz podać kilka, jeśli chcesz)
4. Proszę podaj swoje dane kontaktowe:
   - Imię i nazwisko
   - Numer telefonu
   - Adres dostawy
5. Jaką metodę płatności preferujesz? (np. gotówka, karta) 

Czekam na Twoje odpowiedzi!
```

```python
pizza_assistant.interact("Vegetariana, 43 cm, bez dodatków. Jan Okwalski, 888 621 1, ul. Fajna 66/6, Pole Małe. Płace BLIKIEM")

Dziękuję za wszystkie informacje! Oto podsumowanie Twojego zamówienia:

- **Rodzaj pizzy:** Vegetarian
- **Rozmiar pizzy:** Średnia (42 cm)
- **Dodatki:** Brak
- **Dane kontaktowe:**
  - Imię i nazwisko: Jan Okwalski
  - Numer telefonu: 888 621 1
  - Adres dostawy: ul. Fajna 66/6, Pole Małe
- **Metoda płatności:** BLIK

**Całkowity koszt zamówienia: 52 PLN** (cena pizzy Vegetarian w rozmiarze średnim).

Przewidywany czas dostawy to około 30-45 minut.

Czy wszystko się zgadza? Jeśli tak, potwierdź proszę zamówienie!
```

```python
pizza_assistant.interact("Zamawiam pizze. Nie zgadza się, chciałem 43cm")

Przepraszam za pomyłkę! Rozmiar 43 cm to średnia pizza, która ma 42 cm. 

Czy chciałbyś zamówić pizzę w rozmiarze dużym (60 cm)? Jeśli tak, to całkowity koszt zamówienia wyniesie 88 PLN. 

Proszę o potwierdzenie, czy chcesz zamówić dużą pizzę Vegetarian, czy może chcesz zmienić coś w zamówieniu?
```
---

### Key Features Demonstrated

- **Task Delegation**: Queries are routed to appropriate subagents based on the context.
- **Custom Personalities and Roles**: Each subagent has a unique role and personality tailored to its task.
- **Natural Language Interactions**: Responses simulate a professional customer service experience.
- **Extensibility**: The framework supports adding new subagents for additional tasks.

---

### TODO

1. **Enhance Multi-Agent Logic**:
   - Implement more complex delegation rules based on natural language understanding.
   - Support dynamic subagent creation during runtime.

2. **Error Handling**:
   - Add better error messages for undefined subagents or unsupported queries.
   - Implement fallback mechanisms for unhandled cases.

3. **Data Persistence**:
   - Store interaction history in a database or external file for future reference.

4. **Localization**:
   - Expand supported languages beyond the current options.
   - Integrate a language auto-detection feature.

5. **API Integration**:
   - Replace the mocked `generate_response` function with actual API calls.
   - Add authentication and rate-limiting mechanisms for OpenAI API usage.

6. **Testing and Debugging**:
   - Write unit tests for all core components.
   - Simulate real-world customer interactions to test system robustness.

7. **Improved UX**:
   - Develop a web or mobile interface for interacting with the assistant.
   - Provide visual cues for delegated tasks and responses.

Feel free to contribute or suggest new features for the framework!
