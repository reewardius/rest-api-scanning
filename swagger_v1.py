# python swagger.py --swagger-file swagger.json --output-dir burp_requests --proxy http://127.0.0.1:8080 --host example.com -t <jwt_token>

import json
import os
import shutil
import argparse
import requests
from urllib.parse import urlencode

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_swagger_file(file_path):
    """Load and parse the Swagger JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_sample_body(schema_ref, definitions=None, required_fields=None, depth=0, max_depth=5):
    """Generate a sample JSON body based on the schema, including required and optional fields."""
    if depth > max_depth:
        return {}  # Prevent infinite recursion
    if not schema_ref or not definitions:
        return {}

    # Resolve the schema reference
    ref_path = schema_ref.get('$ref', '')
    if ref_path:
        schema_key = ref_path.split('/')[-1]
        schema = definitions.get(schema_key, {})
    else:
        schema = schema_ref

    if not schema:
        return {}

    sample_body = {}
    properties = schema.get('properties', {})
    required = required_fields or schema.get('required', [])

    for name, prop in properties.items():
        # Include both required and optional fields
        prop_type = prop.get('type')
        prop_ref = prop.get('$ref')
        prop_default = prop.get('default')
        prop_example = prop.get('example')
        value = prop_example or prop_default

        if prop_type == 'string':
            sample_body[name] = value if value is not None else f"sample_{name}"
        elif prop_type == 'number' or prop_type == 'integer':
            sample_body[name] = value if value is not None else 123
        elif prop_type == 'boolean':
            sample_body[name] = value if value is not None else True
        elif prop_type == 'array':
            items_ref = prop.get('items', {}).get('$ref', '')
            if items_ref:
                item_schema = {'$ref': items_ref}
                sample_body[name] = [generate_sample_body(item_schema, definitions, [], depth + 1, max_depth)]
            else:
                item_type = prop.get('items', {}).get('type', 'string')
                sample_body[name] = [f"sample_{name}_item" if item_type == 'string' else 123]
        elif prop_type == 'object' or prop_ref:
            nested_schema = prop if prop_type == 'object' else {'$ref': prop_ref}
            sample_body[name] = generate_sample_body(nested_schema, definitions, [], depth + 1, max_depth)

    # Ensure all required fields are included
    for req_field in required:
        if req_field not in sample_body:
            sample_body[req_field] = f"sample_{req_field}"

    return sample_body

def generate_burp_request(method, path, host, base_path, schemes, parameters, operation_id, body_schema=None, definitions=None, token=None, custom_host=None):
    """Generate a Burp Suite-compatible HTTP request string."""
    # Use only the path for the request line, normalize to avoid double slashes
    request_path = f"{base_path}{path}".replace('//', '/')
    
    # Initialize query parameters
    query_params = []
    headers = {
        "Host": custom_host if custom_host else host,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Add Authorization header if token is provided
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = ""

    # Process parameters
    for param in parameters:
        param_name = param.get('name')
        param_in = param.get('in')
        param_required = param.get('required', False)
        param_type = param.get('type', 'string')
        param_default = param.get('default', '')

        if param_in == 'query':
            # Add query parameters
            value = param_default or f"{{{{input_{param_name}}}}}" if not param_required else f"sample_{param_type}"
            query_params.append((param_name, value))
        elif param_in == 'header':
            # Add headers (skip Authorization if token is provided)
            if param_name.lower() != 'authorization' or not token:
                headers[param_name] = param_default or f"{{{{input_{param_name}}}}}" if not param_required else f"sample_{param_type}"
        elif param_in == 'path':
            # Replace path parameters in path
            value = param_default or f"{{{{input_{param_name}}}}}" if not param_required else f"sample_{param_type}"
            request_path = request_path.replace(f"{{{param_name}}}", value)
        elif param_in == 'body' and body_schema:
            # Generate sample body based on schema
            body = json.dumps(generate_sample_body(body_schema, definitions, body_schema.get('required', [])), indent=2)

    # Append query parameters to path if any
    if query_params:
        request_path += '?' + urlencode(query_params)

    # Normalize path again to handle any double slashes introduced by query params
    request_path = request_path.replace('//', '/')

    # Construct the HTTP request
    request_lines = [
        f"{method.upper()} {request_path} HTTP/1.1"
    ]
    for header, value in headers.items():
        request_lines.append(f"{header}: {value}")

    # Add body if present for POST, PUT, PATCH, DELETE
    if body and method.upper() in ['POST', 'PUT', 'PATCH', 'DELETE']:
        request_lines.append("")
        request_lines.append(body)

    return "\n".join(request_lines), headers, body, request_path

def send_to_burp(method, request_path, headers, body, scheme, host, proxy):
    """Send the HTTP request to Burp Suite via the specified proxy."""
    url = f"{scheme}://{host}{request_path}"
    proxies = {
        "http": proxy,
        "https": proxy
    }
    
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            data=body if body else None,
            proxies=proxies,
            verify=False  # Disable SSL verification for testing (optional, adjust as needed)
        )
        print(f"Sent request to {url}, status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Failed to send request to {url}: {e}")

def save_burp_request(request, operation_id, output_dir):
    """Save the Burp request to a file."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Sanitize operation_id to create a valid filename
    safe_operation_id = operation_id.replace('/', '_').replace(' ', '_')
    file_path = os.path.join(output_dir, f"{safe_operation_id}.txt")
    
    with open(file_path, 'w') as f:
        f.write(request)

def main(swagger_file, output_dir, token=None, custom_host=None, proxy=None):
    """Main function to process Swagger JSON and generate Burp requests."""
    # Delete the output directory if it exists
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    # Create a new output directory
    os.makedirs(output_dir)
    
    swagger_data = load_swagger_file(swagger_file)
    
    host = swagger_data.get('host', 'feedback.arlo.com')
    base_path = swagger_data.get('basePath', '/')
    schemes = swagger_data.get('schemes', ['https'])
    paths = swagger_data.get('paths', {})
    definitions = swagger_data.get('definitions', {})

    for path, methods in paths.items():
        for method, details in methods.items():
            operation_id = details.get('operationId', f"{method}_{path.replace('/', '_')}")
            parameters = details.get('parameters', [])
            body_schema = None
            for param in parameters:
                if param.get('in') == 'body':
                    body_schema = param.get('schema', {})
            
            # Generate the request and extract components for sending
            request, headers, body, request_path = generate_burp_request(method, path, host, base_path, schemes, parameters, operation_id, body_schema, definitions, token, custom_host)
            
            # Save the request to a file
            save_burp_request(request, operation_id, output_dir)
            print(f"Generated Burp request for {operation_id}")

            # Send to Burp Suite if proxy is specified
            if proxy:
                scheme = schemes[0] if schemes else 'https'
                send_to_burp(method, request_path, headers, body, scheme, host, proxy)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Swagger JSON to Burp Suite requests")
    parser.add_argument('-t', '--token', type=str, help='Access token to include in Authorization header as Bearer token')
    parser.add_argument('-H', '--host', type=str, help='Custom Host header value')
    parser.add_argument('--swagger-file', type=str, default="swagger.json", help='Path to the Swagger JSON file')
    parser.add_argument('--output-dir', type=str, default="burp_requests", help='Directory to save Burp request files')
    parser.add_argument('--proxy', type=str, help='Proxy URL for sending requests to Burp Suite (e.g., http://127.0.0.1:8080)')
    args = parser.parse_args()

    main(args.swagger_file, args.output_dir, args.token, args.host, args.proxy)
