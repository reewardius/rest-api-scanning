import json
import os
import argparse
import base64
import requests
import shutil
from urllib.parse import urlencode
from jsonschema import validate, ValidationError
from uuid import uuid4

# OpenAPI v3 schema for validation (simplified)
OPENAPI_SCHEMA = {
    "type": "object",
    "required": ["openapi", "info", "paths"],
    "properties": {
        "openapi": {"type": "string"},
        "info": {"type": "object"},
        "paths": {"type": "object"},
        "components": {"type": "object"}
    }
}

def validate_openapi(data):
    """Validate OpenAPI document against a simplified schema."""
    try:
        validate(instance=data, schema=OPENAPI_SCHEMA)
        return True
    except ValidationError as e:
        print(f"OpenAPI validation error: {e}")
        return False

def parse_openapi(file_path):
    """Parse and validate OpenAPI JSON file."""
    try:
        with open(file_path, 'r') as f:
            openapi_data = json.load(f)
        if not validate_openapi(openapi_data):
            raise ValueError("Invalid OpenAPI document")
        return openapi_data
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        raise
    except Exception as e:
        print(f"Error reading OpenAPI file: {e}")
        raise

def generate_example_value(schema, components):
    """Generate example value for a schema, handling enums, arrays, and references."""
    if not schema:
        return "example"
    
    schema_type = schema.get("type")
    if "enum" in schema:
        return schema["enum"][0] if schema["enum"] else "example"
    elif schema_type == "string":
        return schema.get("default", "example")
    elif schema_type == "integer":
        return schema.get("default", 0)
    elif schema_type == "number":
        return schema.get("default", 0.0)
    elif schema_type == "boolean":
        return schema.get("default", True)
    elif schema_type == "array":
        items_schema = schema.get("items", {})
        return [generate_example_value(items_schema, components)]
    elif schema_type == "object":
        properties = schema.get("properties", {})
        return {prop: generate_example_value(prop_schema, components) for prop, prop_schema in properties.items()}
    elif "$ref" in schema:
        ref_path = schema["$ref"].split("/")
        schema_name = ref_path[-1]
        ref_schema = components.get("schemas", {}).get(schema_name, {})
        return generate_example_value(ref_schema, components)
    return "example"

def replace_path_params(path, parameters, components):
    """Replace path parameters in URL with example values."""
    result = path
    for param in parameters:
        if param.get("in") == "path":
            param_name = param["name"]
            schema = param.get("schema", {})
            value = generate_example_value(schema, components)
            result = result.replace(f"{{{param_name}}}", str(value))
    return result

def get_auth_headers(openapi_data, auth_value, auth_type):
    """Generate authentication headers based on auth type."""
    headers = {}
    if auth_value and auth_type:
        if auth_type == "bearer":
            headers["Authorization"] = f"Bearer {auth_value}"
        elif auth_type == "apiKey":
            headers["X-API-Key"] = auth_value
        elif auth_type == "basic":
            encoded = base64.b64encode(auth_value.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
    return headers

def create_burp_request(method, path, host, headers, body=None, content_type="application/json"):
    """Generate HTTP request string in Burp Suite format."""
    # Build request line and headers
    request_lines = [f"{method.upper()} {path} HTTP/1.1", f"Host: {host}"]
    for header, value in headers.items():
        request_lines.append(f"{header}: {value}")
    request_lines.append("User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    request_lines.append("Accept: application/json")
    request_lines.append("Connection: close")
    
    # Add Content-Type and Content-Length for methods with body
    if method.upper() in ["POST", "PUT", "PATCH"] and body:
        request_lines.append(f"Content-Type: {content_type}")
        request_lines.append(f"Content-Length: {len(body)}")
    
    # Add single empty line and body (if present)
    request_lines.append("")
    if body:
        request_lines.append(body)
    
    # Join lines with \r\n
    return "\r\n".join(request_lines)

def generate_burp_requests(openapi_data, host, auth_value, auth_type, proxy):
    """Generate Burp Suite requests from OpenAPI document."""
    # Remove existing burp_requests directory
    output_dir = "burp_requests"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    headers = get_auth_headers(openapi_data, auth_value, auth_type)
    paths = openapi_data.get("paths", {})
    components = openapi_data.get("components", {})
    
    for path, methods in paths.items():
        for method, details in methods.items():
            operation_id = details.get("operationId", f"{method}_{uuid4().hex[:8]}")
            filename = f"{output_dir}/{method}_{operation_id}.txt"
            
            # Handle all parameter types
            query_params = {}
            path_params = []
            for param in details.get("parameters", []):
                schema = param.get("schema", {})
                param_name = param["name"]
                if param["in"] == "query":
                    query_params[param_name] = generate_example_value(schema, components)
                elif param["in"] == "path":
                    path_params.append(param)
            
            # Replace path parameters
            full_path = replace_path_params(path, path_params, components)
            if query_params:
                full_path += "?" + urlencode(query_params)
            
            # Handle request body and content type
            body = None
            content_type = "application/json"
            if "requestBody" in details:
                content = details["requestBody"].get("content", {})
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    body = json.dumps(generate_example_value(schema, components))
                    content_type = "application/json"
                elif "multipart/form-data" in content:
                    body = "--boundary\nContent-Disposition: form-data; name=\"example\"\n\nexample\n--boundary--"
                    content_type = "multipart/form-data; boundary=boundary"
                    headers["Content-Type"] = content_type
                elif "application/x-www-form-urlencoded" in content:
                    body = urlencode({"example": "data"})
                    content_type = "application/x-www-form-urlencoded"
                    headers["Content-Type"] = content_type
            
            # Create Burp request
            request = create_burp_request(method, full_path, host, headers, body, content_type)
            
            # Save to file with explicit \r\n line endings
            with open(filename, "w", newline='') as f:
                f.write(request)
            
            # Send request to proxy if specified
            if proxy:
                proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
                try:
                    url = f"http://{host}{full_path}"
                    method = method.upper()
                    request_func = {
                        "GET": requests.get,
                        "POST": requests.post,
                        "PUT": requests.put,
                        "PATCH": requests.patch,
                        "DELETE": requests.delete,
                        "OPTIONS": requests.options
                    }.get(method)
                    
                    if request_func:
                        request_func(url, headers=headers, data=body, proxies=proxies)
                    else:
                        print(f"Unsupported HTTP method: {method}")
                except Exception as e:
                    print(f"Error sending request to {url}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate Burp Suite requests from OpenAPI documentation")
    parser.add_argument("--file", required=True, help="Path to OpenAPI JSON file")
    parser.add_argument("--host", required=True, help="Host header (e.g., example.com)")
    parser.add_argument("--auth-value", help="Authentication value (Bearer token, API key, or user:pass for Basic Auth)")
    parser.add_argument("--auth-type", choices=["bearer", "apiKey", "basic"], default="bearer", help="Authentication type")
    parser.add_argument("--proxy", help="Proxy address for Burp Suite (e.g., 127.0.0.1:8080)")
    
    args = parser.parse_args()
    
    openapi_data = parse_openapi(args.file)
    generate_burp_requests(openapi_data, args.host, args.auth_value, args.auth_type, args.proxy)

if __name__ == "__main__":
    main()
