#!/usr/bin/env python
import sys
import pytest

if __name__ == '__main__':
    # Show output results from every test function
    # Show the message output for skipped and expected failures
    # Ignore the pyqtgraph test suite by default, can be run separately if working on pyqtgraph code. These tests are
    # located at pydm/pydm_pyqtgraph/examples and pydm/pydm_pyqtgraph/examples
    args = ['-v', '-vrxs', '--ignore=pydm/pydm_pyqtgraph/']

    # Add extra arguments
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])

    # Show coverage
    if '--show-cov' in args:
        args.extend(['--cov=pydm', '--cov-report', 'term-missing'])
        args.remove('--show-cov')

    print('pytest arguments: {}'.format(args))

    sys.exit(pytest.main(args))
