"""
🏗️ DEPENDENCY INJECTION CONTAINER - IoC Container Pattern
Contenedor centralizado para gestionar dependencias y sus ciclos de vida
"""

import logging
from typing import Dict, Type, Any, Optional, Callable
from services.auto_discovery import AutoDiscoveryEngine
from services.interfaces.discovery_interface import DiscoveryEngineInterface
from services.industrial_factory import IndustrialFactory

logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    🔌 CONTENEDOR DE INYECCIÓN DE DEPENDENCIAS
    
    Implementa el patrón IoC (Inversion of Control) Container para:
    - Registro de dependencias con interfaces
    - Resolución automática de dependencias 
    - Gestión de ciclos de vida (singleton, transient)
    - Configuración centralizada
    
    Ejemplo de uso:
    ```python
    # Registro
    container = DependencyContainer()
    container.register_singleton(DiscoveryEngineInterface, AutoDiscoveryEngine)
    
    # Resolución
    factory = container.resolve(IndustrialFactory)  # Auto-inyecta dependencias
    ```
    """
    
    def __init__(self):
        """Inicializa el container con configuración por defecto"""
        logger.info("🔌 Dependency Container inicializado")
        
        # Registro de dependencias: Interface -> Implementation
        self._registrations: Dict[Type, Dict[str, Any]] = {}
        
        # Cache de instancias singleton
        self._singletons: Dict[Type, Any] = {}
        
        # Configurar dependencias por defecto del sistema
        self._register_default_dependencies()
    
    def _register_default_dependencies(self):
        """
        Registra las dependencias por defecto del sistema
        Configuración centralizada siguiendo principios SOLID
        """
        logger.info("📦 Registrando dependencias por defecto del sistema...")
        
        # Discovery Engine como Singleton - una sola instancia para toda la app
        self.register_singleton(
            interface=DiscoveryEngineInterface,
            implementation=AutoDiscoveryEngine,
            description="Auto-discovery de scrapers desde filesystem"
        )
        
        # Industrial Factory como Transient - nueva instancia en cada uso
        self.register_transient(
            interface=IndustrialFactory,
            implementation=IndustrialFactory,
            description="Factory para ejecución paralela de scrapers"
        )
        
        logger.info("✅ Dependencias por defecto registradas correctamente")
    
    def register_singleton(self, interface: Type, implementation: Type, description: str = ""):
        """
        Registra una dependencia como Singleton
        Una sola instancia durante toda la vida de la aplicación
        """
        self._registrations[interface] = {
            'implementation': implementation,
            'lifecycle': 'singleton',
            'description': description
        }
        logger.info(f"🔗 Singleton registrado: {interface.__name__} -> {implementation.__name__}")
    
    def register_transient(self, interface: Type, implementation: Type, description: str = ""):
        """
        Registra una dependencia como Transient
        Nueva instancia en cada resolución
        """
        self._registrations[interface] = {
            'implementation': implementation,
            'lifecycle': 'transient', 
            'description': description
        }
        logger.info(f"🔄 Transient registrado: {interface.__name__} -> {implementation.__name__}")
    
    def register_factory(self, interface: Type, factory: Callable, description: str = ""):
        """
        Registra una dependencia usando Factory Method
        Control total sobre la creación de instancias
        """
        self._registrations[interface] = {
            'factory': factory,
            'lifecycle': 'factory',
            'description': description
        }
        logger.info(f"🏭 Factory registrado: {interface.__name__}")
    
    def resolve(self, interface: Type) -> Any:
        """
        Resuelve una dependencia registrada con inyección automática
        
        Args:
            interface: Tipo/Interface a resolver
            
        Returns:
            Instancia del tipo solicitado con dependencias inyectadas
        """
        if interface not in self._registrations:
            # Intentar resolución directa si no está registrado
            logger.warning(f"⚠️ {interface.__name__} no registrado, intentando resolución directa...")
            return self._resolve_direct(interface)
        
        registration = self._registrations[interface]
        lifecycle = registration.get('lifecycle')
        
        if lifecycle == 'singleton':
            return self._resolve_singleton(interface, registration)
        elif lifecycle == 'transient':
            return self._resolve_transient(interface, registration)
        elif lifecycle == 'factory':
            return self._resolve_factory(interface, registration)
        else:
            raise ValueError(f"Lifecycle no soportado: {lifecycle}")
    
    def _resolve_singleton(self, interface: Type, registration: Dict) -> Any:
        """Resuelve dependencia Singleton con cache"""
        if interface in self._singletons:
            logger.debug(f"🔍 Singleton cache hit: {interface.__name__}")
            return self._singletons[interface]
        
        implementation = registration['implementation']
        logger.info(f"🔌 Creando singleton: {implementation.__name__}")
        
        # Crear instancia con inyección de dependencias
        instance = self._create_instance_with_injection(implementation)
        
        # Cache para futuras resoluciones
        self._singletons[interface] = instance
        return instance
    
    def _resolve_transient(self, interface: Type, registration: Dict) -> Any:
        """Resuelve dependencia Transient - nueva instancia cada vez"""
        implementation = registration['implementation']
        logger.debug(f"🔄 Creando transient: {implementation.__name__}")
        
        # Crear nueva instancia con inyección de dependencias
        return self._create_instance_with_injection(implementation)
    
    def _resolve_factory(self, interface: Type, registration: Dict) -> Any:
        """Resuelve dependencia usando Factory Method"""
        factory = registration['factory']
        logger.debug(f"🏭 Ejecutando factory para: {interface.__name__}")
        
        return factory(self)  # Pasar container a factory para resolver dependencias
    
    def _resolve_direct(self, interface: Type) -> Any:
        """
        Resolución directa para tipos no registrados
        Fallback de compatibilidad con código existente
        """
        logger.info(f"📦 Resolución directa: {interface.__name__}")
        return self._create_instance_with_injection(interface)
    
    def _create_instance_with_injection(self, implementation: Type) -> Any:
        """
        Crea instancia con inyección automática de dependencias del constructor
        Analiza signature del constructor y resuelve dependencias recursivamente
        """
        try:
            import inspect
            
            # Obtener signature del constructor
            signature = inspect.signature(implementation.__init__)
            parameters = signature.parameters
            
            # Resolver dependencias del constructor (excluyendo 'self')
            kwargs = {}
            for param_name, param in parameters.items():
                if param_name == 'self':
                    continue
                    
                # Si tiene type annotation, intentar resolverla
                if param.annotation != inspect.Parameter.empty:
                    try:
                        kwargs[param_name] = self.resolve(param.annotation)
                        logger.debug(f"🔗 Dependencia inyectada: {param_name} = {param.annotation.__name__}")
                    except Exception as e:
                        # Si no se puede resolver, usar valor por defecto si existe
                        if param.default != inspect.Parameter.empty:
                            logger.debug(f"⚠️ Usando valor por defecto para {param_name}: {param.default}")
                        else:
                            logger.warning(f"❌ No se pudo resolver {param_name}: {e}")
            
            # Crear instancia con dependencias inyectadas
            instance = implementation(**kwargs)
            logger.debug(f"✅ Instancia creada con DI: {implementation.__name__}")
            return instance
            
        except Exception as e:
            # Fallback: crear instancia sin parámetros
            logger.warning(f"⚠️ DI falló, creando instancia simple: {e}")
            return implementation()
    
    def get_registrations(self) -> Dict[str, Dict]:
        """
        Obtiene información de todas las dependencias registradas
        Útil para debugging y documentación
        """
        info = {}
        for interface, registration in self._registrations.items():
            implementation = registration.get('implementation')
            impl_name = implementation.__name__ if implementation else 'Factory'
            
            info[interface.__name__] = {
                'implementation': impl_name,
                'lifecycle': registration.get('lifecycle'),
                'description': registration.get('description', ''),
                'is_singleton_cached': interface in self._singletons
            }
        return info


# 🔌 INSTANCIA GLOBAL DEL CONTAINER
# Singleton pattern para el container mismo
_global_container: Optional[DependencyContainer] = None

def get_container() -> DependencyContainer:
    """
    Obtiene la instancia global del container
    Singleton Pattern para el DI Container
    """
    global _global_container
    if _global_container is None:
        _global_container = DependencyContainer()
        logger.info("🌍 DI Container global inicializado")
    return _global_container


def inject_dependencies(cls: Type) -> Type:
    """
    🔌 DECORADOR PARA INYECCIÓN AUTOMÁTICA
    
    Decorator que permite inyección automática de dependencias
    
    Ejemplo:
    ```python
    @inject_dependencies
    class MyService:
        def __init__(self, discovery: DiscoveryEngineInterface):
            self.discovery = discovery
    ```
    """
    original_init = cls.__init__
    
    def new_init(self, *args, **kwargs):
        if not args and not kwargs:  # Solo si no se pasan argumentos
            container = get_container()
            instance = container._create_instance_with_injection(cls)
            # Copiar atributos de la instancia creada con DI
            for attr_name in dir(instance):
                if not attr_name.startswith('_'):
                    setattr(self, attr_name, getattr(instance, attr_name))
        else:
            original_init(self, *args, **kwargs)
    
    cls.__init__ = new_init
    return cls