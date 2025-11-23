from flask import Flask, request, jsonify

app = Flask(__name__)

# Dein existierendes Programm hier importieren:
# from globe_generator import generate_globe_pattern
from pattern import Loader, StitchCoordinates, colorword, PatternGenerator
@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    loader = data.get("loader")
    stitch_coordinates = data.get("stitch_coordinates")

    # Ergebnis erzeugen
    #stitch_coordinates = StitchCoordinates(2, 2, 1, 1)
    #loader = Loader("C:\\Users\\arian\\OneDrive\\Dokumente\\GitHub\\GlobeCrochetPattern\\Data\\*.tif")
    pattern_generator = PatternGenerator(loader, stitch_coordinates)
    result=pattern_generator.generate()


    return jsonify({"result": result})

if __name__ == "__main__":
    app.run()
