<h2 align="center"> Nest - A flexible tool for building and sharing deep learning modules </h2>

[![](https://img.shields.io/badge/core-0.1-blue.svg)](https://github.com/ZhouYanzhao/Nest)
[![](https://img.shields.io/badge/pytorch-0.1-red.svg)](https://github.com/ZhouYanzhao/Nest/tree/pytorch)
[![](https://img.shields.io/badge/mxnet-scheduled-green.svg)](#)
[![](https://img.shields.io/badge/tensorflow-scheduled-green.svg)](#)

Nest is a flexible deep learning module manager, which aims at encouraging code reuse and sharing. It ships with a bunch of useful features, such as CLI based module management, runtime checking,  and experimental task runner, etc.  You can integrate Nest with PyTorch, Tensorflow, MXNet, or any deep learning framework you like that provides a python interface. 

Moreover, a set of [Pytorch-backend Nest modules](https://github.com/ZhouYanzhao/Nest/tree/pytorch), e.g., network trainer, data loader, optimizer, dataset, visdom logging, are already provided. More modules and framework support will be added later. 

---

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
    - [Create your first Nest module](#create-your-first-nest-module)
    - [Use your Nest module in Python](#use-your-nest-module-in-python)
    - [Debug your Nest modules](#debug-your-nest-modules)
    - [Install Nest modules from local path](#install-nest-modules-from-local-path)
    - [Install Nest modules from URL](#install-nest-modules-from-url)
    - [Uninstall Nest modules](#uninstall-nest-modules)
    - [Version control Nest modules](#version-control-nest-modules)
    - [Use Nest to manage your experiments](#use-nest-to-manage-your-experiments)
- [Contact](#contact)
- [Issues](#issues)
- [Contribution](#contribution)
- [License](#license)

## Prerequisites
* System (tested on Ubuntu 14.04LTS, Win10, and MacOS *High Sierra*)
* [Python](https://www.python.org) >= 3.5
* [Git](https://git-scm.com)

## Installation
```bash
# directly install via pip
pip install git+https://github.com/ZhouYanzhao/Nest.git

# manually download and install
git clone https://github.com/ZhouYanzhao/Nest.git
pip install ./Nest
```

## Basic Usage
> The official website and documentation are under construction.

### Create your first Nest module
1. Create "hello.py" under your current path with the following content:

    ```python
    from nest import register

    @register(author='Yanzhao', version='1.0.0')
    def hello_nest(name: str) -> str:
        """My first Nest module!"""

        return 'Hello ' + name
    ```

    > Note that the type of module parameters and return values must be clearly defined. This helps the user to better understand the module, and at runtime Nest automatically checks whether each module receives and outputs as expected, thus helping you to identify potential bugs earlier.

2. Execute the following command in your shell to verify the module:

    ```bash
    $ nest module list -v
    # Output:
    # 
    # 1 Nest module found.
    # [0] main.hello_nest (1.0.0) by "Yanzhao":
    #     hello_nest(
    #         name:str) -> str

    # Documentation:
    #     My first Nest module!
    #     author: Yanzhao
    #     module_path: /Users/yanzhao/Workspace/Nest.doc
    #     version: 1.0.0 
    ```

    > Note that all modules under current path are registered under the "**main**" namespace.

    > With the CLI tool, you can easily manage Nest modules. Execute `nest -h` for more details. 

3. That's it. You just created a simple Nest module!


### Use your Nest module in Python
1. Open an interactive python interpreter under the same path of "hello.py" and run following commands:

    ```python
    >>> from nest import modules
    >>> print(modules.hello_nest) # access the module
    # Output:
    # 
    # hello_nest(
    # name:str) -> str
    >>> print(modules['*_nes?']) # wildcard search
    # Output:
    # 
    # hello_nest(
    # name:str) -> str
    >>> print(modules['r/main.\w+_nest']) # regex search
    # Output:
    # 
    # hello_nest(
    # name:str) -> str
    >>> modules.hello_nest('Yanzhao') # use the module
    # Output:
    #
    # 'Hello Yanzhao'
    >>> modules.hello_nest(123) # runtime type checking
    # Output:
    #
    # TypeError: The param "name" of Nest module "hello_nest" should be type of "str". Got "123".
    >>> modules.hello_nest('Yanzhao', wrong=True)
    # Output:
    #
    # Unexpected param(s) "wrong" for Nest module:
    # hello_nest(
    # name:str) -> str
    ```

    > Note that Nest automatically imports modules and checks them as they are used to make sure everything is as expected.

2. You can also directly import modules like this:

    ```python
    >>> from nest.main.hello import hello_nest
    >>> hello_nest('World')
    # Output:
    #
    # 'Hello World'
    ```

    > The import syntax is `from nest.<namespace>.<filename> import <module_name>`

3. Access to Nest modules through code is flexible and easy.

### Debug your Nest modules
1. Open an interactive python interpreter under the same path of "hello.py" and run following commands:

    ```python
    >>> from nest import modules
    >>> modules.hello_nest('Yanzhao')
    # Output:
    #
    # 'Hello Yanzhao'
    ```

2. Keep the interpreter **OPEN** and use an externel editor to modify the "hello.py":

    ```python
    # change Line7 from "return 'Hello ' + name" to
    return 'Nice to meet you, ' + name
    ```

3. Back to the interpreter and rerun the same command:

    ```python
    >>> modules.hello_nest('Yanzhao')
    # Output:
    #
    # 'Nice to meet you, Yanzhao'
    ```

    > Note that Nest detects source file modifications and automatically reloads the module.

4. You can use this feature to develop and debug your Nest modules efficiently.

### Install Nest modules from local path
1. Create a folder `my_namespace` and move the `hello.py` into it:

    ```bash
    $ mkdir my_namespace
    $ mv hello.py ./my_namespace/
    ```

2. Create a new file `more.py` under the folder `my_namespace` with the following content:

    ```python
    from nest import register

    @register(author='Yanzhao', version='1.0.0')
    def sum(a: int, b: int) -> int:
        """Sum two numbers."""

        return a + b

    # There is no need to repeatedly declare meta information
    # as modules within the same file automatically reuse the 
    # previous information. But overriding is also supported.
    @register(version='2.0.0')
    def mul(a: float, b: float) -> float:
        """Multiply two numbers."""
        
        return a * b
    ```

    > Now we have:
    ```
    current path/
    ├── my_namespace/
    │   ├── hello.py
    │   ├── more.py
    ```

3. Run the following command in the shell:

    ```bash
    $ nest module install ./my_namespace hello_word
    # Output:
    #
    # Install "./my_namespace/" -> Search paths. Continue? (Y/n) [Press <Enter>]
    ```

    > This command will add  "**my_namespace**" folder to Nest's search path, and register all Nest modules in it under the namespace "**hello_word**". If the last argument is omitted, the directory name, "my_namespace" in this case, is used as the namespace.

4. Verify the installation via CLI:

    ```bash
    $ nest module list
    # Output:
    #
    # 3 Nest modules found.
    # [0] hello_world.hello_nest (1.0.0)
    # [1] hello_world.mul (2.0.0)
    # [2] hello_world.sum (1.0.0)
    ```

    > Note that those Nest modules can now be accessed regardless of your working path.

5. Verify the installation via Python interpreter:

    ```bash
    $ ipython # open IPython interpreter
    ```
    ```python
    >>> from nest import modules
    >>> print(len(modules))
    # Output:
    #
    # 3
    >>> modules.[Press <Tab>] # IPython Auto-completion
    # Output:
    #
    # hello_nest
    # mul
    # sum
    >>> modules.sum(3, 2)
    # Output:
    #
    # 5
    >>> modules.mul(2.5, 4.0)
    # Output:
    #
    # 10.0
    ```

6. Thanks to the auto-import feature of Nest, you can easily share modules between different local projects.
    
### Install Nest modules from URL
1. You can use the CLI tool to install modules from URL:

    ```bash
    # select one of the following commands to execute
    # 0. install from Github repo via short URL (GitLab, Bitbucket are also supported)
    $ nest module install github@ZhouYanzhao/Nest:pytorch pytorch
    # 1. install from Git repo
    $ nest module install "-b pytorch https://github.com/ZhouYanzhao/Nest.git" pytorch
    # 2. install from zip file URL
    $ nest module install "https://github.com/ZhouYanzhao/Nest/archive/pytorch.zip" pytorch
    ```

    > The last optional argument is used to specify the namespace, "**pytorch**" in this case.

2. Verify the installation:

    ```bash
    $ nest module list
    # Output:
    #
    # 26 Nest modules found.
    # [0] hello_world.hello_nest (1.0.0)
    # [1] hello_world.mul (2.0.0)
    # [2] hello_world.sum (1.0.0)
    # [3] pytorch.adadelta_optimizer (0.1.0)
    # [4] pytorch.checkpoint (0.1.0)
    # [5] pytorch.cross_entropy_loss (0.1.0)
    # [6] pytorch.fetch_data (0.1.0)
    # [7] pytorch.finetune (0.1.0)
    # [8] pytorch.image_transform (0.1.0)
    # ...
    ```

### Uninstall Nest modules
1. You can remove modules from Nest's search path by executing:

    ```bash
    # given namespace
    $ nest module remove hello_world
    # given path to the namespace
    $ nest module remove ./my_namespace/
    ```

2. You can also delete the corresponding files by appending a `--delete` or `-d` flag:

    ```bash
    $ nest module remove hello_world --delete
    ```

### Version control Nest modules

1. When installing modules, Nest adds the namespace to its search path without modifying or moving the original files. So you can use any version control system you like, e.g., Git, to manage modules. For example:

    ```bash
    $ cd <path of the namespace>
    # update modules
    $ git pull
    # specify version
    $ git checkout v1.0
    ```

2. When developing a Nest module, it is recommended to define meta information for the module, such as the author, version, requirements, etc. Those information will be used by Nest's CLI tool. There are two ways to set meta information:

    * define meta information in code

    ```python
    from nest import register

    @register(author='Yanzhao', version='1.0')
    def my_module() -> None:
        """My Module"""
        pass
    ```

    * define meta information in a `nest.yml` under the path of namespace

    ```YAML
    author: Yanzhao
    version: 1.0
    requirements:
        - {url: opencv, tool: conda}
        # default tool is pip
        - torch>=0.4
    ```

    > Note that you can use both ways at the same time.

### Use Nest to manage your experiments
1. Make sure you have Pytorch-backend modules installed, and if not, execute the following command:

    ```bash
    $ nest module install github@ZhouYanzhao/Nest:pytorch pytorch
    ```

2. Create "**train_mnist.yml**" with the following content:

    ```YAML
    _name: network_trainer
    data_loaders:
      _name: fetch_data
      dataset: 
        _name: mnist
        data_dir: ./data
      batch_size: 128
      num_workers: 4
      transform:
        _name: image_transform
        image_size: 28
        mean: [0.1307]
        std: [0.3081]
      train_splits: [train]
      test_splits: [test]
    model:
      _name: lenet5
    criterion:
      _name: cross_entropy_loss
    optimizer:
      _name: adadelta_optimizer
    meters:
      top1:
        _name: topk_meter
        k: 1
    max_epoch: 10
    device: cpu
    hooks:
      on_end_epoch: 
        - 
          _name: print_state
          formats:
            - 'epoch: {epoch_idx}'
            - 'train_acc: {metrics[train_top1]:.1f}%'
            - 'test_acc: {metrics[test_top1]:.1f}%'   
    ```

    > Check [HERE](https://github.com/ZhouYanzhao/Nest/tree/pytorch/demo) for more comprehensive demos.

3. Run your experiments through CLI:

    ```bash
    $ nest task run ./train_mnist.yml
    ```

4. You can also use Nest's task runner in your code:

    ```python
    >>> from nest import run_tasks
    >>> run_tasks('./train_mnist.yml')
    ```

5. Based on the task runner feature, Nest modules can be flexibly replaced and assembled to create your desired experiment settings.

## Contact 
Yanzhao Zhou <yzhou.work at outlook.com>

## Issues
Feel free to submit bug reports and feature requests.

## Contribution
Pull requests are welcome.

## License
[MIT](https://opensource.org/licenses/MIT)

Copyright © 2018-present, Yanzhao Zhou
