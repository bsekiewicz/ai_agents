# AI Agents - Paragon

## Backend API

Do poprawnego działania wymagane jest utworzenie pliku `.env` w lokalizacji `backend/` (patrz przykład `.env.empty`)

### Opis
Backend API aktualnie obsługuje przetwarzanie obrazów paragonów za pomocą LLM OCR. Umożliwia przesyłanie obrazów oraz ekstrakcję danych z paragonów w sposób automatyczny.

### Uruchomienie API
1. Przejdź do katalogu `paragon/backend`:
   ```bash
   cd paragon/backend
   ```
2. Zainstaluj wymagane zależności:
   ```bash
   pip install -r requirements.txt
   ```
3. Uruchom serwer API:
   ```bash
   uvicorn app.main:app --reload
   ```

### Korzystanie z API
Po uruchomieniu API dostępne jest pod adresem `http://127.0.0.1:8000`

### Przesyłanie obrazu paragonu
Aby wykonać OCR na obrazie, należy wysłać żądanie `POST` na endpoint:
```
POST /ocr-image
```
Przykładowe wywołanie w `cURL`:
```bash
curl -X POST "http://127.0.0.1:8000/ocr-image" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@sciezka/do/pliku.jpg"
```

### Co się dzieje po wywołaniu?
1. API przetwarza obraz i wykonuje OCR.
2. Wygenerowane dane zapisywane są w katalogu `data/{data}/{hash_pliku}`.
3. Pliki testowe można znaleźć w katalogu `data-test/`.
4. Dane walidacyjne są zwracane jako odpowiedź w formacie JSON.

### Frontend

In progress...

```
npx expo start --tunnel
```