# CODESYS scripting API script (IronPython 2.7, runs inside CODESYS --noUI mode)
# Purpose: open a password-protected project and export all POU source code
#          as a PLCopen XML file for offline analysis.
#
# STATIC + ENV-DRIVEN: /codesySpy passes its parameters through the *environment*
# (inherited by this CODESYS child process), so nothing secret is written to disk
# and there is no per-run generated copy to scrub:
#   CODESYS_PROJECT     full path to the .project file        (from -fn)
#   CODESYS_PW          the project password                  (from -pw)
#   CODESYS_EXPORT_XML  where to write the PLCopen XML
#
# Run via:  run_export.bat (invoked with `cmd /c` so --profile quoting survives).
# Output:   the PLCopen XML at CODESYS_EXPORT_XML (all POUs, declarations as plaintext).

import os

export_path  = os.environ["CODESYS_EXPORT_XML"]
project_path = os.environ["CODESYS_PROJECT"]
password     = os.environ["CODESYS_PW"]

proj = None
try:
    # 'projects' is the CODESYS scripting API global object
    proj = projects.open(project_path, password=password)
    print("Project opened: " + proj.path)

    # Recursively collect every object in the project tree
    all_objects = []
    def collect(obj):
        all_objects.append(obj)
        for child in obj.get_children(False):
            collect(child)

    for obj in proj.get_children(False):
        collect(obj)

    print("Total objects found: " + str(len(all_objects)))

    # Exclude device objects: their PLCopen export needs the device description
    # installed, and a single missing devdesc (e.g. 'EP2339_0022') aborts the
    # whole export. We only want code (POUs/GVLs/DUTs/...), so devices are dropped.
    def is_device(o):
        try:
            return bool(o.is_device)
        except:
            return False
    code_objects = [o for o in all_objects if not is_device(o)]
    print("Code objects (devices excluded): " + str(len(code_objects)))

    # recursive=False: the list is already fully flattened, so we must NOT let
    # CODESYS re-expand children (recursive=True would re-pull device children and
    # re-trigger the missing-devdesc error). declarations_as_plaintext=True adds
    # the <InterfaceAsPlainText> sections that are easier to parse later.
    try:
        proj.export_xml(code_objects, path=export_path, recursive=False,
                        declarations_as_plaintext=True)
        print("Export done: " + export_path)
    except Exception as bulk_err:
        # Resilient fallback: probe each object alone, keep the ones that export
        # cleanly, then write the combined file once. One bad object can't lose
        # the whole program.
        print("Bulk export failed (" + str(bulk_err) + "); retrying per-object...")
        probe = export_path + ".probe.tmp"
        good, skipped = [], []
        for o in code_objects:
            try:
                proj.export_xml([o], path=probe, recursive=False,
                                declarations_as_plaintext=True)
                good.append(o)
            except Exception as one_err:
                skipped.append(str(one_err))
        try:
            os.remove(probe)
        except:
            pass
        proj.export_xml(good, path=export_path, recursive=False,
                        declarations_as_plaintext=True)
        print("Export done (per-object): " + export_path)
        print("Exported " + str(len(good)) + ", skipped " + str(len(skipped)))

except Exception as e:
    print("ERROR: " + str(e))
    import traceback
    traceback.print_exc()
finally:
    if proj is not None:
        try:
            proj.close()
        except:
            pass
