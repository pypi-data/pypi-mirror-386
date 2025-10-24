# Set up a Python venv with Avocado for development

VENV=avocado_venv
python3 -m venv $VENV
$VENV/bin/pip install avocado-framework
$VENV/bin/pip install build
. $VENV/bin/activate
