# Test básico para verificar que PySide6 se puede inicializar
from PySide6.QtWidgets import QApplication

def test_pyside_initialization():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    assert app is not None
    assert isinstance(app, QApplication)
