import os

cookie_dir = "KumsalTR/cookies"
if os.path.exists(cookie_dir):
    for file in os.listdir(cookie_dir):
        if file.endswith(".txt"):
            path = os.path.join(cookie_dir, file)
            print(f"Fixing {path}...")
            with open(path, "r", encoding="utf-8", errors="ignore") as fr:
                content = fr.read()
            
            lines = []
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    lines.append(line)
                    continue
                
                parts = line.split(None, 6)
                if len(parts) >= 7:
                    lines.append("\t".join(parts))
                else:
                    lines.append(line)
            
            with open(path, "w", encoding="utf-8", newline="\n") as fw:
                fw.write("\n".join(lines) + "\n")
            print(f"Done fixing {path}.")
else:
    print(f"Directory {cookie_dir} not found.")
