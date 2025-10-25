import os
import uvicorn
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, Iterator,Tuple
from fastapi.responses import StreamingResponse

import json
from .storage_manager import (
    StorageManager, 
    CollectionExistsError, 
    CollectionNotFoundError, 
    StorageError
)
DATA_PATH = os.environ.get("BLOOMKV_DATA_PATH", os.path.join(os.getcwd(), "bloomkv_server_data"))
SERVER_PORT = int(os.environ.get("BLOOMKV_SERVER_PORT", 8000))

SERVER_MANAGER = StorageManager(base_data_path=DATA_PATH)
app = FastAPI(title="BloomKV Server", version="1.1.1")

# --- Pydantic Schemas for Request Bodies ---
# These structures help validate incoming client data

class CreateCollectionRequest(BaseModel):
    name: str
    engine_type: str = "lsmtree"
    description: str = ""
    options: Optional[dict] = {}

class UseCollectionRequest(BaseModel):
    name: str

class KeyValueRequest(BaseModel):
    key: str
    value: str

class KeyRequest(BaseModel):
    key: str

@app.on_event("shutdown")
def shutdown_event():
    """Ensures graceful closure of the Storage Manager on server shutdown."""
    print("Shutting down server: Closing all collections...")
    SERVER_MANAGER.close_all()
    print("Shutdown complete.")


def run_server():
    """Entry point for the 'bloomkv-server' command."""
    print(f"LSM Server starting. Data path: {DATA_PATH}")
    # The database will load existing collections on-demand via USE
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)

# --- Helper Functions ---

def get_active_store():
    """Retrieves the active store instance or raises an HTTP error."""
    if not SERVER_MANAGER.active_collection_name:
        raise HTTPException(status_code=400, detail="No active collection selected. Use /collection/use first.")
    active_store = SERVER_MANAGER.get_active_collection()
    if active_store is None:
        raise HTTPException(status_code=500, detail="Active collection is named but not loaded.")
    return active_store

def iterator_to_json_stream(iterator: Iterator[Tuple[str, str]]):
    """
    Takes a Python iterator and yields JSON strings suitable for streaming.
    The format is [ {key: v, value: v}, {key: v, value: v}, ... ]
    """
    yield '[' # Start JSON Array
    first_item = True
    for key, value in iterator:
        if not first_item:
            yield ',' # Separator for subsequent items
        
        # NOTE: Keys and values must be JSON-encoded here.
        yield json.dumps({"key": key, "value": value})
        first_item = False
    
    yield ']'

# --- Collection Management Endpoints ---

