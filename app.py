"""Local entrypoint for the Server Monitor demo."""

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Local demo only — binds to localhost.
    app.run(host="127.0.0.1", port=5000, debug=True)
