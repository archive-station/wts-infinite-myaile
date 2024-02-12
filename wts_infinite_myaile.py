from flask import Flask, request, send_file
from io import BytesIO
import os

SAVEDATA_HEADER = b"BX30"
SAVEDATA_MYAILE_COUNT_POSITION = 0x286b

GET_MYAILE_COUNT_ACTION = "wts_infinite_myaile.api_endpoint.get_myaile_count"
UPDATE_MYAILE_COUNT_ACTION = "wts_infinite_myaile.api_endpoint.update_myaile_count"

MAXIMUM_MYAILE_COUNT = 32767

app = Flask(__name__, static_url_path=None)


# TODO(mikhail): do the nice looking frontend
@app.get("/wts-infinite-myaile/")
def index_page():
    return send_file("index.html")


# TODO(mikhail): figure out the savedata structure
@app.post("/wts-infinite-myaile/")
def api_endpoint():
    savedata = request.files.get("savedata")

    if savedata is None:
        return {"message": "no savedata provided"}, 400

    if savedata.read(4) != SAVEDATA_HEADER:
        return {"message": "invalid savedata provided"}, 400

    action = request.form.get("action")

    if action == GET_MYAILE_COUNT_ACTION:
        savedata.seek(SAVEDATA_MYAILE_COUNT_POSITION, os.SEEK_SET)
        myaile_count = int.from_bytes(savedata.read(2), "big", signed=True)

        return {"myaile_count": myaile_count}

    if action == UPDATE_MYAILE_COUNT_ACTION:
        savedata.seek(0, os.SEEK_SET)
        updated_savedata = BytesIO()

        updated_savedata.write(savedata.read(SAVEDATA_MYAILE_COUNT_POSITION))
        updated_savedata.write(MAXIMUM_MYAILE_COUNT.to_bytes(2, "big", signed=True))

        savedata.seek(2, os.SEEK_CUR)
        updated_savedata.write(savedata.read())

        return updated_savedata.getvalue(), 200, {
            "Content-Type": "application/octet-stream",
            "Content-Disposition": "attachment; filename=savedata.bin"
        }

    return {"message": "no known action provided"}, 400
