#!/usr/bin/env python3
"""
Migration Helper for FlowProcessor Refactoring

This script provides utilities to safely migrate and refactor the FlowProcessor project.
"""

import os
import shutil
import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class MigrationHelper:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.flowproc_dir = self.project_root / "flowproc"
        self.backup_dir = self.project_root / "backup_before_refactoring"
        
    def create_backup(self):
        """Create a backup of the current codebase."""
        print("🔄 Creating backup...")
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        shutil.copytree(self.flowproc_dir, self.backup_dir / "flowproc")
        print(f"✅ Backup created at: {self.backup_dir}")
    
    def find_imports(self, file_path: Path) -> Set[str]:
        """Find all imports in a Python file."""
        imports = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
                        
        except Exception as e:
            print(f"⚠️  Error parsing {file_path}: {e}")
            
        return imports
    
    def find_files_importing(self, target_module: str) -> List[Path]:
        """Find all files that import a specific module."""
        importing_files = []
        
        for py_file in self.flowproc_dir.rglob("*.py"):
            imports = self.find_imports(py_file)
            if target_module in imports:
                importing_files.append(py_file)
        
        return importing_files
    
    def update_imports(self, file_path: Path, old_import: str, new_import: str):
        """Update imports in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple string replacement (could be enhanced with AST)
            updated_content = content.replace(old_import, new_import)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
                
            print(f"✅ Updated imports in {file_path}")
            
        except Exception as e:
            print(f"❌ Error updating {file_path}: {e}")
    
    def consolidate_visualization_services(self):
        """Consolidate visualization services into a unified structure."""
        print("🎨 Consolidating visualization services...")
        
        # Create new directory structure
        viz_dir = self.flowproc_dir / "domain" / "visualization"
        renderers_dir = viz_dir / "renderers"
        processors_dir = viz_dir / "processors"
        
        renderers_dir.mkdir(exist_ok=True)
        processors_dir.mkdir(exist_ok=True)
        
        # Create base renderer
        base_renderer_content = '''"""
Base renderer for visualization components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseRenderer(ABC):
    """Base class for all renderers."""
    
    @abstractmethod
    def render(self, data: Any, config: Dict[str, Any]) -> Any:
        """Render the data according to the configuration."""
        pass
    
    @abstractmethod
    def supports_format(self, format_type: str) -> bool:
        """Check if this renderer supports the given format."""
        pass
'''
        
        with open(renderers_dir / "__init__.py", 'w') as f:
            f.write('"""Renderer implementations."""\n')
        
        with open(renderers_dir / "base_renderer.py", 'w') as f:
            f.write(base_renderer_content)
        
        # Move existing renderers
        existing_renderers = [
            "plotly_renderer.py",
            "simple_visualizer.py"
        ]
        
        for renderer in existing_renderers:
            src = viz_dir / renderer
            if src.exists():
                dst = renderers_dir / renderer
                shutil.move(str(src), str(dst))
                print(f"✅ Moved {renderer} to renderers/")
        
        # Create unified service
        unified_service_content = '''"""
Unified visualization service.
"""

from typing import Dict, Any, List
from flowproc.domain.visualization.renderers.base_renderer import BaseRenderer

class VisualizationService:
    """Unified service for all visualization needs."""
    
    def __init__(self, renderers: List[BaseRenderer]):
        self.renderers = renderers
    
    def render(self, data: Any, config: Dict[str, Any]) -> Any:
        """Render data using the appropriate renderer."""
        format_type = config.get('format', 'plotly')
        
        for renderer in self.renderers:
            if renderer.supports_format(format_type):
                return renderer.render(data, config)
        
        raise ValueError(f"No renderer found for format: {format_type}")
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported formats."""
        formats = []
        for renderer in self.renderers:
            # This would need to be implemented in each renderer
            pass
        return formats
'''
        
        with open(viz_dir / "service.py", 'w') as f:
            f.write(unified_service_content)
        
        print("✅ Visualization services consolidated")
    
    def consolidate_parsing_services(self):
        """Consolidate parsing services into a unified structure."""
        print("📝 Consolidating parsing services...")
        
        # Create new directory structure
        parsing_dir = self.flowproc_dir / "domain" / "parsing"
        parsers_dir = parsing_dir / "parsers"
        validators_dir = parsing_dir / "validators"
        
        parsers_dir.mkdir(exist_ok=True)
        validators_dir.mkdir(exist_ok=True)
        
        # Create base parser
        base_parser_content = '''"""
