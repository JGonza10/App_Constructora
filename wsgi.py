from dotenv import load_dotenv
load_dotenv()

from constructora import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(__import__("os").environ.get("PORT", 5000)))
