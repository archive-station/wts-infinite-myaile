from flask import Flask, request, send_file
from flask_cors import CORS, cross_origin
from io import BytesIO
import os

SAVEDATA_HEADER = b"BX30"
SAVEDATA_MYAILE_COUNT_POSITION_ENTRY_BYTE = b" "
SAVEDATA_MYAILE_COUNT_POSITIONS = [0x2873, 0x286B]
SAVEDATA_MAXIMUM_MYAILE_COUNT = 32767

API_GET_MYAILE_COUNT_ACTION = "wts_infinite_myaile.api_endpoint.get_myaile_count"
API_UPDATE_MYAILE_COUNT_ACTION = "wts_infinite_myaile.api_endpoint.update_myaile_count"

API_ERROR_MESSAGE_NO_SAVEDATA_PROVIDED = "no savedata provided"
API_ERROR_MESSAGE_NO_KNOWN_ACTION_PROVIDED = "no known action provided"
API_ERROR_MESSAGE_INVALID_SAVEDATA_PROVIDED = "invalid savedata provided"
API_ERROR_MESSAGE_CANT_FIND_MYAILE_COUNT_IN_SAVEDATA = "can't find myaile count in savedata"

app = Flask(__name__, static_url_path=None)
cors = CORS(app)


# TODO(mikhail): move to frontend framework
@app.get("/wts-infinite-myaile/")
def index_page():
    return send_file("index.html")


def go_to_myaile_count_position(savedata):
    for position in SAVEDATA_MYAILE_COUNT_POSITIONS:
        savedata.seek(position - 2, os.SEEK_SET)
        if savedata.read(1) != SAVEDATA_MYAILE_COUNT_POSITION_ENTRY_BYTE:
            continue

        return savedata.seek(position, os.SEEK_SET)

    return -1


# TODO(mikhail): figure out the savedata structure
# TODO(mikhail): replace it by sane API
@app.post("/wts-infinite-myaile/")
@cross_origin()
def api_endpoint():
    savedata = request.files.get("savedata")

    if savedata is None:
        return {"message": API_ERROR_MESSAGE_NO_SAVEDATA_PROVIDED}, 400

    if savedata.read(4) != SAVEDATA_HEADER:
        return {"message": API_ERROR_MESSAGE_INVALID_SAVEDATA_PROVIDED}, 400

    action = request.form.get("action")

    if action == API_GET_MYAILE_COUNT_ACTION:
        if go_to_myaile_count_position(savedata) == -1:
            return {"message": API_ERROR_MESSAGE_CANT_FIND_MYAILE_COUNT_IN_SAVEDATA}, 400

        myaile_count = int.from_bytes(savedata.read(2), "big", signed=True)
        return {"myaile_count": myaile_count}

    if action == API_UPDATE_MYAILE_COUNT_ACTION:
        actual_pos = go_to_myaile_count_position(savedata)

        if actual_pos == -1:
            return {"message": API_ERROR_MESSAGE_CANT_FIND_MYAILE_COUNT_IN_SAVEDATA}, 400

        savedata.seek(0, os.SEEK_SET)
        updated_savedata = BytesIO()

        updated_savedata.write(savedata.read(actual_pos))
        updated_savedata.write(SAVEDATA_MAXIMUM_MYAILE_COUNT.to_bytes(2, "big", signed=True))

        savedata.seek(2, os.SEEK_CUR)
        updated_savedata.write(savedata.read())

        return updated_savedata.getvalue(), 200, {
            "Content-Type": "application/octet-stream",
            "Content-Disposition": "attachment; filename=savedata.bin"
        }

    return {"message": API_ERROR_MESSAGE_NO_KNOWN_ACTION_PROVIDED}, 400
