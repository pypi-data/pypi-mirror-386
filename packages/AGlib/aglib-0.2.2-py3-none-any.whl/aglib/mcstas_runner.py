"""
Helper module to run McStas simulations on Windows from
within Jupyter Notebook.
"""

import os
import shutil
from subprocess import run
from IPython.display import display, HTML
from IPython import get_ipython  

ROOT = os.path.realpath(os.path.dirname(__file__))

def set_mcstas_27():
    """
    Set McStas environment variables for windows default location of version 2.7.2
    For use in jupyter notebooks.
    """
    ipython = get_ipython()
    # Setting environment for McStas execution, see mcstas/bin/mccodeenv.bat
    PATH = os.environ['PATH']
    ipython.magic('set_env PATH=C:\\mcstas-2.7.2\\bin;C:\\mcstas-2.7.2\\miniconda3;C:\\mcstas-2.7.2\\miniconda3\\Scripts\\;C:\\mcstas-2.7.2\\miniconda3\\Library\\bin;C:\\mcstas-2.7.2\\miniconda3\\Library\\mingw-w64\\bin;c:\\strawberry\\perl\\bin;c:\\Program Files\\Microsoft MPI\\Bin;%s'%PATH)
    # McStas related:
    ipython.magic('set_env MCSTAS=C:\\mcstas-2.7.2\\lib')
    ipython.magic('set_env MCSTAS_TOOLS=C:\\mcstas-2.7.2\\lib\\tools\\Perl\\')
    ipython.magic('set_env MCSTAS_CC=gcc')
    ipython.magic('set_env MCSTAS_FORMAT=')
    ipython.magic('set_env MCSTAS_CFLAGS=" -std=c99 -g -O2 -lm"')

def set_mcstas_3(subversion="5.24"):
    """
    Set McStas environment variables for windows default location of version 3.x
    For use in jupyter notebooks.
    """
    ipython = get_ipython()
    # Setting environment for McStas execution, see mcstas/bin/mccodeenv.bat
    PATH = os.environ['PATH']
    ipython.magic(f'set_env PATH=C:\\mcstas-3.{subversion}\\bin;C:\\mcstas-3.{subversion}\\miniconda3;C:\\mcstas-3.{subversion}\\miniconda3\\Scripts\\;C:\\mcstas-3.{subversion}\\miniconda3\\Library\\bin;C:\\mcstas-3.{subversion}\\miniconda3\\Library\\mingw-w64\\bin;c:\\strawberry\\perl\\bin;c:\\Program Files\\Microsoft MPI\\Bin;%s'%PATH)
    # McStas related:
    ipython.magic(f'set_env MCSTAS=C:\\mcstas-3.{subversion}\\lib')
    ipython.magic(f'set_env MCSTAS_TOOLS=C:\\mcstas-3.{subversion}\\lib\\tools\\Perl\\')
    ipython.magic('set_env MCSTAS_CC=gcc')
    ipython.magic('set_env MCSTAS_FORMAT=')
    ipython.magic('set_env MCSTAS_CFLAGS=" -std=c99 -g -O2 -lm"')

def set_mcstas_34():
    """
    Set McStas environment variables for windows default location of version 2.7
    For use in jupyter notebooks.
    """
    return set_mcstas_3(subversion="4")


def compile_model(model_name, call_path='.'):
    """
    Compile a McStas model.
    """
    res=run(f'mcstas -o {model_name}.c {model_name}.instr', shell=True, capture_output=True, 
            cwd=call_path)
    print(res.stdout.decode('utf-8')+"\n\x1b[31m"+res.stderr.decode('utf-8')+"\x1b[0m")
    res=run(f'mpicc -std=c99 -O2 -o {model_name}.exe {model_name}.c -lm −DUSE_MPI', shell=True, capture_output=True,
            cwd=call_path)
    print(res.stdout.decode('utf-8')+"\n\x1b[31m"+res.stderr.decode('utf-8')+"\x1b[0m")
    os.chdir(ROOT)

NUM_POCS = 14

def run_model(model_name, output_name, options="", n="1e7", call_path='.', gravity=False):
    """
    Run a McStas model to given output path and zip the resulting data.
    """
    # clear output path, run model and compress results
    output_name_full = os.path.join('results', output_name)
    output_name_rel = os.path.join(os.path.relpath('results', call_path), output_name)
    try:
        shutil.rmtree(output_name_full)
    except FileNotFoundError:  
        pass

    print(f"Run {model_name} -> {output_name}")
    add_options = ""
    if gravity:
        add_options+=" --gravitation"
    res=run(f'mpiexec -n {NUM_POCS} {model_name}.exe -n {n}{add_options} -d {output_name_rel} {options}', 
            shell=True, capture_output=True, cwd=call_path)
    os.chdir(ROOT)
    
    display(HTML(
        "<div style='font-size: 6pt; white-space: pre; max-height: 15em; overflow: auto; line-height: 1.2em;'>"+
        res.stdout.decode('utf-8')+
        "<br /><div style='color: red;'>"+res.stderr.decode('utf-8')+"</div>"+
        "</div>"
    ))
        
    try:
        os.remove(output_name_full+'.zip')
    except FileNotFoundError:  
        pass
    shutil.make_archive(output_name_full, 'zip', base_dir=output_name, root_dir='results')
    try:
        shutil.rmtree(output_name_full)
    except (FileNotFoundError,PermissionError):  
        pass
    
    os.chdir(ROOT)