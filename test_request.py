import urllib.request
import json

url = "http://127.0.0.1:8000/requirements/analyze"
payload = {
    "brd_text": "The checkout system must allow guest users to purchase items. It must integrate with Stripe for payments and send an email receipt via SendGrid.",
    "frd_text": "The frontend cart component should have a 'Checkout as Guest' button. It will call POST /api/checkout with an items array. Stripe tokens are handled locally via JS.",
    "github_repo_url": "https://github.com/myorg/awesome-ecommerce-checkout"
}

data = json.dumps(payload).encode('utf-8')
headers = {'Content-Type': 'application/json'}
req = urllib.request.Request(url, data=data, headers=headers, method='POST')

try:
    print(f"Sending POST to {url} ...")
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print("\\n=== RESPONSE (Status:", response.status, ") ===")
        print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {e}")
