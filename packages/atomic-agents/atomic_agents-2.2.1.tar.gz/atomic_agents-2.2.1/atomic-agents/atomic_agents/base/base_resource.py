from typing import Optional, Type, get_args, get_origin
from abc import ABC, abstractmethod
from pydantic import BaseModel

from atomic_agents.base.base_io_schema import BaseIOSchema


class BaseResourceConfig(BaseModel):
    """
    Configuration for a resource.

    Attributes:
        title (Optional[str]): Overrides the default title of the resource.
        description (Optional[str]): Overrides the default description of the resource.
    """

    title: Optional[str] = None
    description: Optional[str] = None


class BaseResource[InputSchema: BaseIOSchema, OutputSchema: BaseIOSchema](ABC):
    """
    Base class for resources within the Atomic Agents framework.

    Resources enable agents to perform specific tasks by providing a standardized interface
    for input and output. Each resource is defined with specific input and output schemas
    that enforce type safety and provide documentation.

    Type Parameters:
        InputSchema: Schema defining the input data, must be a subclass of BaseIOSchema.
        OutputSchema: Schema defining the output data, must be a subclass of BaseIOSchema.

    Attributes:
        config (BaseResourceConfig): Configuration for the resource, including optional title and description overrides.
        input_schema (Type[InputSchema]): Schema class defining the input data (derived from generic type parameter).
        output_schema (Type[OutputSchema]): Schema class defining the output data (derived from generic type parameter).
        resource_name (str): The name of the resource, derived from the input schema's title or overridden by the config.
        resource_description (str): Description of the resource, derived from the input schema's description or overridden by the config.
    """

    def __init__(self, config: BaseResourceConfig = BaseResourceConfig()):
        """
        Initializes the BaseResource with an optional configuration override.

        Args:
            config (BaseResourceConfig, optional): Configuration for the resource, including optional title and description overrides.
        """
        self.config = config

    def __init_subclass__(cls, **kwargs):
        """
        Hook called when a class is subclassed.

        Captures generic type parameters during class creation and stores them as class attributes
        to work around the unreliable __orig_class__ attribute in modern Python generic syntax.
        """
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "__orig_bases__"):
            for base in cls.__orig_bases__:
                if get_origin(base) is BaseResource:
                    args = get_args(base)
                    if len(args) == 2:
                        cls._input_schema_cls = args[0]
                        cls._output_schema_cls = args[1]
                        break

    @property
    def input_schema(self) -> Type[InputSchema]:
        """
        Returns the input schema class for the resource.

        Returns:
            Type[InputSchema]: The input schema class.
        """
        # Inheritance pattern: MyResource(BaseResource[Schema1, Schema2])
        if hasattr(self.__class__, "_input_schema_cls"):
            return self.__class__._input_schema_cls

        # Dynamic instantiation: MockResource[Schema1, Schema2]()
        if hasattr(self, "__orig_class__"):
            TI, _ = get_args(self.__orig_class__)
            return TI

        # No type info available: MockResource()
        return BaseIOSchema

    @property
    def output_schema(self) -> Type[OutputSchema]:
        """
        Returns the output schema class for the resource.

        Returns:
            Type[OutputSchema]: The output schema class.
        """
        # Inheritance pattern: MyResource(BaseResource[Schema1, Schema2])
        if hasattr(self.__class__, "_output_schema_cls"):
            return self.__class__._output_schema_cls

        # Dynamic instantiation: MockResource[Schema1, Schema2]()
        if hasattr(self, "__orig_class__"):
            _, TO = get_args(self.__orig_class__)
            return TO

        # No type info available: MockResource()
        return BaseIOSchema

    @property
    def resource_name(self) -> str:
        """
        Returns the name of the resource.

        Returns:
            str: The name of the resource.
        """
        return self.config.title or self.input_schema.model_json_schema()["title"]

    @property
    def resource_description(self) -> str:
        """
        Returns the description of the resource.

        Returns:
            str: The description of the resource.
        """
        return self.config.description or self.input_schema.model_json_schema()["description"]

    @abstractmethod
    def read(self, params: InputSchema) -> OutputSchema:
        """
        Executes the resource with the provided parameters.

        Args:
            params (InputSchema): Input parameters adhering to the input schema.

        Returns:
            OutputSchema: Output resulting from executing the resource, adhering to the output schema.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        pass