Base parser for data parsing components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseParser(ABC):
    """Base class for all parsers."""
    
    @abstractmethod
    def parse(self, data: Any) -> Any:
        """Parse the data."""
        pass
    
    @abstractmethod
    def can_parse(self, data: Any) -> bool:
        """Check if this parser can handle the given data."""
        pass
'''
        
        with open(parsers_dir / "__init__.py", 'w') as f:
            f.write('"""Parser implementations."""\n')
        
        with open(parsers_dir / "base_parser.py", 'w') as f:
            f.write(base_parser_content)
        
        # Move existing parsers
        existing_parsers = [
            "tissue_parser.py",
            "well_parser.py",
            "sample_id_parser.py",
            "group_animal_parser.py",
            "time_parser.py"
        ]
        
        for parser in existing_parsers:
            src = parsing_dir / parser
            if src.exists():
                dst = parsers_dir / parser
                shutil.move(str(src), str(dst))
                print(f"✅ Moved {parser} to parsers/")
        
        # Create base validator
        base_validator_content = '''"""
Base validator for data validation components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseValidator(ABC):
    """Base class for all validators."""
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate the data."""
        pass
    
    @abstractmethod
    def get_errors(self) -> List[str]:
        """Get validation errors."""
        pass
'''
        
        with open(validators_dir / "__init__.py", 'w') as f:
            f.write('"""Validator implementations."""\n')
        
        with open(validators_dir / "base_validator.py", 'w') as f:
            f.write(base_validator_content)
        
        # Move existing validators
        existing_validators = [
            "validators.py",
            "validation_utils.py"
        ]
        
        for validator in existing_validators:
            src = parsing_dir / validator
            if src.exists():
                dst = validators_dir / validator
                shutil.move(str(src), str(dst))
                print(f"✅ Moved {validator} to validators/")
        
        print("✅ Parsing services consolidated")
    
    def create_dependency_injection_container(self):
        """Create a proper dependency injection container."""
        print("🔧 Creating dependency injection container...")
        
        container_content = '''"""
Dependency injection container for FlowProcessor.
"""

from dependency_injector import containers, providers
from flowproc.domain.parsing.service import ParsingService
from flowproc.domain.export.service import ExportService

class Container(containers.DeclarativeContainer):
    """Main dependency injection container."""
    
    # Configuration
    config = providers.Configuration()
    
    # Services
    parsing_service = providers.Singleton(ParsingService)
    export_service = providers.Singleton(ExportService)
    
    # Configure service dependencies
    parsing_service.override(
        validators=providers.List(
            providers.Factory(DataValidator),
            providers.Factory(FormatValidator)
        )
    )

# Global container instance
container = Container()
'''
        
        app_dir = self.flowproc_dir / "application"
        with open(app_dir / "container.py", 'w') as f:
            f.write(container_content)
        
        print("✅ Dependency injection container created")
    
    def create_service_interfaces(self):
        """Create standardized service interfaces."""
        print("🔌 Creating service interfaces...")
        
        interfaces_content = '''"""
Standardized interfaces for FlowProcessor services.
"""

from abc import ABC, abstractmethod
from typing import Protocol, Dict, Any, List

class DataProcessor(Protocol):
    """Protocol for data processors."""
    
    def process(self, data: Any) -> Any:
        """Process the data."""
        ...

class Validator(Protocol):
    """Protocol for validators."""
    
    def validate(self, data: Any) -> bool:
        """Validate the data."""
        ...
    
    def get_errors(self) -> List[str]:
        """Get validation errors."""
        ...

class Renderer(Protocol):
    """Protocol for renderers."""
    
    def render(self, data: Any, config: Dict[str, Any]) -> Any:
        """Render the data."""
        ...
    
    def supports_format(self, format_type: str) -> bool:
        """Check if format is supported."""
        ...

class Service(ABC):
    """Base class for all services."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the service."""
        pass
'''
        
        core_dir = self.flowproc_dir / "core"
        with open(core_dir / "interfaces.py", 'w') as f:
            f.write(interfaces_content)
        
        print("✅ Service interfaces created")
    
    def create_pipeline_pattern(self):
        """Create a unified data processing pipeline."""
        print("🔄 Creating pipeline pattern...")
        
        pipeline_content = '''"""
Unified data processing pipeline.
"""

