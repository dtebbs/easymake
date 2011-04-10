
import os

print "Import easymake"

############################################################

class Config(object):
    def __init__(self,
                 buildconfig="debug",
                 platform="android"
                 ):
        self.buildconfig = buildconfig
        self.platform = platform

############################################################

class Settings(object):
    def __init__(self, config):

        platform = config.platform
        buildconfig = config.buildconfig

        self.OBJPATH = "obj/%s-%s" % (platform, buildconfig)
        self.LIBPATH = "lib/%s-%s" % (platform, buildconfig)
        self.DLLPATH = "dll/%s-%s" % (platform, buildconfig)

        self.sysincdirs = []
        self.syslibpaths = []
        self.syslibs = []
        self.dllsyslibs = []

        self.CXX = None
        self.CXXFLAGS = []
        self.CC = None
        self.CFLAGS = []
        self.AR = None
        self.RANLIB = None
        self.LIBTOOL = None
        self.LINK = None

        self.scons_make_objects = None
        self.scons_make_staticlib = None
        self.scons_make_dynamiclib = None

        pass

############################################################

def _make_str_array(stringOrArray):
    if isinstance(stringOrArray, str):
        return [ stringOrArray ]
    elif isinstance(stringOrArray, list):
        return stringOrArray
    elif stringOrArray is None:
        return []
    else:
        raise "Object %s cannot be converted to array of string" % stringOrArray

############################################################

# Config is passed to the platform-specific config file, which fills
# out a settings objects.

# Functions:
#    scons_make_objects
#    scons_make_staticlib
#    scons_make_dynamiclib
# Take args:  (module, env, config, settings)
# Return: [ <targets> ]

############################################################

#
#
#
class Module(object):
    # _name
    # _srcdirs
    # _incdirs
    # _depnames
    # _fulldeps
    def __init__(self, name,
                 srcdirs,
                 incdirs,
                 deps,
                 srcfiles,
                 srcexcludes,
                 incdirs_internal):
        self._name = name

        if (srcfiles != []) and (srcdirs != []):
            raise "Cannot use both srcdirs and srcfiles attributes"

        self._srcdirs = _make_str_array(srcdirs)
        self._incdirs = _make_str_array(incdirs)
        self._srcfiles = _make_str_array(srcfiles)
        self._srcexcludes = _make_str_array(srcexcludes)
        self._incdirs_internal = _make_str_array(incdirs_internal)

        # Deps get resolved later
        self._depnames = deps

        # For now, keep these as None
        self._fulldeps = None
        self._objects = None
        self._target = None

    #
    def _calcdeps(self):
        if not self._fulldeps is None:
            print "earlying out (%s)" %self._name
            return

        self._fulldeps = []
        for dep in self._depnames:
            if isinstance(dep, str):
                print "dep is name: %s" % dep
                depmod = allmodules[dep]
            elif isinstance(dep, Module):
                print "dep is module: %s" % dep
                depmod = dep
            else:
                raise "Unknown module %s" % dep
            depmod._calcdeps()

            # Add any dependencies of depmod.  We always track from
            # right to left, adding on the left.  This keeps a given
            # module to the left of (i.e. before) it's dependencies.

            print "Recursively adding dependencies of %s" % depmod._name
            for depDep in reversed(depmod._fulldeps):
                if not depDep in self._fulldeps:
                    self._fulldeps = [ depDep ] + self._fulldeps

            # Add depmod itself

            if not depmod in self._fulldeps:
                self._fulldeps = [ depmod ] + self._fulldeps
        print "Module %s has deps: %s" %(self._name, [a._name for a in self._fulldeps])

    #
    def _defineobjects(self, env, config, settings):

        # Use platform specific version if it exists

        if not settings.scons_make_objects is None:
            fn = settings.scons_make_objects
            self._objects = fn(self, env, config, settings)
            return self._objects

        # Regular scons version.  Collect src files, filtering out
        # excludes.

        allsrc = []

        for sd in self._srcdirs:
            globres = env.Glob(sd + "/*.cpp")
            globres += env.Glob(sd + "/*.c")

            srcglob = []
            for g in globres:
                if not str(g) in self._srcexcludes:
                    srcglob += [ g ]

            allsrc += srcglob

        for sf in self._srcfiles:
            if not sf in self._srcexcludes:
                allsrc += env.Glob(sf)

        srcS = [str(s) for s in allsrc]
        print "Mod %s: src: %s" %(self._name, srcS)

        # Object directory

        objectpath = settings.OBJPATH + "/" + self._name

        # Full include paths for this module

        includepaths = settings.sysincdirs
        for d in self._fulldeps:
            includepaths += [ d._incdirs ]
        includepaths += [ self._incdirs ]
        includepaths += self._incdirs_internal

        # Create the rules

        objects = []
        for src in allsrc:
            s = str(src)
            sbase = os.path.basename(s)
            (objname, ext) = os.path.splitext(sbase)

            obj=objectpath+"/"+objname
            print "Object: %s source: %s" % (obj, s)

            objects += env.Object(source=s,
                                  target=obj,
                                  CPPPATH=includepaths)

        self._objects = objects
        return objects

