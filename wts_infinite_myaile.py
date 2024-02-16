from flask import Flask, request, send_file
from flask_cors import CORS, cross_origin
from io import BytesIO
import os

SAVEDATA_HEADER = b"BX30"

SAVEDATA_MYAILE_COUNT_ENTRY_1 = 0x2871
SAVEDATA_MYAILE_COUNT_ENTRY_2 = 0x2869

SAVEDATA_MYAILE_COUNT_POSITION_1 = 0x2873
SAVEDATA_MYAILE_COUNT_POSITION_2 = 0x286B

GET_MYAILE_COUNT_ACTION = "wts_infinite_myaile.api_endpoint.get_myaile_count"
UPDATE_MYAILE_COUNT_ACTION = "wts_infinite_myaile.api_endpoint.update_myaile_count"

MAXIMUM_MYAILE_COUNT = 32767

app = Flask(__name__, static_url_path=None)
cors = CORS(app)


# TODO(mikhail): do the nice looking frontend
@app.get("/wts-infinite-myaile/")
def index_page():
    return send_file("index.html")


# TODO(mikhail): figure out the savedata structure
@app.post("/wts-infinite-myaile/")
@cross_origin()
def api_endpoint():
    savedata = request.files.get("savedata")

    if savedata is None:
        return {"message": "no savedata provided"}, 400

    if savedata.read(4) != SAVEDATA_HEADER:
        return {"message": "invalid savedata provided"}, 400

    action = request.form.get("action")

    if action == GET_MYAILE_COUNT_ACTION:
        savedata.seek(SAVEDATA_MYAILE_COUNT_ENTRY_1, os.SEEK_SET)
        byte = savedata.read(1)
        if byte == b' ':
            savedata.seek(SAVEDATA_MYAILE_COUNT_POSITION_1, os.SEEK_SET)
        else:
            savedata.seek(SAVEDATA_MYAILE_COUNT_ENTRY_2, os.SEEK_SET)
            byte = savedata.read(1)
            if byte == b' ':
                savedata.seek(SAVEDATA_MYAILE_COUNT_POSITION_2, os.SEEK_SET)
            else:
                return {"message": "invalid savedata provided"}, 400
        
        myaile_count = int.from_bytes(savedata.read(2), "big", signed=True)

        return {"myaile_count": myaile_count}

    if action == UPDATE_MYAILE_COUNT_ACTION:
        actual_pos = 0
    
        savedata.seek(SAVEDATA_MYAILE_COUNT_ENTRY_1, os.SEEK_SET)
        byte = savedata.read(1)
        if byte == b' ':
            actual_pos = SAVEDATA_MYAILE_COUNT_POSITION_1
        else:
            savedata.seek(SAVEDATA_MYAILE_COUNT_ENTRY_2, os.SEEK_SET)
            byte = savedata.read(1)
            if byte == b' ':
                actual_pos = SAVEDATA_MYAILE_COUNT_POSITION_2
            else:
                return {"message": "invalid savedata provided"}, 400
        
        
        savedata.seek(0, os.SEEK_SET)
        updated_savedata = BytesIO()

        updated_savedata.write(savedata.read(actual_pos))
        updated_savedata.write(MAXIMUM_MYAILE_COUNT.to_bytes(2, "big", signed=True))

        savedata.seek(2, os.SEEK_CUR)
        updated_savedata.write(savedata.read())

        return updated_savedata.getvalue(), 200, {
            "Content-Type": "application/octet-stream",
            "Content-Disposition": "attachment; filename=savedata.bin"
        }

    return {"message": "no known action provided"}, 400
