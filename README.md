# stan-language-server

A server implementing the Language Server Protocol for the STAN probabilistic
programming language. Currently in a very alpha state.

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

## Roadmap

- [ ] LSP implementation
    - [ ] textDocument/completion
    - [x] Diagnostics
    - [ ] Definitely more
- [ ] Clients
    - [ ] VSCode extension
    - [ ] Neovim (lspconfig+mason)
    - [ ] probably more