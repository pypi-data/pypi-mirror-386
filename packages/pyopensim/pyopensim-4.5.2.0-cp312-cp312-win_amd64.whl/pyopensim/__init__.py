"""
PyOpenSim: Python bindings for OpenSim using SWIG

This package provides Python bindings for the OpenSim biomechanical modeling
and simulation toolkit.
"""


# start delvewheel patch
def _delvewheel_patch_1_11_2():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'pyopensim.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_11_2()
del _delvewheel_patch_1_11_2
# end delvewheel patch

import sys
import os
import ctypes
import atexit

# Get the current directory
_curFolder = os.path.dirname(os.path.realpath(__file__))
_lib_path = os.path.join(_curFolder, 'lib')

# Set up library loading - CRITICAL: must be done before importing SWIG modules
if sys.platform.startswith('win'):
    # Windows: add DLL directory
    if os.path.exists(_lib_path):
        os.add_dll_directory(_lib_path)
else:
    # Unix-like: preload essential libraries and update LD_LIBRARY_PATH
    if os.path.exists(_lib_path):
        # Add to LD_LIBRARY_PATH for subprocess
        if 'LD_LIBRARY_PATH' in os.environ:
            os.environ['LD_LIBRARY_PATH'] = _lib_path + os.pathsep + os.environ['LD_LIBRARY_PATH']
        else:
            os.environ['LD_LIBRARY_PATH'] = _lib_path
        
        # Preload critical libraries in correct order
        # Use platform-appropriate library extension
        lib_ext = '.dylib' if sys.platform == 'darwin' else '.so'
        try:
            ctypes.CDLL(os.path.join(_lib_path, f'libSimTKcommon{lib_ext}'), mode=ctypes.RTLD_GLOBAL)
            ctypes.CDLL(os.path.join(_lib_path, f'libSimTKmath{lib_ext}'), mode=ctypes.RTLD_GLOBAL)
            ctypes.CDLL(os.path.join(_lib_path, f'libSimTKsimbody{lib_ext}'), mode=ctypes.RTLD_GLOBAL)
        except OSError as e:
            print(f"Warning: Could not preload SimTK libraries: {e}")

# Make pyopensim appear as opensim for SWIG module compatibility
import sys
sys.modules['opensim'] = sys.modules[__name__]

# Import SWIG-generated modules as submodules (preserving structure)
try:
    from . import simbody
except ImportError as e:
    print(f"Warning: Could not import simbody module: {e}")
    simbody = None

try:
    from . import common
except ImportError as e:
    print(f"Warning: Could not import common module: {e}")
    common = None

try:
    from . import simulation
except ImportError as e:
    print(f"Warning: Could not import simulation module: {e}")
    simulation = None

try:
    from . import actuators
except ImportError as e:
    print(f"Warning: Could not import actuators module: {e}")
    actuators = None

try:
    from . import analyses
except ImportError as e:
    print(f"Warning: Could not import analyses module: {e}")
    analyses = None

try:
    from . import tools
except ImportError as e:
    print(f"Warning: Could not import tools module: {e}")
    tools = None

# Try to import optional modules
try:
    from . import examplecomponents
except ImportError:
    examplecomponents = None  # Optional module

try:
    from . import moco
except ImportError:
    moco = None  # Optional module

try:
    from . import report
except ImportError:
    report = None  # Optional module

# For backwards compatibility with OpenSim's flat namespace,
# also import commonly used classes at the top level
if simbody:
    # SimTK and geometry classes from simbody
    for cls_name in ['Vec3', 'Rotation', 'Transform', 'Inertia', 'Gray', 'SimTK_PI']:
        try:
            cls = getattr(simbody, cls_name)
            globals()[cls_name] = cls
        except AttributeError:
            pass  # Class doesn't exist in this module

if common:
    # Core modeling classes
    for cls_name in ['Component', 'Property', 'Storage', 'Array', 'StepFunction', 'ConsoleReporter']:
        try:
            cls = getattr(common, cls_name)
            globals()[cls_name] = cls
        except AttributeError:
            pass  # Class doesn't exist in this module

