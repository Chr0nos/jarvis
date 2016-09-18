set nocompatible              " be iMproved, required
filetype off                  " required
syn on
set number
set hlsearch
set tabstop=4
syntax on
set ruler
set nu
set colorcolumn=80

set swapfile!

nmap <s-tab> :tabnew
nmap <tab> :tabnext<cr>
imap <s-tab> <esc>:tabnext<cr>i
nmap <s-r> :NERDTreeToggle<cr>

" set the runtime path to include Vundle and initialize
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()
" alternatively, pass a path where Vundle should install plugins
"call vundle#begin('~/some/path/here')

" let Vundle manage Vundle, required
Plugin 'VundleVim/Vundle.vim'
" ------------------------------------------------

" Js
Plugin 'crusoexia/vim-javascript-lib'
Plugin 'pangloss/vim-javascript'

" Essential
Plugin 'scrooloose/nerdtree'
Plugin 'editorconfig/editorconfig-vim'

" Less essential
Plugin 'eparreno/vim-l9'
Plugin 'othree/vim-autocomplpop'
Plugin 'szw/vim-tags'
let g:vim_tags_auto_generate = 1

" Graphical
Plugin 'crusoexia/vim-monokai'
Plugin 'flazz/vim-colorschemes'
" ------------------------------------------------


" All of your Plugins must be added before the following line
call vundle#end()            " required
filetype plugin indent on    " required

colorscheme monokai
