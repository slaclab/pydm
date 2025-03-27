#!/usr/bin/env python
import os
import sys
import pytest

if __name__ == "__main__":
    # Show output results from every test function
    # Show the message output for skipped and expected failures
    args = ["-v", "-vrxs"]

    # Add extra arguments
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])

    # Show coverage
    if "--show-cov" in args:
        args.extend(["--cov=pydm", "--cov-report", "term-missing"])
        args.remove("--show-cov")

    # Exclude p4p and pyca tests on Windows until p4p/pyepics compatibility issue is resolved
    # and a Windows PyCA build exists
    if os.name == "nt":
        args.append("--ignore=pydm/tests/data_plugins/test_p4p_plugin_component.py")
        args.append("--ignore=pydm/tests/data_plugins/test_psp_plugin_component.py")

    print("pytest arguments: {}".format(args))

    sys.exit(pytest.main(args))
