from flask import Flask, render_template
import planeTracker as pt

app = Flask(__name__)

@app.route("/")
def index():
	planes = pt.get_planes()
	data = pt.show_frame(planes['flyovers']).to_html()

	return render_template("index.html", data=data)
