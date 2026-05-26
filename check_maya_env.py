import sys
import maya.cmds as cmds

print("Maya version:", cmds.about(version=True))
print("Python version:", sys.version)

try:
    import PySide2
    print("PySide2:", PySide2.__version__)
except:
    try:
        import PySide6
        print("PySide6:", PySide6.__version__)
    except:
        print("No PySide found")

try:
    from shiboken2 import wrapInstance
    print("shiboken2: OK")
except:
    try:
        from shiboken6 import wrapInstance
        print("shiboken6: OK")
    except:
        print("No shiboken found")

print("Maya API:", cmds.about(api=True))