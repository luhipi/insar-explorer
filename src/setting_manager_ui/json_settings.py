__version__ = '0.4.1'

try:
    import json5 as json
except ImportError:
    import json


class JsonSettings:
    """
    Class to handle the settings JSON file.

    :param filename: The name of the JSON file.
    :type filename: str
    :param block_key: The key for a specific block of settings, defaults to None.
    :type block_key: str, optional
    """
    def __init__(self, filename, block_key=None):
        self.filename = filename
        self.block_key = block_key
        self.data = {}
        self.block = {}
        self.load()

    def load(self, block_key=None):
        """
        Load the settings from the JSON file.

        :param block_key: The key for a specific block of settings, defaults to None.
        :type block_key: str, optional
        :return: The loaded settings data.
        :rtype: dict
        """

        # TODO: allow a list to get a nested block
        with open(self.filename, 'r') as f:
            full_data = json.load(f)

        self.data = full_data

        if block_key is None:
            block_key = self.block_key

        if block_key is None:
            return self.data

        self.block_key = block_key

        if block_key not in full_data:
            full_data[block_key] = {}

        block_data = full_data[block_key]
        self.block = block_data
        return block_data

    def save(self, block_key, new_data):
        """
        Save data to the JSON file.

        :param block_key: The key for a specific block of settings.
        :type block_key: str
        :param new_data: The new data to be saved.
        :type new_data: dict
        """
        self.data[block_key] = new_data
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)

    def get(self, key: list):
        """
        Get the value of a key.

        :param key: The list of keys to access the nested value.
        :type key: list
        :return: The value of the key, or the default value if the auto flag is set.
        :rtype: any
        """
        data = self.block
        for k in key:
            data = data.get(k, None)
            if data is None:
                return None
        default = data.get("default", None)
        auto_flag = data.get("auto", False)
        if auto_flag:
            return None
        return data.get("value", default)

    def getDefault(self, key: list):
        """
        Get the default value of a key.

        :param key: The list of keys to access the nested default value.
        :type key: list
        :return: The default value of the key.
        :rtype: any
        """
        data = self.block
        for k in key:
            data = data.get(k, None)
            if data is None:
                return None
        return data.get("default", None)

