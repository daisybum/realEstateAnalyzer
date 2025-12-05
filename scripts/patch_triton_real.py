import os

file_path = "/home/sanghyun/miniforge3/envs/realEstateAnal/lib/python3.12/site-packages/triton/backends/nvidia/compiler.py"

with open(file_path, "r") as f:
    content = f.read()

old_code = """def sm_arch_from_capability(capability: int):
    # TODO: Handle non-"a" sms
    suffix = "a" if capability >= 90 else ""
    return f"sm_{capability}{suffix}"
"""

new_code = """def sm_arch_from_capability(capability: int):
    # Patch for GB10 (sm_121) -> sm_120a
    if capability == 121:
        return "sm_120a"
    # TODO: Handle non-"a" sms
    suffix = "a" if capability >= 90 else ""
    return f"sm_{capability}{suffix}"
"""

if old_code in content:
    new_content = content.replace(old_code, new_code)
    with open(file_path, "w") as f:
        f.write(new_content)
    print("Successfully patched triton compiler.py")
else:
    if "if capability == 121:" in content:
        print("Already patched.")
    else:
        print("Could not find exact code block to patch. Please check the file manually.")