if simulation:
    # Simulation classes - import each individually to avoid failures
    for cls_name in ['Model', 'Manager', 'State', 'Body', 'PinJoint', 'PhysicalOffsetFrame', 
                     'Ellipsoid', 'Millard2012EquilibriumMuscle', 'PrescribedController',
                     'InverseKinematicsSolver', 'InverseDynamicsSolver']:
        try:
            cls = getattr(simulation, cls_name)
            globals()[cls_name] = cls
        except AttributeError:
            pass  # Class doesn't exist in this module

if actuators:
    # Common actuator classes
    for cls_name in ['Muscle', 'CoordinateActuator', 'PointActuator']:
        try:
            cls = getattr(actuators, cls_name)
            globals()[cls_name] = cls
        except AttributeError:
            pass  # Class doesn't exist in this module

if tools:
    # Analysis tools
    for cls_name in ['InverseKinematicsTool', 'InverseDynamicsTool', 'ForwardTool', 'AnalyzeTool']:
        try:
            cls = getattr(tools, cls_name)
            globals()[cls_name] = cls
        except AttributeError:
            pass  # Class doesn't exist in this module

# Import version information
# Try to import from _version.py (generated during build), fallback to package metadata
try:
    from ._version import __version__, __opensim_version__
except ImportError:
    # Fallback to package metadata
    try:
        from importlib.metadata import version
        __version__ = version("pyopensim")
        __opensim_version__ = __version__  # Best guess
    except ImportError:
        # Fallback for Python < 3.8
        try:
            from importlib_metadata import version
            __version__ = version("pyopensim")
            __opensim_version__ = __version__  # Best guess
        except ImportError:
            __version__ = "0.0.0"  # Fallback version
            __opensim_version__ = "0.0.0"

# Set up geometry path if available
_geometry_path = os.path.join(_curFolder, 'Geometry')
if os.path.exists(_geometry_path):
    try:
        ModelVisualizer.addDirToGeometrySearchPaths(_geometry_path)
    except NameError:
        pass  # ModelVisualizer not available

# Define what's available when using 'from pyopensim import *'
__all__ = [
    # Core modules
    'simbody', 'common', 'simulation', 'actuators', 'analyses', 'tools',
    # Optional modules (if available)
    'examplecomponents', 'moco', 'report',
    # Common classes at top level for convenience
    'Model', 'Manager', 'State', 'Body',
    'Component', 'Property',
    'Vec3', 'Rotation', 'Transform', 'Inertia',
    'PinJoint', 'PhysicalOffsetFrame', 'Ellipsoid',
    'Millard2012EquilibriumMuscle', 'PrescribedController',
    'StepFunction', 'ConsoleReporter',
    'Gray', 'SimTK_PI',
    'Storage', 'Array',
    'InverseKinematicsSolver', 'InverseDynamicsSolver',
    'Muscle', 'CoordinateActuator', 'PointActuator',
    'InverseKinematicsTool', 'InverseDynamicsTool',
    'ForwardTool', 'AnalyzeTool',
    '__version__', '__opensim_version__'
]

# Filter out None values from __all__ (for optional modules that failed to import)
__all__ = [item for item in __all__ if globals().get(item) is not None]

# Exit handler to prevent segfaults during cleanup
def _cleanup_opensim():
    """Cleanup function to prevent segfaults during Python exit."""
    try:
        # Force garbage collection to clean up objects before static destructors
        import gc
        
        # Clear globals that might hold OpenSim objects
        global simbody, common, simulation, actuators, analyses, tools
        global examplecomponents, moco, report
        
        # Clear references to potentially problematic modules
        for name in ['simbody', 'common', 'simulation', 'actuators', 'analyses', 'tools',
                     'examplecomponents', 'moco', 'report']:
            if name in globals():
                globals()[name] = None
        
        # Force garbage collection
        gc.collect()
        gc.collect()  # Call twice to handle circular references
        
    except:
        pass  # Ignore any errors during cleanup

# Register cleanup handler - only for test environments or when explicitly requested
if 'pytest' in sys.modules or os.environ.get('PYOPENSIM_FORCE_EXIT_HANDLER'):
    atexit.register(_cleanup_opensim)
