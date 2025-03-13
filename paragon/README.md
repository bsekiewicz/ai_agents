## BACKEND

Run  
```
uvicorn app.main:app --reload --host 0.0.0.0 --port 5001
```

### API

```
curl -X 'POST' 'http://localhost:5001/ocr-image' \
-H 'accept: application/json' \
-H 'Content-Type: multipart/form-data' \
-F 'file=@image.jpg'
```


## FRONTEND

Run
```
npx expo start --tunnel
```