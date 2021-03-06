
print "Importing macosx Config"

def _config(config, settings):
    commonCFLAGS = ['-arch', 'i386', '-DMACOSX', '-fPIC', '-g']
    settings.CXXFLAGS += commonCFLAGS
    settings.CFLAGS += commonCFLAGS

    settings.LINKFLAGS += ['-arch', 'i386', '-g']

    settings.DLLFLAGS += ['-shared']

    settings.srcexts += ['mm']

    def make_appfile_macosx(config, settings, name):
        f = settings.APPPATH+"/"
        #f += name+".app/Contents/MacOS/"
        f += name+".bin"
        return f

    settings.make_appfile = make_appfile_macosx

    # Set the name of the build config in XCode

    if config.buildconfig == "debug":
        settings._xcodeconfig="Debug"
    elif config.buildconfig == "release":
        settings._xcodeconfig="Release"
    else:
        throw ("Don't understand build config '%s'" % config.buildconfig)

