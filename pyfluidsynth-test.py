from sys import platform
on_linux = False
on_macos = False
if platform == "linux" or platform == "linux2":
    on_linux = True
elif platform == "darwin":
    on_macos = True
elif platform == "win32":
    pass  # Windows is not supported


COLORS = {"red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m", "blue": "\033[34m", "bold": "\033[1m", "end": "\033[0m"}

if on_macos:
    SOURCE_FS_PATH = "/opt/homebrew/Cellar/fluid-synth"
    SOURCE_FS = "bin/fluidsynth"
    SOUNDFONT_DIR = "/share/soundfonts"
    TARGET_LIB_PATH = "/usr/local/lib/libfluidsynth.dylib"
    SOURCE_LIB_EXT = ".dylib"
elif on_linux:
    SOURCE_FS_PATH = "/usr/bin"
    SOURCE_FS = "fluidsynth"
    SOUNDFONT_DIR = "/usr/share/soundfonts"
    TARGET_LIB_PATH = "/usr/lib/libfluidsynth.so"
    SOURCE_LIB_EXT = ".so"

DEFAULT_SOUND_FONT = "default.sf2"


def cprint(msg, color=None):
    if color is None:
        print(msg)
    print(f"{COLORS[color]}{msg}{COLORS['end']}")


def find_fs():
    dirs = list()
    if on_macos:
        if os.path.exists(SOURCE_FS_PATH) and os.path.isdir(SOURCE_FS_PATH):
            # dirs = os.listdir(SOURCE_FS_PATH)
            prob_dirs = os.listdir(SOURCE_FS_PATH)
            for d in prob_dirs:
                fpath = f"{SOURCE_FS_PATH}/{d}/{SOURCE_FS}"
                if os.path.exists(fpath) and os.path.isfile(fpath):
                    dirs.append(f"{SOURCE_FS_PATH}/{d}")
    if on_linux:
        fpath = f"{SOURCE_FS_PATH}/{SOURCE_FS}"
        if os.path.exists(fpath) and os.path.isfile(fpath):
            dirs.append(SOURCE_FS_PATH)
    return dirs


def find_soundfont(fluid_synth_dirs):
    dirs = list()
    if on_macos:
        for d in fluid_synth_dirs:
            sf_dir = f"{d}{SOUNDFONT_DIR}"
            dirs.append(sf_dir)
    if on_linux:
        dirs.append(SOUNDFONT_DIR)
    return dirs


def find_fs_lib(fluidsynth_dirs):
    dirs = list()
    for d in fluidsynth_dirs:
        src_lib_dir = f"{d}/lib"
        files = os.listdir(src_lib_dir)
        for f in files:
            lib_path = f"{src_lib_dir}/{f}"
            if os.path.isfile(lib_path) and not os.path.islink(lib_path) and SOURCE_LIB_EXT in lib_path:
                dirs.append(lib_path)
    return dirs


def find_target_libs(target_lib_path):
    libs = list()
    if os.path.exists(target_lib_path) and os.path.isfile(target_lib_path):
        libs.append(target_lib_path)
    path, name = os.path.split(target_lib_path)
    for f in os.listdir(path):
        if f.startswith(name):
            libs.append(f"{path}/{f}")
    return libs


def fs_version():
    from ctypes import c_int
    maj_ver = c_int()
    min_ver = c_int()
    mic_ver = c_int()
    fluidsynth.fluid_version(maj_ver, min_ver, mic_ver)
    return f"{maj_ver.value}.{min_ver.value}.{mic_ver.value}"


def pfs_version():
    import subprocess
    sp = subprocess.run(["pip", "freeze"], capture_output=True)
    strs = sp.stdout.decode("utf-8").split('\n')
    version = "None"
    for s in strs:
        if "pyFluidSynth" in s:
            _, version = s.split("==")
    return version


def play_sound(sf_path):
    def play_note(midi_note, duration):
        fs.noteon(0, midi_note, 127)
        time.sleep(duration)
        fs.noteoff(0, midi_note)

    def play_chord(midi_notes, duration):
        for n in midi_notes:
            fs.noteon(0, n, 127)
        time.sleep(duration)
        for n in midi_notes:
            fs.noteoff(0, n)

    import time

    print("Creating Synth object...")
    fs = fluidsynth.Synth(samplerate=44100.0)

    if not sf_path:
        cprint("Soundfont is not provided, exiting...", "red")
        return

    print(f"Loading soundfont: {sf_path}...")
    sfid = fs.sfload(sf_path)

    print("Selecting channel 0, bank 0, preset 0...")
    fs.program_select(0, sfid, 0, 0)

    cprint("Playing the opening from 'Also sprach Zarathustra'...", "blue")
    fs.start()
    time.sleep(1.0)

    quarter_note = 0.5

    play_note(48, quarter_note * 2.0)  # C
    play_note(55, quarter_note * 2.0)  # G
    play_note(60, quarter_note * 3.5)  # C
    time.sleep(quarter_note / 4.0)

    play_chord([48, 52, 55, 67, 72, 76], quarter_note / 4.0)  # C E G G C E
    time.sleep(quarter_note / 4.0)

    play_chord([48, 51, 55, 67, 72, 75], quarter_note * 3.75)  # C Eb G  G C Eb

    time.sleep(0.25)

    print("Deleting the Synth interface...")
    fs.delete()


