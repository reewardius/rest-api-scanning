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
3. Burp Suite Api Scan

![image](https://github.com/user-attachments/assets/74a46f9f-c984-4167-b5d2-d825d8d00cb8)

![image](https://github.com/user-attachments/assets/c49ff740-0a39-4c63-a437-47b8be94b667)

![image](https://github.com/user-attachments/assets/fa391dd8-0bfd-40bb-aa76-c9197350f81a)


---
4. Convert Swagger to Burp Suite requests
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
#### Example
```
python3 swagger.py --swagger-file swagger.json -t <jwt_token> -H api.example.com
```
---

5. Convert OpenAPI to Burp Suite requests
```
pip install jsonschema requests
```
##### Help
```
python openapi_parse_v1.py -h
usage: openapi_parse_v1.py [-h] --file FILE --host HOST [--auth-value AUTH_VALUE]
                        [--auth-type {bearer,apiKey,basic}] [--proxy PROXY]

Generate Burp Suite requests from OpenAPI documentation

optional arguments:
  -h, --help            show this help message and exit
  --file FILE           Path to OpenAPI JSON file
  --host HOST           Host header (e.g., example.com)
  --auth-value AUTH_VALUE
                        Authentication value (Bearer token, API key, or
                        user:pass for Basic Auth)
  --auth-type {bearer,apiKey,basic}
                        Authentication type
  --proxy PROXY         Proxy address for Burp Suite (e.g., 127.0.0.1:8080)
```
##### Example:
```
python3 openapi_parse_v1.py --file openapi.json --host example.com --auth-value <jwt_token> --auth-type bearer --proxy 127.0.0.1:8080
python3 openapi_parse_v1.py --file openapi.json --host example.com --auth-value user:pass --auth-type basic --proxy 127.0.0.1:8080
python3 openapi_parse_v1.py --file openapi.json --host example.com --auth-value my-api-key-123 --auth-type apiKey    // Custom HTTP Header -> X-API-Key (can be changed in code)
```
**All Generate API requests will be saved in the burp_requests/ folder**

![image](https://github.com/user-attachments/assets/92c49442-5391-4ebb-a08d-f7e610fcb3d3)

---

6. Token-Tailor

https://github.com/forteBruno/Token-Tailor

![image](https://github.com/user-attachments/assets/b9965c39-b24d-4bfd-af33-cd32c12bc859)
