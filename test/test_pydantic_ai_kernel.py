# Useful for protocol-level test, not for kernel functionnalities
import unittest
import jupyter_kernel_test as jtk


class TestPydanticAIKernel(jtk.KernelTests):
    kernel_name = "pydantic_ai"

    # TESTS
    # checked against language_info.name in kernel_info_reply
    language_name = "pydantic_ai"

    # checked against language_info.file_extension
    file_extension = ".ai"

    # code that writes exactly "hello, world" to stdout
    # code_hello_world = "print('hello, world')"

    # code that writes anything to stderr
    # code_stderr = "import sys; print('error', file=sys.stderr)"

    # tab-completion samples: `text` is the partial input,
    # `matches` is a set of strings that must appear in the reply
    completion_samples = [
        {"text": r"%con", "matches": {r"%config"}},
    ]

    # used by console clients to decide whether to execute on <Enter>
    complete_code_samples = ["Hey"]
    incomplete_code_samples = ["Hey "]

    # # (code, expected string repr of the result) pairs
    # code_execute_result = [
    #     {"code": "1 + 1", "result": "2"},
    # ]

    # code that raises an error and sends a traceback
    # code_generate_error = "raise ValueError('oops')"

    # object name that the kernel can provide inspection help for
    # code_inspect_sample = "print"


if __name__ == "__main__":
    unittest.main()
