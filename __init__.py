
import os

print "Import easymake"

libs = {}
dlls = {}
apps = {}
allmodules = {}

############################################################

# flags
# TOOLS
# TOOLFLAGS
# toolflags



platform = "android"
config = "debug"

OBJPATH = "obj/%s-%s" % (platform, config)
LIBPATH = "lib/%s-%s" % (platform, config)
DLLPATH = "dll/%s-%s" % (platform, config)

sysincdirs = []
#sysincdirs += [ "." ]

NDK_ROOT = "../../android-ndk-r5"
NDK_TOOLCHAIN_ROOT = NDK_ROOT + "/toolchains/arm-linux-androideabi-4.4.3/prebuilt/darwin-x86"
NDK_TOOLSBIN = NDK_TOOLCHAIN_ROOT+"/bin"
NDK_TOOLSLIB = NDK_TOOLCHAIN_ROOT+"/lib/gcc/arm-linux-androideabi/4.4.3"
NDK_PLATFORM_ROOT = NDK_ROOT + "/platforms/android-8/arch-arm"
NDK_PLATFORMLIB = NDK_PLATFORM_ROOT+"/usr/lib"

LINKDLL = NDK_TOOLSBIN + "/arm-linux-androideabi-gcc"
LINKDLL_FLAGS = " -nostdlib -Wl,-soname,lib.so -Wl,-shared,-Bsymbolic"
LINKDLL_FLAGS_POST = "-Wl,--no-whole-archive --sysroot="+NDK_PLATFORM_ROOT
LINKDLL_FLAGS_POST += "-Wl,--no-undefined -Wl,-z,noexecstack"
LINKDLL_FLAGS_POST += "-Wl,-rpath-link="+NDK_PLATFORMLIB
linkdll_out = "-o"

syslibpaths = [ NDK_PLATFORMLIB ]
syslibs = [ NDK_TOOLSLIB+"/libgcc.a",
            NDK_PLATFORMLIB+"/libc.so",
            NDK_PLATFORMLIB+"/libstdc++.so",
            NDK_PLATFORMLIB+"/libm.so",
            "-lGLESv1_CM",
            "-llog",
            "-lz"
            ]

############################################################

