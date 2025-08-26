# Install the package
$PYTHON -m pip install . --no-deps -vv

# Create auxiliary dirs
mkdir -p $PREFIX/etc/conda/activate.d
mkdir -p $PREFIX/etc/conda/deactivate.d
mkdir -p $PREFIX/etc/pydm

# Create auxiliary vars
DESIGNER_PLUGIN_PATH=$PREFIX/etc/pydm
DESIGNER_PLUGIN=$DESIGNER_PLUGIN_PATH/register_pydm_designer_plugin.py
ACTIVATE=$PREFIX/etc/conda/activate.d/pydm
DEACTIVATE=$PREFIX/etc/conda/deactivate.d/pydm

cat ./pydm/register_pydm_designer_plugin.py >> $DESIGNER_PLUGIN

echo "export PYQTDESIGNERPATH=\$CONDA_PREFIX/etc/pydm:\$PYQTDESIGNERPATH" >> $ACTIVATE.sh
echo "export PYSIDE_DESIGNER_PLUGINS=\$CONDA_PREFIX/etc/pydm:\$PYSIDE_DESIGNER_PLUGINS" >> $ACTIVATE.sh
echo "unset PYQTDESIGNERPATH" >> $DEACTIVATE.sh
echo "unset PYSIDE_DESIGNER_PLUGINS" >> $DEACTIVATE.sh

echo '@echo OFF' >> $ACTIVATE.bat
echo 'IF "%PYQTDESIGNERPATH%" == "" (' >> $ACTIVATE.bat
echo 'set PYQTDESIGNERPATH=%CONDA_PREFIX%\etc\pydm' >> $ACTIVATE.bat
echo ')ELSE (' >> $ACTIVATE.bat
echo 'set PYQTDESIGNERPATH=%CONDA_PREFIX%\etc\pydm;%PYQTDESIGNERPATH%' >> $ACTIVATE.bat
echo ')' >> $ACTIVATE.bat
echo 'IF "%PYSIDE_DESIGNER_PLUGINS%" == "" (' >> $ACTIVATE.bat
echo 'set PYSIDE_DESIGNER_PLUGINS=%CONDA_PREFIX%\etc\pydm' >> $ACTIVATE.bat
echo ')ELSE (' >> $ACTIVATE.bat
echo 'set PYSIDE_DESIGNER_PLUGINS=%CONDA_PREFIX%\etc\pydm;%PYSIDE_DESIGNER_PLUGINS%' >> $ACTIVATE.bat
echo ')' >> $ACTIVATE.bat

unset DESIGNER_PLUGIN_PATH
unset DESIGNER_PLUGIN
unset ACTIVATE
unset DEACTIVATE
