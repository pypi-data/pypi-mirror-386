__path__ = __import__("pkgutil").extend_path(__path__, __name__)  # type: ignore

default_app_config = "karrio.server.events.apps.EventsConfig"
