from flask import Flask, render_template

app = Flask(__name__)


# Loading page
@app.route("/")
def loading():
    return render_template("common/loading.html")


# Role selection page
@app.route("/roles")
def role_selection():
    return render_template("common/role_selection.html")


if __name__ == "__main__":
    app.run(debug=True)