from core.engine_manager import EngineManager


manager = EngineManager()

print("Collaboration:", manager.get_engine_path("collaboration"))
print("Coordination:", manager.get_engine_path("coordination"))