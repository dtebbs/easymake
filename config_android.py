
print "Importing Android Config"

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
 -lGLESv2
 -llog
 -Wl,-rpath-link=../../../../../../android-ndk-r5/platforms/android-8/arch-arm/usr/lib
 -o libs/armeabi/liboyk-core.so
"""

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

############################################################

def scons_make_dynamiclib(mod, env, config, settings):

    # This will only be called once for a given mod, and mod._fulldeps
    # will all have their ._target arrays set correctly

    # Our build requirements:

    objects = mod._objects

    deplibs = []
    for d in mod._fulldeps:
        deplibs += d._target

    dllout = settings.DLLPATH + "/lib" + mod._name + ".so"
    deplibsS = [ str(l) for l in deplibs ]
    deplibS = " ".join(deplibsS)

    objectsS = [ str(o) for o in objects ]
    objectS = " ".join(objectsS)

    # Construct the command

    syslibs = settings.dllsyslibs
    syslibpaths = settings.syslibpaths

    cmd  = LINKDLL + " " + LINKDLL_FLAGS
    cmd += " " + objectS
    cmd += " " + LINKDLL_FLAGS_POST
    cmd += " " + deplibS
    cmd += " " + " ".join(syslibs)
    cmd += " " + " ".join([ "-L"+path for path in syslibpaths ])
    cmd += " " + linkdll_out + " $TARGET"

    # Add the rule and extra dependencies

    target = env.Command(dllout, objects, cmd)
    env.Depends(target, deplibs)

    # Return the array of created targets

    return target

############################################################



############################################################

#
#
#
def _config(config, settings):

    # System libs and paths

    settings.syslibpaths += [ NDK_PLATFORMLIB ]
    settings.syslibs += [ NDK_TOOLSLIB+"/libgcc.a",
                          NDK_PLATFORMLIB+"/libc.so",
                          NDK_PLATFORMLIB+"/libstdc++.so",
                          NDK_PLATFORMLIB+"/libm.so",
                          "-lGLESv2",
                          "-llog",
                          "-lz"
                          ]

#                          "-lGLESv1_CM",

    settings.dllsyslibs += settings.syslibs

    # Compile flags

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

    if config.buildconfig == "debug":
        commonflags += [ "-O0" ]
    else:
        commonflags += [ "-Os" ]

    # CXX

    cxxflags = commonflags + [ "-fno-rtti", "-Wno-reorder" ]

    settings.CXX = NDK_TOOLSBIN+"/arm-linux-androideabi-g++"
    settings.CXXFLAGS += cxxflags

    # CC

    cflags = commonflags

    settings.CC = NDK_TOOLSBIN+"/arm-linux-androideabi-gcc"
    settings.CFLAGS += cflags

    # Include dirs

    settings.sysincdirs += [
        NDK_PLATFORM_ROOT+"/usr/include",
        NDK_ROOT+"/sources/cxx-stl/system/include" ]

    # AR

    settings.AR = NDK_TOOLSBIN+"/arm-linux-androideabi-ar"
    settings.RANLIB = NDK_TOOLSBIN+"/arm-linux-androideabi-ranlib"

    # Dynamic libs

    settings.scons_make_dynamiclib = scons_make_dynamiclib

    # LINK

    settings.LIBTOOL = "adsf"
    settings.LINK = "afadsf"
