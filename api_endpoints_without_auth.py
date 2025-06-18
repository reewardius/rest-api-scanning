# python3 api_endpoints_without_auth.py -url https://example.com/swagger/v1/swagger.json
# python3 api_endpoints_without_auth.py -f urls.txt -silent

import json
import argparse
import requests
import sys
from urllib.parse import urlparse
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_swagger(url):
    """Download Swagger/OpenAPI spec from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        # Try to parse as JSON
        try:
            return response.json()
        except json.JSONDecodeError:
            # If not JSON, might be YAML
            try:
                import yaml
                return yaml.safe_load(response.text)
            except ImportError:
                print(f"Warning: YAML support not available. Install PyYAML for YAML support.")
                return None
            except yaml.YAMLError:
                print(f"Error: Unable to parse response as JSON or YAML from {url}")
                return None
                
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None

def detect_public_endpoints(spec_data):
    """Detect public endpoints from Swagger/OpenAPI spec data"""
    if not spec_data:
        return []

    paths = spec_data.get("paths", {})
    security_definitions = spec_data.get("securityDefinitions", None) or spec_data.get("components", {}).get("securitySchemes", None)
    global_security = spec_data.get("security", None)

    public_endpoints = []

    for path, methods in paths.items():
        for method, operation in methods.items():
            if method.lower() not in {"get", "post", "put", "delete", "patch", "options", "head"}:
                continue

            operation_security = operation.get("security", None)

            # Determine if the endpoint is public
            if security_definitions or global_security:
                # If security is explicitly empty, it's public
                if operation_security == []:
                    public_endpoints.append((method.upper(), path))
                # If operation_security is None and there's no global security, it might be public
                elif operation_security is None and not global_security:
                    public_endpoints.append((method.upper(), path))
            else:
                # No global security defined, treat all as public
                public_endpoints.append((method.upper(), path))

    return public_endpoints

def process_url(url, silent=False):
    """Process a single URL and return results"""
    if not silent:
        print(f"Processing: {url}")
    
    spec_data = download_swagger(url)
    if not spec_data:
        if not silent:
            print(f"Failed to download or parse: {url}")
        return url, []
    
    public_endpoints = detect_public_endpoints(spec_data)
    return url, public_endpoints

def format_output(url, endpoints, silent=False, separator="-----"):
    """Format output for a single URL"""
    output_lines = []
    
    if silent:
        if endpoints:
            output_lines.append(url)
    else:
        output_lines.append(f"\n{separator}")
        output_lines.append(f"Public endpoints in {url}:")
        if endpoints:
            for method, endpoint in endpoints:
                output_lines.append(f"  {method} {endpoint}")
        else:
            output_lines.append("  No public endpoints found.")
        output_lines.append(separator)
    
    return "\n".join(output_lines)

def main():
    parser = argparse.ArgumentParser(description="Detect public (unauthenticated) endpoints in Swagger/OpenAPI specs")
    
    # URL options
    parser.add_argument('-url', '--url', help='Single Swagger/OpenAPI URL to check')
    parser.add_argument('-f', '--file', help='File containing URLs to check (one per line)')
    
    # Output options
    parser.add_argument('-o', '--output', help='Output file to write results')
    parser.add_argument('-silent', '--silent', action='store_true', 
                       help='Silent mode: only output URLs with public endpoints')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.url and not args.file:
        parser.error("Either -url or -f must be specified")
    
    if args.url and args.file:
        parser.error("Cannot specify both -url and -f at the same time")
    
    urls = []
    
    # Collect URLs
    if args.url:
        urls.append(args.url)
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            print(f"Error: File {args.file} not found")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file {args.file}: {e}")
            sys.exit(1)
    
    if not urls:
        print("No URLs to process")
        sys.exit(1)
    
    # Process URLs
    all_results = []
    urls_with_results = []
    
    for url in urls:
        try:
            url_clean = url.strip()
            if not url_clean:
                continue
                
            # Add protocol if missing
            if not url_clean.startswith(('http://', 'https://')):
                url_clean = 'https://' + url_clean
            
            processed_url, endpoints = process_url(url_clean, args.silent)
            
            if endpoints or not args.silent:
                result_output = format_output(processed_url, endpoints, args.silent, 
                                            separator="#####" if args.file else "-----")
                all_results.append(result_output)
                
                if endpoints:
                    urls_with_results.append(processed_url)
            
            # Small delay to be respectful
            if len(urls) > 1:
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            break
        except Exception as e:
            if not args.silent:
                print(f"Error processing {url}: {e}")
            continue
    
    # Output results
    final_output = "\n".join(all_results)
    
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                if args.silent:
                    # In silent mode, write only URLs with results
                    f.write("\n".join(urls_with_results))
                else:
                    f.write(final_output)
            
            if not args.silent:
                print(f"\nResults written to {args.output}")
                if urls_with_results:
                    print(f"Found public endpoints in {len(urls_with_results)} URL(s)")
        except Exception as e:
            print(f"Error writing to output file: {e}")
            sys.exit(1)
    else:
        if final_output.strip():
            print(final_output)
        elif not args.silent:
            print("No results to display")

if __name__ == "__main__":
    main()