def _config(env, config):

    commonflags = [ "-fpic",
                    "-mthumb-interwork",
                    "-ffunction-sections",
                    "-funwind-tables",
                    "-fstack-protector",
                    "-fno-short-enums",
                    "-fno-exceptions",
                    "-march=armv5te",
                    "-mtune=xscale",
                    "-msoft-float",
                    "-fomit-frame-pointer",
                    "-fno-strict-aliasing",
                    "-finline-limit=64",
                    "-Wall",
                    "-Wno-psabi",
                    "-D__ARM_ARCH_5__",
                    "-D__ARM_ARCH_5T__",
                    "-D__ARM_ARCH_5E__",
                    "-D__ARM_ARCH_5TE__",
                    "-DANDROID" ]

    if config == "debug":
        commonflags += [ "-O0", "-DDEBUG", "-D_DEBUG" ]
    else:
        commonflags += [ "-Os", "-DNDEBUG" ]

    # CXX

    env['CXX'] = "../../android-ndk-r5/toolchains/arm-linux-androideabi-4.4.3/prebuilt/darwin-x86/bin/arm-linux-androideabi-g++"
    env['CXXFLAGS'] = commonflags + [ "-fno-rtti", "-Wno-reorder" ]
    if 'CXXFLAGS' in config:
        env['CXXFLAGS'] += config['CXXFLAGS']

    # CC

    env["CC"] = "../../android-ndk-r5/toolchains/arm-linux-androideabi-4.4.3/prebuilt/darwin-x86/bin/arm-linux-androideabi-gcc"
    env["CFLAGS"] = commonflags
    if 'CFLAGS' in config:
        env['CFLAGS'] += config['CFLAGS']

    global sysincdirs
    sysincdirs +=[ "../../android-ndk-r5/platforms/android-8/arch-arm/usr/include",
                   "../../android-ndk-r5/sources/cxx-stl/system/include"]

    env['AR'] = "../../android-ndk-r5/toolchains/arm-linux-androideabi-4.4.3/prebuilt/darwin-x86/bin/arm-linux-androideabi-ar"
    env['RANLIB'] = "../../android-ndk-r5/toolchains/arm-linux-androideabi-4.4.3/prebuilt/darwin-x86/bin/arm-linux-androideabi-ranlib"

    # LINK

    env['LIBTOOL'] = "adsf"
    env['LINK'] = "afadsf"

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

        # _srcdirs
        if isinstance(srcdirs, str):
            self._srcdirs = [ srcdirs ]
        elif len(srcdirs) != 0:
            self._srcdirs = srcdirs
        else:
            self._srcdirs = []

        # _srcfiles
        if isinstance(srcfiles, str):
            self._srcfiles = [ srcfiles ]
        elif len(srcfiles) != 0:
            self._srcfiles = srcfiles
        else:
            self._srcfiles = []

        # _srcexcludes
        if isinstance(srcexcludes, str):
            self._srcexcludes = [srcexcludes]
        elif len(srcexcludes) != 0:
            self._srcexcludes = srcexcludes
        else:
            self._srcexcludes = []

        # _incdirs
        if isinstance(incdirs, str):
            self._incdirs = [ incdirs ]
        else:
            self._incdirs = incdirs
        self._incdirs_internal = incdirs_internal

        self._depnames = deps

        self._fulldeps = None
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
    def _defineobjects(self, env):
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

        print "Mod %s: src: %s" %(self._name, [str(i) for i in allsrc])

        # Object directory

        objectpath = OBJPATH + "/" + self._name

        # Full include paths for this module

        includepaths = []
        includepaths += sysincdirs
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

            objects += env.Object(source=s,
                                  target=objectpath+"/"+objname,
                                  CPPPATH=includepaths)
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
    def _definescons(self, env):
        if not self._target is None:
            return

        # Not much to do for static libs

        objects = self._defineobjects(env)

        self._target = env.StaticLibrary(target=LIBPATH+"/"+self._name,
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

    def _definescons(self, env):
        if not self._target is None:
            return

        # Make sure any dependent libs have defined their targets

        for d in self._fulldeps:
            d._definescons(env)

        # Object rules

        objects = self._defineobjects(env)

        # Our build requirements:

        deplibs = []
        for d in self._fulldeps:
            deplibs += d._target

        dllout = DLLPATH + "/lib" + self._name + ".so"
        deplibsS = [ str(l) for l in deplibs ]
        deplibS = " ".join(deplibsS)

        objectsS = [ str(o) for o in objects ]
        objectS = " ".join(objectsS)

        #self._target = env.File(DLLPATH + "/lib" + self._name + ".so")
        #env.Depends(self._target, objects)

        cmd  = LINKDLL + " " + LINKDLL_FLAGS
        cmd += " " + objectS
        cmd += " " + LINKDLL_FLAGS_POST
        cmd += " " + deplibS
        cmd += " " + " ".join(syslibs)
        cmd += " " + " ".join([ "-L"+path for path in syslibpaths ])
        cmd += " " + linkdll_out + " $TARGET"
        self._target = env.Command(dllout, objects, cmd)
        env.Depends(self._target, deplibs)

"""
WORKING:
../../../../../../android-ndk-r5/toolchains/arm-linux-androideabi-4.4.3/prebuilt/darwin-x86/bin/arm-linux-androideabi-gcc
 -nostdlib
 -Wl,-soname,lib.so
 -Wl,-shared,-Bsymbolic
 <object files>
 -Wl,--no-whole-archive --sysroot=../../../../../../android-ndk-r5/platforms/android-8/arch-arm
 ../../../../../../android-ndk-r5/toolchains/arm-linux-androideabi-4.4.3/prebuilt/darwin-x86/lib/gcc/arm-linux-androideabi/4.4.3/libgcc.a
 ../../../../../../android-ndk-r5/platforms/android-8/arch-arm/usr/lib/libc.so
 ../../../../../../android-ndk-r5/platforms/android-8/arch-arm/usr/lib/libstdc++.so
 ../../../../../../android-ndk-r5/platforms/android-8/arch-arm/usr/lib/libm.so
 -Wl,--no-undefined
 -Wl,-z,noexecstack
 -L../../../../../../android-ndk-r5/platforms/android-8/arch-arm/usr/lib
 -lGLESv1_CM
 -llog
 -Wl,-rpath-link=../../../../../../android-ndk-r5/platforms/android-8/arch-arm/usr/lib
 -o libs/armeabi/liboyk-core.so
"""

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

def build(env, config):

    # configuration

    _config(env, config)

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
        mod._definescons(env)
