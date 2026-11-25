"""Local entrypoint for the Server Monitor demo."""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Local demo only — binds to localhost.
    # Default 5027 avoids collisions with other demos often bound to 5000.
    port = int(os.environ.get("PORT", "5027"))
    app.run(host="127.0.0.1", port=port, debug=True)
