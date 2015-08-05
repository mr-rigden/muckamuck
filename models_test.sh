 #!/bin/bash
coverage run test_models.py
coverage report  --include="models.py"
coverage html --include="models.py"