#
#
#
class Library(Module):


    def __init__(self, name,
                 srcdirs=[],
                 incdirs=[],
                 deps=[],
                 srcfiles = [],
                 srcexcludes = [],
                 incdirs_internal = []):
        super(Library, self).__init__(name,
                                      srcdirs,
                                      incdirs,
                                      deps,
                                      srcfiles,
                                      srcexcludes,
                                      incdirs_internal)
        if name in libs:
            print "Library %s already defined" % name
        libs[name] = self

    #
    def _definescons(self, env, config, settings):
        if not self._target is None:
            return

        # Make sure objects have been defined for this module

        objects = self._defineobjects(env, config, settings)

        # Custom static lib creation?

        if not settings.scons_make_staticlib is None:
            fn = settings.scons_make_staticlib
            self._target = fn(mod, env, config, settings)
            return

        # Not much to do for static libs

        libfile = settings.LIBPATH+"/"+self._name
        self._target = env.StaticLibrary(target=libfile,
                                         source=objects)
        print "Lib: %s target: %s" % (self._name, self._target)

#
#
#
class DynamicLibrary(Module):

    def __init__(self, name,
                 srcdirs=[],
                 incdirs=[],
                 deps=[],
                 srcfiles = [],
                 srcexcludes = [],
                 incdirs_internal = []):
        super(DynamicLibrary, self).__init__(name,
                                             srcdirs,
                                             incdirs,
                                             deps,
                                             srcfiles,
                                             srcexcludes,
                                             incdirs_internal)
        if name in dlls:
            print "DynamicLibrary %s already defined" % name
        dlls[name] = self

    def _definescons(self, env, config, settings):
        if not self._target is None:
            return

        # Make sure all deps targets are created, and get the object
        # list

        for d in self._fulldeps:
            d._definescons(env, config, settings)
        objects = self._defineobjects(env, config, settings)

        # Platform-specific version?

        if not settings.scons_make_dynamiclib is None:
            fn = settings.scons_make_dynamiclib
            self._target = fn(self, env, config, settings)
            return

        # Standard version.  Get all lib requirements

        deplibs = []
        for d in self._fulldeps:
            deplibs += d._target
        deplibs += settings.dllsyslibs

        dllout = settings.DLLPATH + "/lib" + self._name + ".so"
        syslibpaths = settings.syslibpaths

        self._target = env.SharedLibrary(target = dllout,
                                         source = objects,
                                         LIBS = deplibs,
                                         LIBPATH = syslibpaths)


"""
../../android-ndk-r5/toolchains/arm-linux-androideabi-4.4.3/prebuilt/darwin-x86/bin/arm-linux-androideabi-gcc
* -nostdlib
* -Wl,-soname,lib.so
* -Wl,-shared,-Bsymbolic
 <objects>
 lib/android-debug/libtherunlib.a lib/android-debug/libdgamesystem.a
 lib/android-debug/libpng.a
 lib/android-debug/libdmath.a
 lib/android-debug/libdsystem.a
 lib/android-debug/libandroidplatform.a
 -L../../android-ndk-r5/platforms/android-8/arch-arm/usr/lib
 ../../android-ndk-r5/toolchains/arm-linux-androideabi-4.4.3/prebuilt/darwin-x86/lib/gcc/arm-linux-androideabi/4.4.3/libgcc.a
 ../../android-ndk-r5/platforms/android-8/arch-arm/usr/lib/libc.so
 ../../android-ndk-r5/platforms/android-8/arch-arm/usr/lib/libstdc++.so
 ../../android-ndk-r5/platforms/android-8/arch-arm/usr/lib/libm.so
 -lGLESv1_CM
 -llog
 -Wl,--no-whole-archive
 --sysroot=../../android-ndk-r5/platforms/android-8/arch-arm-Wl,--no-undefined
 -Wl,-z,noexecstack-Wl,-rpath-link=../../android-ndk-r5/platforms/android-8/arch-arm/usr/lib
 -o dll/android-debug/libtherun.so
"""


        # self._target = env.SharedLibrary(target=DLLPATH+"/"+self._name,
        #                                  source=objects)

############################################################

libs = {}
dlls = {}
apps = {}
allmodules = {}

############################################################

############################################################
# Build
############################################################

def setenv(env, name, value):
    if value is None:
        return
    if isinstance(value, list) and len(value) == 0:
        return
    print "setting env['%s'] = %s" % (name, value)
    env[name] = value

def build(env, config, settings = None):

    # Settings for this platform

    exec('import config_'+config.platform+ ' as _config')

    if settings is None:
        settings = Settings(config)

    # configuration

    _config._config(config, settings)

    # Set up the env

    setenv(env, 'CXX', settings.CXX)
    setenv(env, 'CXXFLAGS', settings.CXXFLAGS)
    setenv(env, 'CC', settings.CC)
    setenv(env, 'CFLAGS', settings.CFLAGS)
    setenv(env, 'AR', settings.AR)
    setenv(env, 'RANLIB', settings.RANLIB)
    setenv(env, 'LIBTOOL', settings.LIBTOOL)
    setenv(env, 'LINK', settings.LINK)

    # List of all modules

    for m in libs:
        allmodules[m] = libs[m]
    for m in dlls:
        allmodules[m] = dlls[m]
    for m in apps:
        allmodules[m] = apps[m]

    # Calculate full dependencies

    for m in allmodules:
        mod = allmodules[m]
        mod._calcdeps()

    # Define Scons rules

    for m in allmodules:
        mod = allmodules[m]
        mod._definescons(env, config, settings)

