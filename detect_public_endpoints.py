import json
import argparse

def detect_public_endpoints(swagger_file):
    with open(swagger_file, 'r', encoding='utf-8') as f:
        spec = json.load(f)

    paths = spec.get("paths", {})
    security_definitions = spec.get("securityDefinitions", None)
    global_security = spec.get("security", None)

    public_endpoints = []

    for path, methods in paths.items():
        for method, operation in methods.items():
            if method not in {"get", "post", "put", "delete", "patch", "options", "head"}:
                continue

            operation_security = operation.get("security", None)

            # Determine if the endpoint is public
            if security_definitions or global_security:
                # If security is explicitly empty, it's public
                if operation_security == []:
                    public_endpoints.append((method.upper(), path))
                # Otherwise (None or non-empty), it's protected
            else:
                # No global security defined, treat all as public
                public_endpoints.append((method.upper(), path))

    return public_endpoints

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect public (unauthenticated) endpoints in Swagger JSON files")
    parser.add_argument('--swagger', nargs='+', required=True, help='Path(s) to Swagger JSON file(s)')

    args = parser.parse_args()

    for file in args.swagger:
        try:
            public = detect_public_endpoints(file)
            print(f"\nPublic endpoints in {file}:")
            if public:
                for method, endpoint in public:
                    print(f"  {method} {endpoint}")
            else:
                print("  No public endpoints found.")
        except Exception as e:
            print(f"Error processing {file}: {e}")
