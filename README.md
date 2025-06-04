# shtick 
#### shell-agnostic-shell-configuration-generation
(noun) : something cl[ever]  
(see also) : pedantic

### what is this?
this is a tool I use to manage groups of shell configurations (aliases, env vars, functions). It started out written in C for a presentation on unix shells to a group of TAs. I asked an LLM to help me port it to python because I got sick of remembering about memory and waking up in cold sweats over a presentation to a bunch of 20 y/o's, and chap and I got carried away. That's the disclaimer - AI helped. But this tool is for me and I use it actively, if you think it could help you too, continue on.  

It's useful if you use multiple shells regularly and would like a single source of truth for your shell ..config (...within reason).  

- Define aliases, env vars, and shell functions in one place (~/.config/shtick/config.toml)
- Manage persistent aliases, env vars, shell functions
- Define toggleable groups of aliases, e.g. dev, personal
- Create, rename, and remove groups
- Backup and restore configurations
- Configurable behavior through settings

### Shell Integration
Shtick generates shell-specific files in `~/.config/shtick/`. To make them available in new shell sessions, add this to your shell config:  

```
# ~/.bashrc or ~/.zshrc
source ~/.config/shtick/load_active.bash

# ~/.config/fish/config.fish or whatever shell you use
source ~/.config/shtick/load_active.fish
```

### Supported Shells
`bash`, `zsh`, `fish`, `ksh`, `mksh`, `yash`, `dash`, `csh`, `tcsh`, `xonsh`, `elvish`, `nushell`, `powershell`, `rc`, `es`, `oil`
- Run `shtick shells` to see the complete list.

### Installation

If you decide you want to use this yourself, do all the usual cloning, then from your local clone run `make install` and the `shtick` package will be installed in your environment.  

## Commands reference

#### Core
```
# Add persistent items (always active)
shtick alias <key>=<value>           # Add persistent alias
shtick env <key>=<value>             # Add persistent env var
shtick function <key>=<value>        # Add persistent function

# Add to specific groups
shtick add <type> <group> <key>=<value>    # Add to specific group
shtick remove <type> <group> <key>         # Remove from group

# Group activation
shtick activate <group>              # Activate group
shtick deactivate <group>           # Deactivate group

# Information
shtick status                       # Show status
shtick list [-l]                    # List items (use -l for detailed view)
shtick shells [-l]                  # List supported shells
```

#### Group management
```
# Create, rename, and remove groups
shtick group create <name> [-d <description>]    # Create new group
shtick group rename <old> <new>                  # Rename group
shtick group remove <name> [-f]                  # Remove group (-f to skip confirmation)
```

#### Backup & restore
```
# Backup management
shtick backup create [-n <name>]     # Create backup (optional custom name)
shtick backup list                   # List available backups
shtick backup restore <name>         # Restore from backup
```

#### Settings management
```
# Configure shtick behavior
shtick settings init                 # Create default settings file
shtick settings show                 # Show current settings
shtick settings set <key> <value>    # Change a setting

# Available settings:
# generation.shells = []             # List of shells to generate for (empty = auto-detect)
# generation.parallel = false        # Enable parallel generation
# behavior.auto_source_prompt = true # Prompt to source after changes
# behavior.check_conflicts = true    # Warn about conflicts
# behavior.backup_on_save = false    # Auto-backup before saving
```

#### Other commands
```
shtick generate [--terse]           # Regenerate shell files
shtick source [--shell <shell>]     # Output source command for eval
```


### Usage Examples
#### Basic Workflow
```
# Add some aliases
shtick alias ll='ls -la'
shtick alias gs='git status'
shtick alias gd='git diff'
```

#### Add environment variables
```
shtick env EDITOR='vim'
shtick env PAGER='less'
```

#### Add functions
```
shtick function mkcd='mkdir -p "$1" && cd "$1"'
shtick function backup='cp "$1" "$1.backup.$(date +%Y%m%d)"'
```

#### Load changes in current shell
`eval "$(shtick source)"`

### Working with Groups
#### Create a work group
`shtick group create work -d "Work-related configurations"`

