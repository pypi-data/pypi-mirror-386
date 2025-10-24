"""
Write Ahead Log (WAL) implementation. 
This is a log stored in disk, records all the operations to the database, for persistance.
It is used to recover the database in case of a crash or failure.
It is a simple append-only log, where each line is a JSON object representing an operation.
"""

import os
import json

TOMBSTONE = "__TOMBSTONE__"

class WriteAheadLog:
    def __init__(self, wal_path: str):
        self.wal_path = wal_path
        self._file = None
        
        # Open in append mode, create if not exists.
        # The file handle has to be open.
        try:
            self._file = open(self.wal_path, 'a', encoding='utf-8')
        except IOError as e:
            raise IOError("Error opening the Write Ahead Log")

    def log_operation(self, operation_type: str, key: str, value=None) -> bool:
        """
        Logs an operation to the WAL.
        operation_type: "PUT" or "DELETE"
        value: The value for "PUT", ignored for "DELETE".
        """
        log_entry = {"op": operation_type, "key": key}
        if operation_type == "PUT":
            log_entry["value"] = value
        elif operation_type != "DELETE":
            raise ValueError(f"Unknown operation type '{operation_type}' for WAL.")
       
        try:
            json_entry = json.dumps(log_entry)
            self._file.write(json_entry + '\n')
            self._file.flush()  # Ensure it's written to disk immediately for persistence
        except (IOError, TypeError) as e:
            raise IOError(f"Error writing to WAL {self.wal_path}: {e}")

    def replay(self) -> list[dict]:
        """
        Reads all entries from the WAL and returns them as a list of dicts.
        This is used to reconstruct the memtable on startup.
        """
        entries = []
        if not os.path.exists(self.wal_path):
            return entries

        # Close the current append-mode file handle before reopening in read mode
        current_pos = 0
        if self._file and not self._file.closed:
            current_pos = self._file.tell() # Save position if needed, though replay usually means full read
            self._file.close() # Close append mode file

        try:
            with open(self.wal_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            entries.append(entry)
                        except json.JSONDecodeError as e:
                            continue
        except IOError as e:
            raise IOError(f"Error reading WAL file {self.wal_path} during replay: {e}")
        finally:
            self._reopen_for_append()
                
        return entries

    def _reopen_for_append(self):
        # Reopen in append mode
            try:
                self._file = open(self.wal_path, 'a', encoding='utf-8')
            except IOError as e:
                raise IOError(f"Critical Error: Failed to reopen WAL {self.wal_path} for appending: {e}")
            
    def truncate(self):
        """
        Clears the WAL file. Called after a memtable flush to SSTable is successful.
        """
        if self._file and not self._file.closed:
            self._file.close()
        try:
            # Open in write mode to truncate, then immediately reopen in append mode
            with open(self.wal_path, 'w', encoding='utf-8') as f:
                pass # Opening in 'w' mode truncates the file
            self._reopen_for_append()
        except IOError as e:
            raise IOError(f"Error truncating WAL file {self.wal_path}: {e}")


    def close(self):
        if self._file and not self._file.closed:
            try:
                self._file.flush() # Final flush
                self._file.close()
                
            except IOError as e:
                raise IOError(f"Error closing WAL file {self.wal_path}: {e}")
        self._file = None

    def __del__(self):
        if self._file and not self._file.closed:
            self.close()