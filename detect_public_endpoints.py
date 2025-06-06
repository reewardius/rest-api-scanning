import json
import argparse

def detect_public_endpoints(swagger_file):
    with open(swagger_file, 'r', encoding='utf-8') as f:
        spec = json.load(f)

    paths = spec.get("paths", {})
    security_definitions = spec.get("securityDefinitions", None)

    public_endpoints = []

    for path, methods in paths.items():
        for method, operation in methods.items():
            if method not in {"get", "post", "put", "delete", "patch", "options", "head"}:
                continue

            if security_definitions:
                if operation.get("security") == []:
                    public_endpoints.append((method.upper(), path))
            else:
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
