def gen_main_tex(title, i):
    with open(f"./problems/problem_{i}/main.tex", "w") as f:
        f.write(f"\\documentclass{{article}}\n")
        f.write(f"\\usepackage{{v-problem}}\n")
        f.write(f"\\vgeometry\n\n")
        f.write(f"\\begin{{document}}\n")
        f.write(f"\\vtitle[\\textsc{{{title}}}]\n\n")
        f.write(f"\\begin{{enumerate}}\\addtocounter{{enumi}}{{{i-1}}}\n")
        f.write(f"\t\\input{{problem.tex}}\n")
        f.write(f"\\end{{enumerate}}\n\n")
        f.write(f"\\end{{document}}\n")