@app.post("/collection/create", tags=["Collection Management"])
def create_collection(data: CreateCollectionRequest):
    """Creates a new collection on disk and loads it."""
    try:
        SERVER_MANAGER.create_collection(
            name=data.name,
            engine_type=data.engine_type,
            options=data.options,
            description=data.description
        )
        return {"status": "OK", "message": f"Collection '{data.name}' created successfully."}
    except CollectionExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except (ValueError, NotImplementedError, StorageError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/collection/use", tags=["Collection Management"])
def use_collection(data: UseCollectionRequest):
    """Sets an existing or newly loaded collection as active."""
    try:
        SERVER_MANAGER.use_collection(data.name)
        return {"status": "OK", "active_collection": data.name}
    except CollectionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/collection/close", tags=["Collection Management"])
def close_collection(data: UseCollectionRequest):
    """Closes and unloads a collection from memory."""
    try:
        SERVER_MANAGER.close_collection(data.name)
        return {"status": "OK", "message": f"Collection '{data.name}' closed."}
    except CollectionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collection/list", tags=["Collection Management"])
def list_collections():
    """Lists all available collections found on disk."""
    collections = SERVER_MANAGER.list_collections_on_disk()
    return {"status": "OK", "collections": collections}

@app.get("/collection/active", tags=["Collection Management"])
def get_active_collection():
    """Returns the name of the currently active collection."""
    if not SERVER_MANAGER.active_collection_name:
        return {"status": "OK", "active_collection": None}
    return {"status": "OK", "active_collection": SERVER_MANAGER.active_collection_name}

@app.get("/collection/meta", tags=["Collection Management"])
def get_collection_metadata():
    """Returns the metadata for the active collection."""
    try:
        active_coll_name = SERVER_MANAGER.active_collection_name
        if not active_coll_name:
            raise HTTPException(status_code=400, detail="No active collection selected.")
        
        # NOTE: Using a protected method here for convenience, 
        # but in a production API, this logic should be encapsulated.
        meta_file_path = SERVER_MANAGER._get_meta_file_path(active_coll_name)
        
        # Ensure latest key count is written before reading (optional, but good for real-time meta)
        active_store = SERVER_MANAGER.get_active_collection()
        if active_store:
            active_store.update_metadata()

        with open(meta_file_path, 'r') as f:
            meta_data = json.load(f)
            
        return {"status": "OK", "metadata": meta_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading metadata: {e}")

# --- Key-Value Operations Endpoints (Requires Active Collection) ---

@app.post("/kv/put", tags=["Key-Value Operations"])
def put_kv(data: KeyValueRequest):
    """Stores a key-value pair in the active collection."""
    active_store = get_active_store()
    try:
        active_store.put(data.key, data.value)
        return {"status": "OK"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PUT failed: {str(e)}")

@app.get("/kv/get/{key:path}", tags=["Key-Value Operations"])
def get_kv(key: str):
    """Retrieves the value for a given key from the active collection."""
    active_store = get_active_store()
    try:
        value = active_store.get(key)
        if value is not None:
            return {"status": "OK", "key": key, "value": value}
        else:
            return {"status": "NOT_FOUND", "key": key, "value": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GET failed: {str(e)}")

@app.get("/kv/range", tags=["Key-Value Operations"])
def range_query_kv(start_key: str, end_key: str):
    """
    Retrieves a range of key-value pairs using a heap merge iterator.
    The response is streamed to prevent memory exhaustion for large ranges.
    """
    active_store = get_active_store()
    
    try:
        # returns an iterator over the store which contains all the found keys
        range_iterator = active_store.range_query(start_key, end_key)
        
        # Use StreamingResponse to send the iterator output back to the client immediately
        return StreamingResponse(
            iterator_to_json_stream(range_iterator),
            media_type="application/json"
        )
    except Exception as e:
        # Note: If the error occurs after streaming starts, the client might receive 
        # a partially complete JSON array. The CLI will need to handle this robustly.
        raise HTTPException(status_code=500, detail=f"RANGE query failed: {str(e)}")


@app.post("/kv/delete", tags=["Key-Value Operations"])
def delete_kv(data: KeyRequest):
    """Deletes a key-value pair (inserts a tombstone) in the active collection."""
    active_store = get_active_store()
    try:
        active_store.delete(data.key)
        return {"status": "OK"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DELETE failed: {str(e)}")

@app.get("/kv/exists/{key:path}", tags=["Key-Value Operations"])
def exists_kv(key: str):
    """Checks if a key exists in the active collection."""
    active_store = get_active_store()
    try:
        result = active_store.exists(key)
        return {"status": "OK", "exists": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"EXISTS failed: {str(e)}")


@app.get("/internal/levels", tags=["Internal (Testing)"])
def get_levels_status():
    """
    Returns the current SSTable level status for the active collection. 
    Used by test_async.py to monitor compaction progress.
    """
    try:
        active_store = get_active_store()
        # Ensure the active store is an LSMTreeStore to access its internal properties
        if hasattr(active_store, 'levels'):
            # Return a list of lists representing the levels structure
            return {"status": "OK", "levels": active_store.levels}
        else:
            raise HTTPException(status_code=400, detail="Active collection is not an LSMTreeStore.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking levels: {str(e)}")
