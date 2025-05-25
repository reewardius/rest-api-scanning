# rest-api-scanning




1. Load + Autofill -> Send to Burp -> Burp Export Items -> Nuclei DAST Scanning

https://github.com/reewardius/Swagger-EZ

![image](https://github.com/user-attachments/assets/4d6a4cd9-09de-4095-a729-21d7200ced5f)


![image](https://github.com/user-attachments/assets/0904122b-b575-4203-8373-eedcc6da3658)

2. Nuclei DAST (OpenAPI)

![image](https://github.com/user-attachments/assets/0e4e1a2d-7093-4f86-95c1-0c70e767d629)
![image](https://github.com/user-attachments/assets/435bdac6-971c-4f04-a576-1f594fb27abd)

```
nuclei -l openapi.yaml -im openapi -t nuclei-dast-templates/
```

![image](https://github.com/user-attachments/assets/ddd0bbce-41f9-40fe-b09c-d185bfb71b6b)

3. Burp Suite Api Scan

![image](https://github.com/user-attachments/assets/74a46f9f-c984-4167-b5d2-d825d8d00cb8)

![image](https://github.com/user-attachments/assets/c49ff740-0a39-4c63-a437-47b8be94b667)

![image](https://github.com/user-attachments/assets/fa391dd8-0bfd-40bb-aa76-c9197350f81a)
