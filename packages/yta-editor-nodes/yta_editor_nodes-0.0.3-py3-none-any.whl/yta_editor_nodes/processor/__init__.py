"""
The nodes that are able to make simple processing.
"""
from yta_editor_nodes.utils import instantiate_cpu_and_gpu_processors
from yta_editor_nodes.abstract import _ProcessorGPUAndCPU
from yta_editor_nodes import Node
from typing import Union


class _NodeProcessor(_ProcessorGPUAndCPU, Node):
    """
    *Abstract class*
    
    *Singleton class*

    *For internal use only*

    *This class must be inherited by the specific
    implementation of some effect that will be done by
    CPU or GPU (at least one of the options)*

    A simple processor node that is capable of
    processing inputs and obtain a single output by
    using the GPU or the CPU.

    This type of node is for the effects and 
    transitions.
    """

    def __init__(
        self,
        node_processor_cpu: Union['_NodeProcessorCPU', None] = None,
        node_processor_gpu: Union['_NodeProcessorGPU', None] = None,
        do_use_gpu: bool = True,
    ):
        """
        The `node_processor_cpu` and `node_processor_gpu` have
        to be set by the developer when building the specific
        classes, but the `do_use_gpu` boolean flag will be set
        by the user when instantiating the class to choose 
        between GPU and CPU.
        """
        super().__init__(
            processor_cpu = node_processor_cpu,
            processor_gpu = node_processor_gpu,
            do_use_gpu = do_use_gpu
        )

    def __reinit__(
        self,
        node_processor_cpu: Union['_NodeProcessorCPU', None] = None,
        node_processor_gpu: Union['_NodeProcessorGPU', None] = None,
        do_use_gpu: bool = True,
    ):
        super().__reinit__(
            processor_cpu = node_processor_cpu,
            processor_gpu = node_processor_gpu,
            do_use_gpu = do_use_gpu
        )

    def process(
        self,
        # TODO: What about the type (?)
        input: Union['np.ndarray', 'moderngl.Texture'],
        **kwargs
    # TODO: What about the output type (?)
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the provided 'input' with GPU or CPU 
        according to the internal flag.
        """
        return self._processor.process(
            input = input,
            **kwargs
        )
    
# Specific implementations below
class SelectionMaskNodeProcessor(_NodeProcessor):
    """
    Class to use a mask selection (from which we will
    determine if the pixel must be applied or not) to
    apply the processed input over the original one.

    If the selection mask is completely full, the
    result will be the processed input.
    """

    def __init__(
        self,
        do_use_gpu: bool = True,
    ):
        """
        The `node_processor_cpu` and `node_processor_gpu` have
        to be set by the developer when building the specific
        classes, but the `do_use_gpu` boolean flag will be set
        by the user when instantiating the class to choose 
        between GPU and CPU.
        """
        # Dynamic way to import it
        node_processor_cpu, node_processor_gpu = instantiate_cpu_and_gpu_processors(
            class_name = 'SelectionMaskProcessor',
            cpu_module_path = 'yta_editor_nodes_cpu.processor',
            cpu_kwargs = {},
            gpu_module_path = 'yta_editor_nodes_gpu.processor',
            gpu_kwargs = {
                'opengl_context': None,
                # TODO: Do not hardcode please...
                'output_size': (1920, 1080),
            }
        )

        super().__init__(
            node_processor_cpu = node_processor_cpu,
            node_processor_gpu = node_processor_gpu,
            do_use_gpu = do_use_gpu
        )

    def __reinit__(
       self,
        node_processor_cpu: Union['_NodeProcessorCPU', None] = None,
        node_processor_gpu: Union['_NodeProcessorGPU', None] = None,
        do_use_gpu: bool = True,
    ):
        # Dynamic way to import it
        node_processor_cpu, node_processor_gpu = instantiate_cpu_and_gpu_processors(
            class_name = 'SelectionMaskProcessor',
            cpu_module_path = 'yta_editor_nodes_cpu.processor',
            cpu_kwargs = {},
            gpu_module_path = 'yta_editor_nodes_gpu.processor',
            gpu_kwargs = {
                'opengl_context': None,
                # We don't want to change the output
                'output_size': None,
            }
        )

        super().__reinit__(
            node_processor_cpu = node_processor_cpu,
            node_processor_gpu = node_processor_gpu,
            do_use_gpu = do_use_gpu
        )

    def process(
        self,
        # TODO: What about the type (?)
        original_input: Union['np.ndarray', 'moderngl.Texture'],
        processed_input: Union['np.ndarray', 'moderngl.Texture'],
        selection_mask_input: Union['np.ndarray', 'moderngl.Texture'],
        **kwargs
    # TODO: What about the output type (?)
    ) -> Union['np.ndarray', 'moderngl.Texture']:
        """
        Process the provided 'input' with GPU or CPU 
        according to the internal flag.
        """
        return self._processor.process(
            original_input = original_input,
            processed_input = processed_input,
            selection_mask_input = selection_mask_input,
            **kwargs
        )