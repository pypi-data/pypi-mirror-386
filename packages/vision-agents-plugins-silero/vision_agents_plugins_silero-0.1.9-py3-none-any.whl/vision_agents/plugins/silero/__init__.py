from .vad import VAD

# Re-export under the new namespace for convenience
__path__ = __import__("pkgutil").extend_path(__path__, __name__)

__all__ = ["VAD"]
