
import os

print "Import easymake"

############################################################

class Config(object):
    def __init__(self,
                 buildconfig,
                 platform,
                 ):
        self.buildconfig = buildconfig
        self.platform = platform
        print "config=%s, platform=%s" %(buildconfig, platform)


############################################################

class Settings(object):
    def __init__(self, config):

        platform = config.platform
        buildconfig = config.buildconfig

        self.OBJPATH = "obj/%s-%s" % (platform, buildconfig)
        self.LIBPATH = "lib/%s-%s" % (platform, buildconfig)
        self.DLLPATH = "dll/%s-%s" % (platform, buildconfig)
        self.APPPATH = "bin/%s-%s" % (platform, buildconfig)

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
        self.LINKFLAGS = []

        self.srcexts = ['c', 'cpp']

        self.make_appfile = lambda c, s, name: s.APPPATH+"/"+name+".bin"

        self.scons_make_objects = None
        self.scons_make_staticlib = None
        self.scons_make_dynamiclib = None
        self.scons_make_application = None

        # Settings for this platform

        exec('import config_'+config.platform+ ' as _config')
        _config._config(config, self)

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
class NoModule(object):
    def __init__(self):
        pass


#
#
#
class Module(object):
    # _name
    # _srcdirs
    # _incdirs
    # _deps
    # _fulldeps
    def __init__(self, name,
                 srcdirs,
                 incdirs,
                 deps,
                 srcfiles,
                 srcexcludes,
                 incdirs_internal,
                 cxxflags):
        self._name = name

        if (srcfiles != []) and (srcdirs != []):
            raise "Cannot use both srcdirs and srcfiles attributes"

        self._srcdirs = _make_str_array(srcdirs)
        self._incdirs = _make_str_array(incdirs)
        self._srcfiles = _make_str_array(srcfiles)
        self._srcexcludes = _make_str_array(srcexcludes)
        self._incdirs_internal = _make_str_array(incdirs_internal)
        self._cxxflags = _make_str_array(cxxflags)

        # Deps get resolved later
        self._deps = deps

        # For now, keep these as None
        self._fulldeps = None
        self._objects = None
        self._target = None

    #
    def _calcdeps(self):
        if not self._fulldeps is None:
            return

        self._fulldeps = []
        for dep in self._deps:

            # Filter out any dummy modules
            if isinstance(dep, NoModule):
                continue

            if isinstance(dep, str):
                #print "dep is name: %s" % dep
                depmod = allmodules[dep]
            elif isinstance(dep, Module):
                #print "dep is module: %s" % dep
                depmod = dep
            else:
                raise "Unknown module %s" % dep
            depmod._calcdeps()

            # Add any dependencies of depmod.  We always track from
            # right to left, adding on the left.  This keeps a given
            # module to the left of (i.e. before) it's dependencies.

            #print "Recursively adding dependencies of %s" % depmod._name
            for depDep in reversed(depmod._fulldeps):
                if not depDep in self._fulldeps:
                    self._fulldeps = [ depDep ] + self._fulldeps

            # Add depmod itself

            if not depmod in self._fulldeps:
                self._fulldeps = [ depmod ] + self._fulldeps
        #print "Module %s has deps: %s" %(self._name, [a._name for a in self._fulldeps])

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
        globres = []

        for sd in self._srcdirs:
            for e in settings.srcexts:
                globres += env.Glob(sd + "/*."+e)

            srcglob = []
            for g in globres:
                if not str(g) in self._srcexcludes:
                    srcglob += [ g ]

            allsrc += srcglob

        for sf in self._srcfiles:
            if not sf in self._srcexcludes:
                allsrc += env.Glob(sf)

        srcS = [str(s) for s in allsrc]
        #print "Mod %s: src: %s" %(self._name, srcS)

        # Object directory

        objectpath = settings.OBJPATH + "/" + self._name

        # Full include paths for this module

        includepaths = [] + settings.sysincdirs
        #print "Just sys includes: %s" % includepaths
        for d in self._fulldeps:
            #print " Dep %s has includes: %s" % (d._name, d._incdirs)
            includepaths += d._incdirs
        includepaths += self._incdirs
        includepaths += self._incdirs_internal
        #print "Full includes: %s" % includepaths

        # Flags

        flags = [] + settings.CXXFLAGS
        for d in self._fulldeps:
            flags += d._cxxflags
        flags += self._cxxflags

        # Create the rules

        objects = []
        for src in allsrc:
            s = str(src)
            sbase = os.path.basename(s)
            (objname, ext) = os.path.splitext(sbase)

            obj=objectpath+"/"+objname
            #print "Object: %s source: %s" % (obj, s)

            objects += env.Object(source=s,
                                  target=obj,
                                  CPPPATH=includepaths,
                                  CXXFLAGS=flags)

        self._objects = objects
        return objects

    def _definescons(self, env, config, settings):
        if not self._target is None:
            return

        # Make sure all deps targets are created

        for d in self._fulldeps:
            d._definescons(env, config, settings)

        # Call subclass

        self._target = self._do_definescons(env, config, settings)

        # Set alias for the Module name

        env.Alias(self._name, self._target)


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
                 incdirs_internal = [],
                 cxxflags = []):
        super(Library, self).__init__(name,
                                      srcdirs,
                                      incdirs,
                                      deps,
                                      srcfiles,
                                      srcexcludes,
                                      incdirs_internal,
                                      cxxflags)
        if name in libs:
            print "Library %s already defined" % name
        libs[name] = self

    #
    def _do_definescons(self, env, config, settings):

        # Make sure objects have been defined for this module

        objects = self._defineobjects(env, config, settings)

        # Custom static lib creation?

        if not settings.scons_make_staticlib is None:
            fn = settings.scons_make_staticlib
            return fn(mod, env, config, settings)

        # Not much to do for static libs

        libfile = settings.LIBPATH+"/"+self._name
        target = env.StaticLibrary(target=libfile,
                                         source=objects)

        return target

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
                 incdirs_internal = [],
                 cxxflags = []):
        super(DynamicLibrary, self).__init__(name,
                                             srcdirs,
                                             incdirs,
                                             deps,
                                             srcfiles,
                                             srcexcludes,
                                             incdirs_internal,
                                             cxxflags)
        if name in dlls:
            print "DynamicLibrary %s already defined" % name
        dlls[name] = self

    def _do_definescons(self, env, config, settings):

        # Get object list

        objects = self._defineobjects(env, config, settings)

        # Platform-specific version?

        if not settings.scons_make_dynamiclib is None:
            fn = settings.scons_make_dynamiclib
            return fn(self, env, config, settings)

        # Standard version.  Get all lib requirements

        deplibs = []
        for d in self._fulldeps:
            deplibs += d._target
        deplibs += settings.dllsyslibs

        dllout = settings.DLLPATH + "/lib" + self._name + ".so"
        syslibpaths = settings.syslibpaths

        return env.SharedLibrary(target = dllout,
                                 source = objects,
                                 LIBS = deplibs,
                                 LIBPATH = syslibpaths)

