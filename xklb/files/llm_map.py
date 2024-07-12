import shlex, subprocess
from pathlib import Path
from shutil import which

from xklb import usage
from xklb.createdb import fs_add
from xklb.utils import arggroups, argparse_utils, path_utils
from xklb.utils.arg_utils import gen_paths


def parse_args():
    parser = argparse_utils.ArgumentParser(usage=usage.llm_map)
    parser.add_argument("--prompt", '-q', "--custom-prompt", help="Use a custom prompt")
    parser.add_argument(
        "--text", type=int, nargs="?", const=1500, help="Pass text file contents of each file to the LLM"
    )
    parser.add_argument("--images", action="store_true", help="Treat paths as image files")
    parser.add_argument("--rename", action="store_true", help="Use rename prompt")
    parser.add_argument("--output", help="The output CSV file to save the results.")
    arggroups.debug(parser)

    parser.add_argument(
        '--model',
        '-m',
        "--llamafile",
        help="The path to the llamafile to run. If llamafile is in your PATH then you can also specify a GGUF file.",
    )
    parser.add_argument('--image-model', '--mmproj', help="The path to the LLaVA vision GGUF model.")
    parser.add_argument(
        "--llama-args", "--custom-args", type=shlex.split, default=[], help="Use custom llamafile arguments"
    )

    arggroups.paths_or_stdin(parser)
    args = parser.parse_args()
    arggroups.args_post(args, parser)

    if args.prompt is None:
        if args.rename:
            args.prompt = "Suggest a clean filename following Chicago Manual of Style. When possible, include the year written and any authors names. Use spaces, commas, dashes, and underscores appropriately. Only give me a filename and nothing else. {name}"
            args.llama_args += ["-n", "18"]
            if args.output is None:
                args.output = f"llm_map_renames.csv"
        else:
            raise NotImplementedError

    args.exe = which('llamafile')
    if args.exe:
        args.llama_args += ['-m', args.model]
    else:
        args.exe = args.model

    if args.image_model:
        args.llama_args += ['--mmproj', args.image_model]

    if args.output is None:
        args.output = f"llm_map_{args.prompt}.csv"
    args.output = path_utils.clean_path(args.output.encode())
    return args


def run_llama_with_prompt(args, prompt):
    try:
        cmd = [args.exe, "--silent-prompt", *args.llama_args, "-p", prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running {cmd} for {prompt}: {e.stderr}")
        return None


def llm_map():
    args = parse_args()

    import pandas as pd

    results = []
    for path in gen_paths(args):
        prompt = args.prompt

        replacements = {
            '{path}': "Existing path: " + path,
            '{abspath}': "Existing path: " + str(Path(path).absolute()),
            '{name}': "Existing filename: " + Path(path).name,
            '{stem}': "Existing filename: " + Path(path).stem,
        }
        for k, v in replacements.items():
            prompt.replace(k, '\n' + v + '\n')

        if args.images:
            args.llama_args += ["--image", str(Path(path).absolute())]
        elif args.text:
            file_contents = fs_add.munge_book_tags_fast(path)
            if file_contents:
                file_contents = file_contents.get("tags")
            if file_contents:
                prompt += f"\nFile contents: {file_contents[:args.text].replace(';', '\n')}\n"

        output = run_llama_with_prompt(args, prompt)
        if output is not None:
            if args.rename:
                output = path_utils.clean_path(bytes(Path(path).with_name(output)))

                ext = Path(path).suffix
                if not output.endswith(ext):
                    output += ext

            results.append([path, output])

    df = pd.DataFrame(results, columns=["path", "output"])
    df.to_csv(args.output, index=False)
    print(f"Saved results to {args.output}")
