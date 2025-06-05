# rest-api-scanning



---
1. Load + Autofill -> Send to Burp -> Burp Export Items -> Nuclei DAST Scanning

https://github.com/reewardius/Swagger-EZ

![image](https://github.com/user-attachments/assets/4d6a4cd9-09de-4095-a729-21d7200ced5f)


![image](https://github.com/user-attachments/assets/0904122b-b575-4203-8373-eedcc6da3658)

---
2. Nuclei DAST (OpenAPI)

![image](https://github.com/user-attachments/assets/0e4e1a2d-7093-4f86-95c1-0c70e767d629)
![image](https://github.com/user-attachments/assets/435bdac6-971c-4f04-a576-1f594fb27abd)

```
nuclei -l openapi.yaml -im openapi -t nuclei-dast-templates/
```

![image](https://github.com/user-attachments/assets/ddd0bbce-41f9-40fe-b09c-d185bfb71b6b)

---
3. Convert openapi.json to Burp Suite requests

https://github.com/bolbolabadi/swagger2burp
```
python3 swagger2burp.py -f openapi.json -b https://swagger.domain.com -ho swagger.domain.com -t eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJpc3MiOiJ0b3B0YWwuY29tIiwiZXhwIjoxNDI2NDIwODAwLCJodHRwOi8vdG9wdGFsLmNvbS9qd3RfY2xhaW1zL2lzX2FkbWluIjp0cnVlLCJjb21wYW55IjoiVG9wdGFsIiwiYXdlc29tZSI6dHJ1ZX0.
yRQYnWzskCZUxPwaQupWkiUzKELZ49eM7oWxAQK_ZXw 
```

---
4. Burp Suite Api Scan

![image](https://github.com/user-attachments/assets/74a46f9f-c984-4167-b5d2-d825d8d00cb8)

![image](https://github.com/user-attachments/assets/c49ff740-0a39-4c63-a437-47b8be94b667)

![image](https://github.com/user-attachments/assets/fa391dd8-0bfd-40bb-aa76-c9197350f81a)

---
5. Swagger Convertor in Burp Suite requests
```
python3 swagger.py -h
usage: swagger.py [-h] [-t TOKEN] [-H HOST] [--swagger-file SWAGGER_FILE] [--output-dir OUTPUT_DIR]

Convert Swagger JSON to Burp Suite requests

optional arguments:
  -h, --help                       # Show this help message and exit
  -t TOKEN, --token TOKEN          # Access token to include in Authorization header as Bearer token
  -H HOST, --host HOST             # Custom Host header value
  --swagger-file SWAGGER_FILE      # Path to the Swagger JSON file
  --output-dir OUTPUT_DIR          # Directory to save Burp request files
```
6. Token-Tailor

https://github.com/forteBruno/Token-Tailor

![image](https://github.com/user-attachments/assets/b9965c39-b24d-4bfd-af33-cd32c12bc859)
