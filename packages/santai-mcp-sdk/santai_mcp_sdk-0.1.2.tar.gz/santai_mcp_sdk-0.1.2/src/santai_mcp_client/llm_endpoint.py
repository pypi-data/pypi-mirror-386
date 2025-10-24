import time
import requests


def call_llm(messages, base_endpoint, api_key, model="llama3.1-bedrock"):
    if not base_endpoint:
        raise RuntimeError("OPENAI_API_BASE_URL is not set")

    url = f"{base_endpoint}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "response_format": {"type": "json_object"},  # ignored if unsupported
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    # Separate connect/read timeouts; long read for bigger prompts
    connect_to = 5.0
    read_to = 60.0

    # Simple retry loop to mirror previous behavior (3 attempts, backoff 0.5s, retry on 429/5xx)
    status_forcelist = {429, 500, 502, 503, 504}
    attempts = 3
    backoff = 0.5
    last_exc = None

    for i in range(attempts):
        try:
            resp = requests.post(
                url, json=payload, headers=headers, timeout=(connect_to, read_to)
            )
            # Retry on specific status codes
            if resp.status_code in status_forcelist:
                if i < attempts - 1:
                    time.sleep(backoff * (2**i))
                    continue
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            if isinstance(content, list):
                content = "".join(
                    p.get("text", "") if isinstance(p, dict) else str(p)
                    for p in content
                )
            return (content or "").strip()
        except (requests.RequestException, ValueError) as e:
            last_exc = e
            if i < attempts - 1:
                time.sleep(backoff * (2**i))
                continue
            raise

    # Shouldn’t reach here; re-raise last exception if it somehow does
    if last_exc:
        raise last_exc
