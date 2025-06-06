import json
import os
import argparse
from urllib.parse import urlencode

def parse_openapi(file_path):
    with open(file_path, 'r') as f:
        openapi_data = json.load(f)
    return openapi_data

def create_burp_request(method, path, host, params, headers, body=None):
    request = f"{method.upper()} {path} HTTP/1.1\r\n"
    request += f"Host: {host}\r\n"
    for header, value in headers.items():
        request += f"{header}: {value}\r\n"
    request += "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\n"
    request += "Accept: application/json\r\n"
    request += "Connection: close\r\n"
    
    if method.upper() in ["POST", "PUT"] and body:
        request += f"Content-Type: application/json\r\n"
        request += f"Content-Length: {len(body)}\r\n"
        request += "\r\n"
        request += body
    else:
        request += "\r\n"
    
    return request

def generate_burp_requests(openapi_data, host, auth_token, proxy):
    # Create output directory
    output_dir = "burp_requests"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    paths = openapi_data.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            operation_id = details.get("operationId", "unknown_operation")
            filename = f"{output_dir}/{method}_{operation_id}.txt"
            
            # Handle query parameters
            query_params = {}
            for param in details.get("parameters", []):
                if param["in"] == "query":
                    schema = param.get("schema", {})
                    param_name = param["name"]
                    default_value = schema.get("default", "") if schema.get("default") is not None else "example"
                    query_params[param_name] = default_value
            
            # Construct path with query parameters
            full_path = path
            if query_params:
                full_path += "?" + urlencode(query_params)
            
            # Handle request body
            body = None
            if "requestBody" in details:
                content = details["requestBody"].get("content", {})
                if "application/json" in content:
                    schema_ref = content["application/json"].get("schema", {}).get("$ref")
                    if schema_ref:
                        schema_name = schema_ref.split("/")[-1]
                        schema = openapi_data["components"]["schemas"].get(schema_name, {})
                        body = json.dumps({prop: "example" for prop in schema.get("properties", {})})
                    else:
                        body = json.dumps({"example": "data"})
                elif "multipart/form-data" in content:
                    body = "--boundary\nContent-Disposition: form-data; name=\"example\"\n\nexample\n--boundary--"
                    headers["Content-Type"] = "multipart/form-data; boundary=boundary"
                elif "application/x-www-form-urlencoded" in content:
                    body = urlencode({"example": "data"})
                    headers["Content-Type"] = "application/x-www-form-urlencoded"
            
            # Create Burp request
            request = create_burp_request(method, full_path, host, query_params, headers, body)
            
            # Save to file
            with open(filename, "w") as f:
                f.write(request)
            
            # If proxy is specified, send request to Burp Suite
            if proxy:
                import requests
                proxies = {
                    "http": f"http://{proxy}",
                    "https": f"http://{proxy}"
                }
                try:
                    url = f"http://{host}{full_path}"
                    if method.upper() == "GET":
                        requests.get(url, headers=headers, proxies=proxies)
                    elif method.upper() == "POST":
                        requests.post(url, headers=headers, data=body, proxies=proxies)
                    elif method.upper() == "PUT":
                        requests.put(url, headers=headers, data=body, proxies=proxies)
                    elif method.upper() == "DELETE":
                        requests.delete(url, headers=headers, proxies=proxies)
                except Exception as e:
                    print(f"Error sending request to {url}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate Burp Suite requests from OpenAPI documentation")
    parser.add_argument("--file", required=True, help="Path to OpenAPI JSON file")
    parser.add_argument("--host", required=True, help="Host header (e.g., example.com)")
    parser.add_argument("--auth-token", help="Authorization token (Bearer token)")
    parser.add_argument("--proxy", help="Proxy address for Burp Suite (e.g., 127.0.0.1:8080)")
    
    args = parser.parse_args()
    
    openapi_data = parse_openapi(args.file)
    generate_burp_requests(openapi_data, args.host, args.auth_token, args.proxy)

if __name__ == "__main__":
    main()
