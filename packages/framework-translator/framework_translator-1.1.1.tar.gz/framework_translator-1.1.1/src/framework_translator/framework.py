from abc import ABC, abstractmethod
from typing import List, Dict, Type, Optional


class Framework(ABC):
    """Base framework class"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def language(self) -> str:
        pass
    
    @property
    @abstractmethod
    def group(self) -> str:
        pass
    
    @abstractmethod
    def get_model(self) -> str:
        """Get the model being used for translation"""
        pass


class MachineLearningFramework(Framework):
    """Base class for machine learning frameworks"""
    
    @property
    def group(self) -> str:
        return "ml"
    
    @abstractmethod
    def get_temperature(self) -> float:
        """Get the temperature for ML frameworks"""
        pass
    
    @abstractmethod
    def get_model(self) -> str:
        """Get the model being used for translation"""
        pass


class PythonFramework(MachineLearningFramework):
    """Base class for Python machine learning frameworks"""
    
    @property
    def language(self) -> str:
        return "python"
    
    @abstractmethod
    def get_temperature(self) -> float:
        """Get the temperature for Python ML frameworks"""
        pass
    
    @abstractmethod
    def get_model(self) -> str:
        """Get the model being used for translation"""
        pass


class JAXFramework(PythonFramework):
    @property
    def name(self) -> str:
        return "jax"
    
    def get_temperature(self) -> float:
        return 1.0
    
    def get_model(self) -> str:
        return "o1"


class TensorFlowFramework(PythonFramework):
    @property
    def name(self) -> str:
        return "tensorflow"
    
    def get_temperature(self) -> float:
        return 1.0
    
    def get_model(self) -> str:
        return "o1"


class PyTorchFramework(PythonFramework):
    @property
    def name(self) -> str:
        return "pytorch"
    
    def get_temperature(self) -> float:
        return 1.0
    
    def get_model(self) -> str:
        return "gpt-5"


class ScikitLearnFramework(PythonFramework):
    @property
    def name(self) -> str:
        return "scikit-learn"
    
    def get_temperature(self) -> float:
        return 1.0
    
    def get_model(self) -> str:
        return "o1"


class FrameworkRegistry:
    """Registry to manage framework instances and queries"""
    
    def __init__(self):
        self._frameworks = [
            JAXFramework(),
            TensorFlowFramework(),
            PyTorchFramework(),
            ScikitLearnFramework(),
        ]
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        languages = set()
        for framework in self._frameworks:
            languages.add(framework.language)
        return sorted(list(languages))
    
    def get_supported_groups(self, language: str) -> List[str]:
        """Get list of supported groups for a language"""
        groups = set()
        for framework in self._frameworks:
            if framework.language.lower() == language.lower():
                groups.add(framework.group)
        return sorted(list(groups))
    
    def get_supported_frameworks(self, group: str) -> List[str]:
        """Get list of supported frameworks for a group"""
        frameworks = []
        for framework in self._frameworks:
            if framework.group.lower() == group.lower():
                frameworks.append(framework.name)
        return sorted(frameworks)
    
    def get_framework_by_name(self, name: str) -> Optional[Framework]:
        """Get framework instance by name"""
        for framework in self._frameworks:
            if framework.name.lower() == name.lower():
                return framework
        return None
    
    def get_frameworks_by_language(self, language: str) -> List[Framework]:
        """Get all frameworks for a language"""
        return [f for f in self._frameworks if f.language.lower() == language.lower()]
    
    def get_frameworks_by_group(self, group: str) -> List[Framework]:
        """Get all frameworks for a group"""
        return [f for f in self._frameworks if f.group.lower() == group.lower()]


# Global registry instance
registry = FrameworkRegistry()
