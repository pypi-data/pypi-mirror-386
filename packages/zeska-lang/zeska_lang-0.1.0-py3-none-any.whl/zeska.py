# 🌀 ZeskaLang Interpreter
# Tanglish-based beginner-friendly programming language
# Supports: printu, ifu, elseu, asku, repeatu

def translate_line(line):
    line = line.strip()

    # Ignore empty or comment lines
    if not line or line.startswith("#"):
        return ""

    # --- Zeska Keywords ---
    # printu
    if line.startswith("printu "):
        content = line.replace("printu ", "", 1)
        return f"print({content})"

    # ifu
    if line.startswith("ifu "):
        cond = line.replace("ifu ", "", 1)
        if not cond.endswith(":"):
            cond += ":"
        return f"if {cond}"

    # elseu
    if line.startswith("elseu"):
        return "else:"

    # asku (input)
    if line.startswith("asku "):
        var = line.replace("asku ", "", 1)
        return f"{var} = input('Enter {var}: ')"

    # repeatu (loops)
    if line.startswith("repeatu "):
        # Example: repeatu 5 times:
        parts = line.split()
        if len(parts) >= 3 and parts[2].startswith("times"):
            try:
                n = int(parts[1])
                return f"for _ in range({n}):"
            except:
                return "# invalid repeatu syntax"
        return "# invalid repeatu syntax"

    # Unknown line - return as is
    return line


def run_zeska(filename):
    with open(filename, "r") as f:
        lines = f.readlines()

    indent = 0
    python_lines = []

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        # handle indentation rules
        if line.startswith("ifu ") or line.startswith("repeatu "):
            python_lines.append("    " * indent + translate_line(line))
            indent += 1
        elif line.startswith("elseu"):
            indent -= 1
            python_lines.append("    " * indent + translate_line(line))
            indent += 1
        elif line.startswith("stopu"):
            indent = 0
        else:
            python_lines.append("    " * indent + translate_line(line))

    full_code = "\n".join(python_lines)
    print("=== Zeska running ===")
    print(full_code)
    print("=====================")
    exec(full_code)


# ------------------------------
# Run Zeska directly OR via CLI
# ------------------------------

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: zeska <filename.zeska>")
    else:
        filename = sys.argv[1]
        run_zeska(filename)


# When run directly with Python
if __name__ == "__main__":
    run_zeska("hello.zeska")
