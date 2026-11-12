# TI-Nspire Study Tools

Free study programs for the **TI-Nspire CX II** calculator, plus a Mac tool that puts your notes on the calculator.

- **Step-by-step solvers** for physics and Algebra 2. You type the numbers from the problem and the calculator shows the work the way you would write it on paper, then the answer.
- **Nspire Convert**, a Mac app and script that turns a PDF, Word file or photo into pages you can read on the calculator screen.

Made by a high school junior, with help from Claude. Everything here is free to use and change.

> Use these to study and to check your work. Ask your teacher before using a program on a quiz or test.

## The programs

| File | What it does |
|---|---|
| `programs/physolve.tns` | **Forces.** Weight and mass, up-and-down forces, side-to-side forces, friction, stacked blocks, acceleration. Draws the free-body diagram, writes Fnet = ma, and solves. Uses g = 10. |
| `programs/physolve_2d.tns` | **2-D motion.** Angled and horizontal launches with an x / y table, adding vectors (N, S, E, W), averaging trials, and a helper for data and regressions. Uses g = 10. |
| `programs/algsolve.tns` | **Polynomials.** Standard form, degree, leading coefficient, end behavior, and adding, subtracting and multiplying (FOIL and the box method). You type the problem the way it looks on the paper. |
| `programs/algsolve_topic2.tns` | **Quadratics and complex numbers.** Solving by factoring, completing the square and the quadratic formula; vertex form and graphs; square roots with i; complex numbers; a parabola and a line together. Answers are exact: fractions and simplest radical form. |

Each `.tns` file has a matching `.py` file with the same code, so you can read it or change it.

In every program: the arrow keys move, **enter** picks, **esc** goes back one screen, and **home** or **menu** quits. Each tool remembers the last numbers you typed.

## Put a program on your calculator

You need a TI-Nspire CX II (the Python kind) and the free **TI-Nspire CX Student Software** or **TI-Nspire Computer Link** on your computer.

1. Download the `.tns` file you want (click the file on GitHub, then the download button).
2. Plug the calculator into your computer and open the TI software.
3. Open the `.tns` file in the software, then choose **File › Save to Handheld**. (Or drag the file onto your calculator in the Connected Handhelds panel.)
4. On the calculator, open the document from **My Documents**. It starts by itself; if not, press **ctrl + R**.

## Nspire Convert (Mac)

Turns documents into pictures sized for the calculator screen (320×216) and packs them into one `.tns` file with a small page viewer.

Works with PDF, Word, RTF, text, HTML, EPUB, PowerPoint (text only), Excel and photos.

**Quick way:** double-click `converter/Convert for TI-Nspire.command`, choose your documents, and pick a look:
- **Big text** re-lays out the words in large type. Best for notes and readings.
- **Original look** keeps handwriting, equations and graphs.

The first run spends about a minute setting up Python tools. Add `--tns` on the command line to get a calculator file too:

```bash
cd converter
python3 -m venv .venv && .venv/bin/pip install pymupdf pillow
.venv/bin/python nspire_convert.py notes.pdf --tns
```

**Mac app:** run `converter/app_source/build_app.sh` to build *Nspire Convert.app* (needs Xcode's command line tools, Apple Silicon). Drop documents on its window.

On the calculator, the page viewer uses **Down / Up** to scroll, **Enter** to zoom, and **Tab / Backspace** for the next or previous page.

## Change a program or write your own

1. Edit the `.py` file in `programs/`.
2. Check it on your computer. The `tests/` folder has stand-ins for the calculator's `ti_draw` and `ti_system` modules, so the programs run without a calculator:
   ```bash
   cd tests
   python3 algsolve_run.py ../programs/algsolve.py      # scripted key presses, prints each screen
   python3 algsolve_fuzz.py ../programs/algsolve.py     # thousands of random problems checked against plain math
   python3 physolve_run.py ../programs/physolve.py
   ```
3. Turn it into a calculator file with Luna:
   ```bash
   converter/app_source/luna/luna programs/algsolve.py programs/algsolve.tns
   ```

The included `luna` is built for Apple Silicon Macs. On another computer, build it from the [Luna project](https://github.com/ndless-nspire/Luna).

## Ideas and problems

Found a wrong answer, or want a program for another topic? Open an issue on GitHub and include the problem you typed.

## Credits and license

- The programs and the converter are under the [MIT License](LICENSE).
- `.tns` files are made with [Luna](https://github.com/ndless-nspire/Luna) by Olivier Armand, under the Mozilla Public License 1.1. Its license is in `converter/app_source/luna/`.
- TI-Nspire is a trademark of Texas Instruments. This project is not connected to Texas Instruments.