#### Add items to the work group
```
shtick add alias work deploy='./scripts/deploy.sh'
shtick add env work NODE_ENV='development'
shtick add function work vpn='sudo openvpn /etc/vpn/work.conf'
```

#### Create a personal group
`shtick group create personal`

#### Add items to personal group
```
shtick add alias personal myip='curl ifconfig.me'
shtick add function personal note='echo "$(date): $*" >> $HOME/notes.txt'
```

#### Activate work group
`shtick activate work`

#### Switch to personal
```
shtick deactivate work
shtick activate personal
```

#### Or have both active
```
shtick activate work
shtick activate personal
Backup and Restore  

# Create a backup before major changes
shtick backup create -n "before_refactor"
```

#### Make your changes...
`shtick group remove old_stuff -f`

#### Oops, need to restore
`shtick backup restore before_refactor`

### Settings Customization
#### Initialize settings file
`shtick settings init`

#### Disable auto-source prompt
`shtick settings set behavior.auto_source_prompt false`

#### Generate for specific shells only
`shtick settings set generation.shells '["bash", "zsh"]'`

#### Enable auto-backup
`shtick settings set behavior.backup_on_save true`

## Sample Configuration
Shtick looks for `~/.config/shtick/config.toml`. Here's a sample. See also [sample](/config.sample.toml)

```
# Persistent items - always active in every shell session
[persistent.aliases]
pls = "sudo !!"
bk = "- || cd -"
wttr = "curl wttr.in"
refresh = "source ${HOME}/.zshrc"
goclass = "cd ${HOME}/Documents/Class/"
goproj = "cd ${HOME}/Documents/Project/"
goorg = "cd ${HOME}/Documents/GithubOrgs/"
gad = "git add"
gall = "git add --all"
gputt = "git push origin trunk"
gcamm = "git commit --all --message"
glogg = "git log --oneline --graph --decorate --all"

[persistent.env_vars] 
PAGER = "less"
EDITOR = "micro"
BROWSER = "firefox"

[persistent.functions]
backup = "cp \"$1\" \"$1.backup.$(date +%Y%m%d_%H%M%S)\""

# Development group
[dev.aliases]
mk = "make"
mkr = "make run"
mki = "make install"
gfort = "gfortran"
ni = "npm install"
serve = "python manage.py runserver"
pyserve = "python3 -m http.server 8000"
brewup = "brew update && brew upgrade && brew cleanup"

[dev.env_vars]
DEBUG = "1"
NODE_ENV = "development"

[dev.functions]
newproject = "mkdir -p \"$HOME/projects/$1\" && cd \"$HOME/projects/$1\" && git init"

# Personal group
[personal.aliases]
myip = "curl ifconfig.me"

[personal.env_vars]
PERSONAL_NOTES = "$HOME/Documents/notes"

[personal.functions]
note = "echo \"$(date): $*\" >> $HOME/notes.txt"
todo = "echo \"[ ] $*\" >> $HOME/todo.txt"

# Work group (activate during work hours)
[work.aliases]
deploy = "./scripts/deploy.sh"
staging = "ssh staging.company.com"
prod = "ssh prod.company.com"

[work.env_vars]
AWS_PROFILE = "work"
KUBECONFIG = "$HOME/.kube/work-config"

[work.functions]
vpn = "sudo openvpn /etc/vpn/work.conf"
standup = "open https://meet.company.com/daily-standup"
```

### Tips n. Trinkets


#### "Instant" sourcing alias: Add this for convenience:
```
shtick alias ss='eval "$(shtick source)"'
# Now you can just run 'ss' after any shtick command
```

#### Check for conflicts: Shtick warns you about duplicate items across groups:
```
$ shtick add alias dev ll='ls -la'
Warning: Item 'll' exists in groups: ['persistent']
```

#### Fuzzy removal: Remove items with partial matching:
```
shtick remove alias persistent brew  # Matches 'brewup' and offers selection
```

#### Quick status check: See what's active at a glance:
```$ shtick status
Persistent (always active): 15 items
Available Groups:
  dev: 8 items (ACTIVE)
  personal: 5 items (inactive)
  work: 12 items (ACTIVE)
```
#### Backup before removing groups:
```
shtick backup create -n "safe_point" && shtick group remove old_configs -f
```