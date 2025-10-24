"""in_memory_cache module: In-memory cache implementation for Plotmon."""

from quantify.visualization.plotmon.caching.base_cache import BaseCache


class InMemoryCache(BaseCache):
    """Thread-safe in memory cache implementation."""

    def __init__(self) -> None:
        """Initializes the in-memory cache and its lock."""
        if not hasattr(self, "_cache"):
            self._cache = {}

    def set(self, cache_id: str, data: dict) -> None:
        """
        Set a cache entry by its ID.

        Parameters
        ----------
        cache_id : str
            The ID of the cache entry to set.
        data : Any
            The data to be cached.

        """
        self._cache[cache_id] = data

    def get(self, cache_id: str) -> dict | None:
        """
        Retrieve a cache entry by its ID.

        Parameters
        ----------
        cache_id : str
            The ID of the cache entry to retrieve.

        Returns
        -------
        Any | None
            The cache entry if found, otherwise None.

        """
        return self._cache.get(cache_id, None)

    def get_all(self, prefix: str = "", suffix: str = "") -> dict[str, dict]:
        """
        Retrieve all cache entries that match the given prefix and suffix.

        Parameters
        ----------
        prefix : str
            The prefix that the cache IDs should start with.
        suffix : str
            The suffix that the cache IDs should end with.

        Returns
        -------
        dict[str, Any]
            A dictionary of cache entries that match the criteria.

        """
        return {
            key: value
            for key, value in self._cache.items()
            if key.startswith(prefix) and key.endswith(suffix)
        }

    def clear(self) -> None:
        """Clear all data from the cache."""
        self._cache.clear()