from typing import List, Any, Dict
from flowproc.core.interfaces import DataProcessor

class ProcessingPipeline:
    """Unified pipeline for data processing."""
    
    def __init__(self, processors: List[DataProcessor]):
        self.processors = processors
    
    def process(self, data: Any) -> Any:
        """Process data through the pipeline."""
        result = data
        for processor in self.processors:
            result = processor.process(result)
        return result
    
    def add_processor(self, processor: DataProcessor) -> None:
        """Add a processor to the pipeline."""
        self.processors.append(processor)
    
    def remove_processor(self, processor: DataProcessor) -> None:
        """Remove a processor from the pipeline."""
        if processor in self.processors:
            self.processors.remove(processor)

class PipelineBuilder:
    """Builder for creating processing pipelines."""
    
    def __init__(self):
        self.processors = []
    
    def add_processor(self, processor: DataProcessor) -> 'PipelineBuilder':
        """Add a processor to the pipeline."""
        self.processors.append(processor)
        return self
    
    def build(self) -> ProcessingPipeline:
        """Build the pipeline."""
        return ProcessingPipeline(self.processors)
'''
        
        processing_dir = self.flowproc_dir / "domain" / "processing"
        with open(processing_dir / "pipeline.py", 'w') as f:
            f.write(pipeline_content)
        
        print("✅ Pipeline pattern created")
    
    def create_event_system(self):
        """Create an event-driven architecture."""
        print("📡 Creating event system...")
        
        event_content = '''"""
Event-driven architecture for FlowProcessor.
"""

from dataclasses import dataclass
from typing import Any, Dict, Callable, List
from enum import Enum

class EventType(Enum):
    """Event types."""
    DATA_LOADED = "data_loaded"
    DATA_PROCESSED = "data_processed"
    VISUALIZATION_CREATED = "visualization_created"
    EXPORT_COMPLETED = "export_completed"
    ERROR_OCCURRED = "error_occurred"

@dataclass
class Event:
    """Event data structure."""
    type: EventType
    data: Dict[str, Any]
    source: str
    timestamp: float = None

class EventBus:
    """Central event bus for communication."""
    
    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Subscribe to an event type."""
        self.subscribers[event_type].append(handler)
    
    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type."""
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(handler)
    
    def publish(self, event: Event) -> None:
        """Publish an event."""
        if event.type in self.subscribers:
            for handler in self.subscribers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")

# Global event bus instance
event_bus = EventBus()
'''
        
        core_dir = self.flowproc_dir / "core"
        with open(core_dir / "events.py", 'w') as f:
            f.write(event_content)
        
        print("✅ Event system created")
    
    def run_migration(self, phases: List[str] = None):
        """Run the complete migration."""
        if phases is None:
            phases = ["backup", "interfaces", "container", "pipeline", "events", "visualization", "parsing"]
        
        print("🚀 Starting FlowProcessor migration...")
        
        for phase in phases:
            if phase == "backup":
                self.create_backup()
            elif phase == "interfaces":
                self.create_service_interfaces()
            elif phase == "container":
                self.create_dependency_injection_container()
            elif phase == "pipeline":
                self.create_pipeline_pattern()
            elif phase == "events":
                self.create_event_system()
            elif phase == "visualization":
                self.consolidate_visualization_services()
            elif phase == "parsing":
                self.consolidate_parsing_services()
        
        print("✅ Migration completed successfully!")
        print(f"📁 Backup available at: {self.backup_dir}")

def main():
    """Main function."""
    helper = MigrationHelper()
    
    print("🔧 FlowProcessor Migration Helper")
    print("=" * 50)
    print("1. Run complete migration")
    print("2. Create backup only")
    print("3. Consolidate visualization services")
    print("4. Consolidate parsing services")
    print("5. Create service interfaces")
    print("6. Create DI container")
    print("7. Create pipeline pattern")
    print("8. Create event system")
    
    choice = input("\nEnter your choice (1-8): ").strip()
    
    if choice == "1":
        helper.run_migration()
    elif choice == "2":
        helper.create_backup()
    elif choice == "3":
        helper.consolidate_visualization_services()
    elif choice == "4":
        helper.consolidate_parsing_services()
    elif choice == "5":
        helper.create_service_interfaces()
    elif choice == "6":
        helper.create_dependency_injection_container()
    elif choice == "7":
        helper.create_pipeline_pattern()
    elif choice == "8":
        helper.create_event_system()
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 