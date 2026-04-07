import os

from backend import create_app


app = create_app()
PORT = int(os.getenv("PORT", "5000"))


if __name__ == "__main__":
    if app.config["DEBUG"]:
        app.run(host="0.0.0.0", port=PORT, debug=True)
    else:
        from waitress import serve

        # Waitress is more appropriate than Flask's dev server for normal local deployment.
        serve(app, host="0.0.0.0", port=PORT)
