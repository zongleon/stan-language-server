# stan-language-server

A server implementing the Language Server Protocol for the STAN probabilistic
programming language. Currently in a very alpha state.

Note: You must have the stan compiler [stanc3 binary](https://github.com/stan-dev/stanc3/releases)
on your path. It should be named `stanc`.

## Installing

Assuming you have poetry installed, run:
```sh
make
```

This runs:
```sh
poetry build
pip3 install dist/stan_language_server-0.1.0-py3-none-any.whl --force-reinstall
```

Which is appropriate for testing but you might want to install the wheel in a venv
or somewhere else.

## How to use

I am using neovim, so here's how I'm testing the server so far. This expects that
you are using [lspconfig](https://github.com/neovim/nvim-lspconfig) to manage LSPs.
I added this to my neovim init.

```lua
local lspconfig = require 'lspconfig'
local configs = require 'lspconfig.configs'

if not configs.stan_language_server then
  configs.stan_language_server = {
    default_config = {
      cmd = { 'stan-language-server' },
      filetypes = { 'stan' },
      root_dir = function(fname)
        return lspconfig.util.find_git_ancestor(fname)
      end,
      settings = {},
      single_file_support = true,
    },
  }
end

lspconfig.stan_language_server.setup {}
```

Until I write the neovim client, you will also have to set the filetype.

```lua
vim.filetype.add {
  extension = {
    stan = 'stan',
  },
}
```

## Details

Diagnostics are implemented using the STAN compiler, stanc.
Warnings and errors are collected and sent as diagnostics.

Completions are semi-automatically collected via the script `extract_function_sigs.py'.
This script should be run in the root directory of the STAN documentation, found at
https://github.com/stan-dev/docs. It will generate the complete list of documented
STAN functions.

Keyword completions are manually added from the following page:
https://mc-stan.org/docs/reference-manual/expressions.html#reserved-names.
The current list of keyword completions are found in the following 
[Google Sheets link](https://docs.google.com/spreadsheets/d/1MJqSPgcLxSIKI7qxCH1gVq3SKGUQL25dYww3BDaHERs/edit?usp=sharing).
Variable completions are currently limited to variables declared in `data` or `(transformed) parameters` or `quantities`.

## Roadmap

- [ ] LSP implementation
    - [x] Completion
    - [x] Diagnostics
    - [ ] Hover
    - [ ] Rename
    - [ ] Goto Declaration
    - [ ] Goto Definition
    - [ ] Probably more (snippets?) (folds?)
- [ ] Clients
    - [ ] VSCode extension
    - [ ] Neovim (lspconfig+mason)
    - [ ] probably more