from ipykernel.kernelapp import IPKernelApp
from . import ExampleAgent


IPKernelApp.launch_instance(kernel_class=ExampleAgent)