############################################################

#
#
#
class Application(Module):

    def __init__(self, name,
                 srcdirs=[],
                 incdirs=[],
                 deps=[],
                 srcfiles = [],
                 srcexcludes = [],
                 incdirs_internal = [],
                 cxxflags = [],
                 cwd = ".",
                 args = []):
        super(Application, self).__init__(name,
                                          srcdirs,
                                          incdirs,
                                          deps,
                                          srcfiles,
                                          srcexcludes,
                                          incdirs_internal,
                                          cxxflags)

        self._cwd = cwd
        self._args = args

        if name in apps:
            print "Application %s already defined" % name
        apps[name] = self

    def _do_definescons(self, env, config, settings):

        # Get object list

        objects = self._defineobjects(env, config, settings)

        # Platform-specific version?

        if not settings.scons_make_application is None:
            fn = settings.scons_make_application
            return fn(self, env, config, settings)

        # Standard version.  Get all lib requirements

        deplibs = []
        for d in self._fulldeps:
            deplibs += d._target
        deplibs += settings.syslibs

        appout = settings.make_appfile(config, settings, self._name)
        syslibpaths = settings.syslibpaths

        prog = env.Program(target = appout,
                           source = objects,
                           LIBS = deplibs,
                           LIBPATH = syslibpaths)

        # Define '<name>_run' as a secondary alias

        cmd = ""
        if self._cwd != ".":
            cmd += "cd "+self._cwd+" && "
        cmd += os.path.abspath(str(prog[0]))
        cmd += " ".join(self._args)

        run = env.AlwaysBuild(env.Alias(self._name+"_run", prog, cmd))

        return prog

############################################################

class ExternalCommand(Module):
    def __init__(self, name, output,
                 command,
                 deps=[],
                 srcfiles=[],
                 ):
        super(ExternalCommand, self).__init__(name,
                                              [],
                                              [],
                                              deps,
                                              [],
                                              [],
                                              [],
                                              [])
        self._cmdsrc = _make_str_array(srcfiles)
        self._cmd = command
        self._output = _make_str_array(output)

        externalcommands[name] = self

    def _do_definescons(self, env, config, settings):

        # Require ALL dependency targets to be built before running
        # the command

        mydeps = []
        for d in self._fulldeps:
            #print "%s" % d._name
            mydeps += d._target

        #print "Command %s deps: %s" % (self._name, [str(i) for i in mydeps])

        if len(self._output) == 0:
            target = env.AlwaysBuild(env.Alias(self._name+"always", self._cmdsrc+mydeps, self._cmd))
        else:
            target = env.Command(self._output, self._cmdsrc+mydeps, self._cmd)

        env.Depends(target, mydeps)
        return target

############################################################

def add_default(env, mod):
    env.Default(mod._target)

############################################################

libs = {}
dlls = {}
apps = {}
externalcommands = {}
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
    #print "setting env['%s'] = %s" % (name, value)
    env[name] = value

def build(env, config, settings = None):

    if settings is None:
        settings = Settings(config)

    # Set up the env

    setenv(env, 'CXX', settings.CXX)
    setenv(env, 'CXXFLAGS', settings.CXXFLAGS)
    setenv(env, 'CC', settings.CC)
    setenv(env, 'CFLAGS', settings.CFLAGS)
    setenv(env, 'AR', settings.AR)
    setenv(env, 'RANLIB', settings.RANLIB)
    setenv(env, 'LIBTOOL', settings.LIBTOOL)
    setenv(env, 'LINK', settings.LINK)
    setenv(env, 'LINKFLAGS', settings.LINKFLAGS)

    # List of all modules

    for m in libs:
        allmodules[m] = libs[m]
    for m in dlls:
        allmodules[m] = dlls[m]
    for m in apps:
        allmodules[m] = apps[m]
    for m in externalcommands:
        allmodules[m] = externalcommands[m]

    # Calculate full dependencies

    for m in allmodules:
        mod = allmodules[m]
        mod._calcdeps()

    # Define Scons rules

    for m in allmodules:
        mod = allmodules[m]
        mod._definescons(env, config, settings)

