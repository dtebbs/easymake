
import os

print "Import easymake"

libs = {}
apps = {}

allmodules = {}

OBJPATH = 'obj'
LIBPATH = 'lib'

sysincdirs = []

############################################################

def _config(env):

    env['CXX'] = "../../android-ndk-r5/toolchains/arm-linux-androideabi-4.4.3/prebuilt/darwin-x86/bin/arm-linux-androideabi-g++"
    env['CXXFLAGS'] = [ "-fpic",
                        "-mthumb-interwork",
                        "-ffunction-sections",
                        "-funwind-tables",
                        "-fstack-protector",
                        "-fno-short-enums",
                        "-fno-rtti",
                        "-fno-exceptions",
                        "-march=armv5te",
                        "-mtune=xscale",
                        "-msoft-float",
                        "-fomit-frame-pointer",
                        "-fno-strict-aliasing",
                        "-finline-limit=64",
                        "-Wall",
                        "-Wno-reorder",
                        "-Wno-psabi",
                        "-D__ARM_ARCH_5__",
                        "-D__ARM_ARCH_5T__",
                        "-D__ARM_ARCH_5E__",
                        "-D__ARM_ARCH_5TE__",
                        "-DANDROID",
                        "-Os",
                        "-DNDEBUG",
                        "-DD_GLES11",
                        "-DPACKAGENAME=\"finalfwy\"",
                        "-DGAME_COM_DOMAIN_STR=\"com.dpasca.therun\"" ]

    global sysincdirs
    sysincdirs = [ "../../android-ndk-r5/platforms/android-8/arch-arm/usr/include",
                   "../../android-ndk-r5/sources/cxx-stl/system/include",
                   "Apps/TheRun/android/core/nativesrc" ]


# ../../../../../../android-ndk-r5/toolchains/arm-linux-androideabi-4.4.3/prebuilt/darwin-x86/bin/arm-linux-androideabi-g++ -I../../../../../../android-ndk-r5/platforms/android-8/arch-arm/usr/include -I../../../../../../android-ndk-r5/sources/cxx-stl/system/include -c  -I../core/./nativesrc -I../core/../../../../DGameSystem/include -I../core/../../../../DSystem/include -I../core/../../../../DMath/include -I../core/../../../../externals/libpng -I../../src /Users/dtebbs/android/dev/therun/Apps/TheRun/android/core/nativesrc/native_onlinehiscore.cpp -o objs/native_onlinehiscore.o

############################################################

class Module(object):
    def __init__(self):
        pass

class Library(Module):
    # _name
    # _srcdirs
    # _incdirs
    # _depnames
    # _fulldeps
    def __init__(self, name, srcdirs="", incdirs="", deps=[]):
        super(Library, self).__init__()
        self._name = name

        if isinstance(srcdirs, str):
            self._srcdirs = [ srcdirs ]
        else:
            self._srcdirs = srcdirs

        if isinstance(srcdirs, str):
            self._incdirs = [ incdirs ]
        else:
            self._incdirs = incdirs

        self._depnames = deps

        self._fulldeps = None
        self._target = None

        if name in libs:
            print "Library %s already defined" % name
        libs[name] = self

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

            # The any dependencies of depmod

            for depdep in depmod._fulldeps:
                if not depdep in self._fulldeps:
                    self._fulldeps = [ depdep ] + self._fulldeps

            # Add depmod itself

            self._fulldeps = [ depmod ] + self._fulldeps
        print "Module %s has deps: %s" %(self._name, [a._name for a in self._fulldeps])

    #
    def _defineobjects(self, env):
        allsrc = []

        if self._srcdirs is not None:
            for sd in self._srcdirs:
                globpath = sd + "/*.cpp"
                print "globbing: %s" % globpath
                allsrc += env.Glob(globpath)
                globpath = sd + "/*.c"
                print "globbing: %s" % globpath
                allsrc += env.Glob(globpath)
        print "Mod %s: src: %s" %(self._name, [str(i) for i in allsrc])

        # Object directory

        objectpath = OBJPATH + "/" + self._name

        # Full include paths for this module

        includepaths = []
        includepaths += sysincdirs
        for d in self._fulldeps:
            includepaths += [ d._incdirs ]
        includepaths += [ self._incdirs ]

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
    def _definescons(self, env):
        if not self._target is None:
            return

        # Not much to do for static libs

        objects = self._defineobjects(env)

        self._target = env.StaticLibrary(target=LIBPATH+"/"+self._name,
                                         source=objects)

############################################################

def build(env):

    # configuration

    _config(env)

    # List of all modules

    for l in libs:
        allmodules[l] = libs[l]
    for a in apps:
        allmodules[a] = apps[a]

    # Calculate full dependencies

    for m in allmodules:
        mod = allmodules[m]
        mod._calcdeps()

    # Define Scons rules

    for m in allmodules:
        mod = allmodules[m]
        mod._definescons(env)
