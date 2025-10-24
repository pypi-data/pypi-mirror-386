# Obsidian Asset Manager

> Obsidian Asset Management Model

```text
  ____  __       _    ___             ___               __    
 / __ \/ /  ___ (_)__/ (_)__ ____    / _ | ___ ___ ___ / /____
/ /_/ / _ \(_-</ / _  / / _ `/ _ \  / __ |(_-<(_-</ -_) __(_-<
\____/_.__/___/_/\_,_/_/\_,_/_//_/ /_/ |_/___/___/\__/\__/___/
```

## ⚡️ Quick Start

### 1️⃣ Check preconditions

- [Python](https://www.python.org/downloads/) >= 3
- [pip](https://pip.pypa.io/en/stable/installation/)
- [Obsidian](https://obsidian.md/)
- Obsidian Community Plugins
    - [Tasks](https://publish.obsidian.md/tasks/Getting+Started/Installation)

### 2️⃣ Install `obsiasset` tool

```bash
pip install obsiasset
```

### 3️⃣ Init Asset Vault and Import Sample Assets

```bash
obsiasset init --schema sales --lang en --import-sample
```

![ToDo List](images/todo_list.png)
![Dashboard](images/dashboard.png)
![Project](images/project.png)
![Graph View](images/graph.png)

## 📦 Installation

```bash
pip install obsiasset
obsiasset show-version
```

----

## 🍺 Basic Usage

```text
usage: obsiasset [-h] {show-version,init} ...

positional arguments:
  {show-version,init}
    show-version       display version info for this tool and your Python runtime
    init               Init assets vault

optional arguments:
  -h, --help           show this help message and exit
```

### show-version

```text
usage: obsiasset show-version [-h]

optional arguments:
  -h, --help  show this help message and exit
```

### init

```text
usage: obsiasset init [-h] --schema <sales> --lang <en|cn> [--import-sample]

optional arguments:
  -h, --help        show this help message and exit
  --schema <sales>  Select schema : sales
  --lang <en|cn>    Select language : en | cn
  --import-sample   Import assets sample
```
