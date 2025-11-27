from SCons.Script import Import

Import("env")

# Force the linker to use Hard Float to match the objects
env.Append(LINKFLAGS=[
    "-mfloat-abi=hard", 
    "-mfpu=fpv4-sp-d16"
])