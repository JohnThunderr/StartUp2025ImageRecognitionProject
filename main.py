from website import create_app

app = create_app()

if __name__ == "__main__":
    print("Starting Tree Detection App...")
    print("Open your browser at http://127.0.0.1:5000/")
    app.run(debug=True)
