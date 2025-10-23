# Foldora - File & Directory Manager CLI Tool

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/foldora)](https://pypi.org/project/foldora/)
[![PyPI version](https://img.shields.io/pypi/v/foldora)](https://pypi.org/project/foldora/)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](code_of_conduct.md)

**Foldora** is a Python command-line interface (CLI) tool designed to help you efficiently manage files and directories.

---

## 🚀 Features

Foldora provides essential file and directory management commands:

- 📁 List files and directories  
- 📂 Create directories and files  
- 🧹 Delete (purge) files and directories  
- 📝 Display file contents  
- ✏️ Replace spaces in file and folder names with underscores  

---

## 🛠️ Installation

Install Foldora from PyPI:

```bash
pip install foldora
```

> **Note:** Ensure Python is installed and available in your system path.

---

## 📦 Usage

Run Foldora using the `fd` command followed by the desired operation.

---

### 📁 List Files and Directories

List the files and directories within one or more specified paths.  
If no paths are provided, the current working directory is used.

**Command:**
```bash
fd la [paths] [--files] [--dirs]
```

**Notes:**
- If a specified path is a file, only that file will be listed.  
- Hidden files and directories may be included depending on your system settings.  
- Multiple paths can be provided to list contents from different directories simultaneously.  

**Examples:**
```bash
fd la
fd la --files
fd la --dirs
fd la --files /path/to/dir
fd la --dirs /path/to/dir
fd la --files /path1 /path2
fd la --dirs /path1 /path2
```

---

### 📂 Create Directories

Create one or more directories.  
All necessary parent directories are created automatically if they do not exist.

**Command:**
```bash
fd nd [paths]
```

**Notes:**
- Does not modify existing directories.  
- Supports creating multiple directories in a single command.  

**Examples:**
```bash
fd nd directory1 directory2
fd nd /path/to/parent/new_directory
```

---

### 📄 Create Files

Create one or more empty files in the current directory or a specified path.

**Command:**
```bash
fd nf '[-tp path_to_dir]' [filenames]
```

**Notes:**
- Supports creating multiple files in one command.  
- Existing files will not be overwritten.  
- If the specified directory does not exist, an error will be raised.  

**Examples:**
```bash
fd nf file1.txt file2.txt
fd nf -tp /path/to/dir file1.txt file2.txt
```

---

### 🧹 Delete Files and Directories

Permanently delete specified files and directories, with user confirmation before proceeding.

**Command:**
```bash
fd pg [paths]
```

**Notes:**
- Use with caution — this action **cannot be undone**.  
- Directories are deleted recursively, including all contents.  
- Requires proper permissions to delete the specified paths.  

**Examples:**
```bash
fd pg file1 directory1
```

---

### 📝 Display File Contents

Display the contents of one or more files in the console.

**Command:**
```bash
fd vc [files]
```

**Notes:**
- Files must be readable.  
- Supports multiple files — each file’s content is displayed in sequence.  

**Examples:**
```bash
fd vc file1.txt file2.txt
```

---

### ✏️ Replace Spaces in File/Folder Names

Rename files and folders by replacing spaces in their names with underscores.

**Command:**
```bash
fd fs [path]
```

**Notes:**
- Defaults to the current directory if no path is specified.  
- By default, only top-level files and folders are renamed.  

**Examples:**
```bash
fd fs
fd fs /path/to/dir
```

---

## 🤝 Contributing

Contributions are welcome!  
Feel free to open issues or submit pull requests to help improve Foldora.

---

## 📄 License

This project is licensed under the **MIT License**.