import os

source_libs = list()
sf_path = None

cprint("FluidSynth and pyFluidSynth installation test", "blue")

if not on_linux and not on_macos:
    cprint("OS other than Linux or macOS is not supported", "red")
    exit(1)

print("If both are installed correctly, you should hear sound in the end of the test.")
print()

print("Checking FluidSynth installation...")
fs_dirs = find_fs()
if fs_dirs:
    for d in fs_dirs:
        cprint(f"FluidSynth found: {d}/{SOURCE_FS}", "green")
else:
    if on_macos:
        cprint("FluidSynth is NOT found. Install with homebrew:", "red")
        print("homebrew install fluidsynth")
    if on_linux:
        cprint(f"FluidSynth is NOT found in {SOURCE_FS_PATH}.", "red")
print()

if fs_dirs:
    print("Checking FluidSynth default soundfont...")
    sf_dirs = find_soundfont(fs_dirs)
    for d in sf_dirs:
        if os.path.exists(d) and os.path.isdir(d):
            sf_path = f"{d}/{DEFAULT_SOUND_FONT}"
            if os.path.exists(sf_path):
                cprint(f"Default soundfont found: {sf_path}", "green")
            else:
                cprint(f"Default soundfont {DEFAULT_SOUND_FONT} NOT found in: {d}. Create a symlink or copy the SF2 file to the folder.", "yellow")
        else:
            cprint(f"Soundfont directory is NOT found: {d}. Create:", "yellow")
            if on_macos:
                print(f"mkdir -p {d}")
            if on_linux:
                print(f"sudo mkdir -p {d}")
    print()

    print("Checking FluidSynth library installation...")
    if on_macos:
        source_libs = find_fs_lib(fs_dirs)
        if source_libs:
            for d in source_libs:
                cprint(f"fluidsynth library found: {d}", "green")
        else:
            cprint("fluidsynth library is NOT found.", "red")

        if os.path.exists(TARGET_LIB_PATH) and os.path.isfile(TARGET_LIB_PATH):
            if os.path.islink(TARGET_LIB_PATH):
                lib_path = os.readlink(TARGET_LIB_PATH)
                cprint(f"Symlink to fluidsynth library found: {TARGET_LIB_PATH} -> {lib_path}", "green")
                if lib_path != source_libs[-1]:
                    cprint(f"the link does not seem to point to the latest library: {source_libs[-1]}", "yellow")
            else:
                cprint(f"fluidsynth library found: {TARGET_LIB_PATH}. It is better to create a symlink than to copy the lib.", "yellow")
        else:
            cprint(f"fluidsynth library NOT found. On macOS, the library needs to be in {TARGET_LIB_PATH}", "red")
            print("Create a symlink:")
            print(f"sudo ln -sf {source_libs[-1]} {TARGET_LIB_PATH}")
    if on_linux:
        target_libs = find_target_libs(TARGET_LIB_PATH)
        if target_libs:
            for lib in target_libs:
                if os.path.islink(lib):
                    lib_path = os.readlink(lib)
                    cprint(f"Symlink to fluidsynth library found: {lib} -> {lib_path}", "green")
                else:
                    cprint(f"fluidsynth library found: {lib}.", "green")
        else:
            cprint(f"fluidsynth library NOT found. On Linux, the library needs to be {TARGET_LIB_PATH}.x.y", "red")

print()

print("Checking pyFluidSynth installation...")
pyfs_found = True
try:
    import fluidsynth
except ModuleNotFoundError:
    pyfs_found = False
    cprint("pyFluidSynth module is not found. Try:", "red")
    print("pip install pyfluidsynth")

if pyfs_found:
    cprint(f"Per PIP, pyFluidSynth module installed: {pfs_version()}. Self-reported API version: {fluidsynth.api_version}", "blue")
    cprint(f"Per pyFluidSynth, FluidSynth version is {fs_version()}", "blue")
    print()

    print("Checking the playback...")
    play_sound(sf_path)
    print()
