from esp32 import NVS # type: ignore

class NVSManager:
    def __init__(self, namespace="storage"):
        """Initialize NVS with the given namespace."""
        self.nvs = NVS(namespace)
    
    def set_string(self, key, value):
        """Store a string value in NVS."""
        try:
            # Convert string to bytes and store as blob
            self.nvs.set_blob(key, value.encode('utf-8'))
            self.nvs.commit()
            return True
        except OSError as e:
            print(f"Error setting string: {e}")
            return False
    
    def get_string(self, key, default=None):
        """
        Retrieve a string value from NVS.
        Returns default value if key doesn't exist.
        """
        try:
            # Create a buffer to read the blob
            # First try with small buffer
            buffer = bytearray(256)
            length = self.nvs.get_blob(key, buffer)
            # Return only the valid bytes, decoded as string
            return buffer[:length].decode('utf-8')
        except OSError:
            return default
    
    def set_int(self, key, value):
        """Store an integer value in NVS."""
        try:
            self.nvs.set_i32(key, value)
            self.nvs.commit()
            return True
        except OSError as e:
            print(f"Error setting integer: {e}")
            return False
    
    def get_int(self, key, default=None):
        """
        Retrieve an integer value from NVS.
        Returns default value if key doesn't exist.
        """
        try:
            return self.nvs.get_i32(key)
        except OSError:
            return default
    
    def delete(self, key):
        """Delete a key-value pair from NVS."""
        try:
            self.nvs.erase_key(key)
            self.nvs.commit()
            return True
        except OSError as e:
            print(f"Error deleting key: {e}")
            return False 