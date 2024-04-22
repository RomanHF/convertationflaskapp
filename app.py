import json

from flask import Flask, request, Response, jsonify

from config import VALIDATE_OUTPUT_XML, VALIDATE_INPUT_XML
from json_service import entrant_data_to_xml
from xml_service import entrant_to_json

app = Flask(__name__)


@app.route('/EntrantToXml', methods=['POST'])
def entrant_ro_json():
    try:
        entrant_json = json.loads(request.json)  # require content-type: application/json
    except Exception as e:
        return Response(f"Cant get json: {str(e)}", status=400)
    if not entrant_json:
        return Response("No content", status=400)
    try:
        entrant_xml = entrant_data_to_xml(entrant_json, validate=VALIDATE_OUTPUT_XML)
        return Response(entrant_xml, content_type="application/xml")
    except Exception as e:
        return Response(f"Failed to convert: {str(e)}", status=400)


@app.route('/EntrantToJson', methods=['POST'])
def entrant_to_xml():
    if request.content_type != "application/xml":
        return Response("incorrect content type", status=415)
    entrant_data = request.get_data(as_text=True)
    if not entrant_data:
        return Response("No data", status=400)
    try:
        entrant_json = entrant_to_json(entrant_data, validate=VALIDATE_INPUT_XML)
        return jsonify(entrant_json)
    except Exception as e:
        return Response(str(e), status=400)


if __name__ == "__main__":
    app.run(port=5007)
