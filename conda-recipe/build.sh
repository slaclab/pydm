# Install the package
$PYTHON -m pip install . --no-deps -vv

# Create auxiliary dirs
mkdir -p $PREFIX/etc/conda/activate.d
mkdir -p $PREFIX/etc/conda/deactivate.d
mkdir -p $PREFIX/etc/pydm

# Create auxiliary vars
DESIGNER_PLUGIN_PATH=$PREFIX/etc/pydm
DESIGNER_PLUGIN=$DESIGNER_PLUGIN_PATH/pydm_designer_plugin.py
ACTIVATE=$PREFIX/etc/conda/activate.d/pydm
DEACTIVATE=$PREFIX/etc/conda/deactivate.d/pydm

echo "from pydm.widgets.qtplugins import *" >> $DESIGNER_PLUGIN

echo "export PYQTDESIGNERPATH=\$CONDA_PREFIX/etc/pydm:\$PYQTDESIGNERPATH" >> $ACTIVATE.sh
echo "unset PYQTDESIGNERPATH" >> $DEACTIVATE.sh

echo '@echo OFF' >> $ACTIVATE.bat
echo 'IF "%PYQTDESIGNERPATH%" == "" (' >> $ACTIVATE.bat
echo 'set PYQTDESIGNERPATH=%CONDA_PREFIX%\etc\pydm' >> $ACTIVATE.bat
echo ')ELSE (' >> $ACTIVATE.bat
echo 'set PYQTDESIGNERPATH=%CONDA_PREFIX%\etc\pydm;%PYQTDESIGNERPATH%' >> $ACTIVATE.bat
echo ')' >> $ACTIVATE.bat

unset DESIGNER_PLUGIN_PATH
unset DESIGNER_PLUGIN
unset ACTIVATE
unset DEACTIVATE
