from __future__ import annotations
import os
import uvicorn

def main():
    from agents_boot.server.api import api
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(api, host=host, port=port)

if __name__ == "__main__":
    main()
