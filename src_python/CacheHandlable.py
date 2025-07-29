from src_python.ChaseHoundBase import ChaseHoundBase
import os
import json
from datetime import datetime
import pandas as pd
import pickle
from typing import Optional

class CacheHandlable(ChaseHoundBase):
    def __init__(self):
        super().__init__()
        self.__cache_folder_path = os.path.join(self.project_root, "cache")
        if not os.path.exists(self.__cache_folder_path):
            os.makedirs(self.__cache_folder_path)

        self.class_cache_folder_path = os.path.join(self.__cache_folder_path, self.__class__.__name__)
        if not os.path.exists(self.class_cache_folder_path):
            os.makedirs(self.class_cache_folder_path)

    def _readFromCache(self, cache_key: str):
        cache_file_path = self._getCacheFilePath(cache_key)
        with open(cache_file_path, 'r', encoding='utf-8') as file:
            if cache_key.endswith(".json"):
                return json.load(file)
            elif cache_key.endswith(".csv"):
                return pd.read_csv(file)
            elif cache_key.endswith(".pkl"):
                return pickle.load(file)
            else:
                self.logger.error(f"Unsupported cache file type: {cache_key}")
                return None

    def _saveToCache(self, cache_key: str, cache_data):
        if os.path.exists(self._getCacheFilePath(cache_key)):
            os.remove(self._getCacheFilePath(cache_key))

        if cache_key.endswith(".csv"):
            cache_data.to_csv(self._getCacheFilePath(cache_key), index=False)
        elif cache_key.endswith(".json"):
            with open(self._getCacheFilePath(cache_key), 'w', encoding='utf-8') as file:
                json.dump(cache_data, file)
        elif cache_key.endswith(".pkl"):
            with open(self._getCacheFilePath(cache_key), 'wb') as file:
                pickle.dump(cache_data, file)
        else:
            self.logger.error(f"Unsupported cache file type: {cache_key}")


    def _getCacheFilePath(self, cache_key: str) -> str:
        return os.path.join(self.class_cache_folder_path, cache_key)


    def _doesCacheExist(self, cache_key: str) -> bool:
        """
        Check if a cache file exists for the given cache key.
        
        Args:
            cache_key (str): The unique identifier for the cache entry
            
        Returns:
            bool: True if cache exists, False otherwise
        """
        try:
            cache_file_path = self._getCacheFilePath(cache_key)
            return os.path.exists(cache_file_path)
        except Exception as e:
            self.log_error_with_stack(f"Error checking cache existence for key '{cache_key}'", e)
            return False

    def _getSavedTimeFromCacheName(self, cache_key: str) -> Optional[datetime]:
        for element in cache_key.split(".")[0].split("_"):
            if "at" in element:
                return datetime.strptime(element.split("at")[1], "%Y%m%d%H%M%S")
        self.log_warning(f"No saved time found in cache key: {cache_key}")
        return None

    def _isOlderThan(self, cache_key1: str, cache_key2: str) -> bool:
        return self._getSavedTimeFromCacheName(cache_key1) < self._getSavedTimeFromCacheName(cache_key2)
    
    # MARK: - Private Methods
