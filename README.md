# shtick 
#### shell-agnostic-shell-configuration-generation
(noun) : something cl[ever]
(see also) : pedantic

### what is this?
this is a tool I use to manage groups of shell configurations (aliases, env vars, functions). It started out written in C for a presentation on unix shells to a group of TAs. I asked an LLM to help me port it to python because I got sick of remembering about memory and waking up in cold sweats over a presentation to a bunch of 20 y/o's, and chap and I got carried away. That's the disclaimer - AI helped. But this tool is for me and I use it actively, if you think it could help you too, continue on.  

It's useful if you use multiple shells regularly and would like a single source of truth for your shell ..config (...within reason).  

- Define aliases, env vars, and shell functions in one place (~/.config/shtick/config.toml); 
- Manage persistent aliases, env vars, shell functions
- Define toggleable groups of aliases, e.g. `dev`, `personal`

If you decide you want to use this yourself, do all the usual cloning, then from your local run `make install`. 


`usage: shtick [-h] [--debug] {generate,add,add-persistent,alias,env,function,remove,remove-persistent,activate,deactivate,status,list,shells,source} ...`

Usage examples:
```
shtick generate [--terse] # generate shell files for all items in config

shtick list             # list all managed items
shtick status           # see all active items
shtick activate work    # activate items in work group
shtick deactivate dev   # deactivate items in dev group
eval "$(shtick source)"   # IMPORTANT! load changes in shell. See tip below

shtick alias ll='ls -la'            # add persistent alias
shtick add alias work up='cd ../'   # add alias to specified group
shtick remove alias work up         # remove alias from specified group

shtick env EDITOR='micro'               # add persistent environment variable
shtick remove env project DEBUG='true'  # add env var to project group
shtick remove env persistent XDG_HAM    # remove persistent environment variable

shtick function mkcd='mkdir -p "$1" && cd "$1"'                       # add persistent function
shtick add function util backup='cp "$1" "$1.backup.$(date +%Y%m%d)"' # add function to util group

# Recommended: add the following:
# Add alias for instant sourcing  
shtick alias ss='eval "$(shtick source)"'  # or your own command to source

# Use it after any shtick command to 'auto' source changes  
shtick alias deploy='./deploy.sh' && ss  
shtick activate work && ss  
```

Sample config (pulled from my config):
`~/.config/shtick/config.toml. Also see [sample](/config.sample.toml)
```
# Persistent items - always active in every shell session
[persistent.aliases]
pls="sudo !!"
bk = "- || cd -"
wttr = "curl wttr.in"
refresh = "source ${HOME}/.zshrc"
goclass = "cd ${HOME}/Documents/Class/"
goproj = "cd ${HOME}/Documents/Project/"
goorg = "cd ${HOME}/Documents/GithubOrgs/"
gad="git add"
gall="git add --all"
gputt="git push origin trunk"
gcamm="git commit --all --message"
glogg="git log --online --graph --decorate --all"

[persistent.env_vars] 
PAGER = "less"
EDITOR = "micro"
BROWSER = "firefox"

[persistent.functions]
backup = "cp \"$1\" \"$1.backup.$(date +%Y%m%d_%H%M%S)\""

[dev.aliases]
mk = "make"
mkr =  "make run"
mki =  "make install"
gfort = "gfortran"
ni = "npm --install"
serve = "python manage.py runserver"
pyserve = "python3 -m http.server 8000"
brewup = "brew update && brew upgrade && brew cleanup"

[dev.env_vars]
JOM = "terry"

[dev.functions]
newproject = "mkdir -p \"$HOME/projects/$1\" && cd \"$HOME/projects/$1\" && git init"

[personal.aliases]
myip = "curl ifconfig.me"

[personal.env_vars]
TOM = "JERRY"

[personal.functions]
note = "echo \"$(date): $*\" >> $HOME/notes.txt"
```  

## Python API Usage
We also expose a public API for using shtick functionality as library functions.  

### Basic Usage
```
from shtick import ShtickManager

# Initialize the manager
manager = ShtickManager()

# Add persistent aliases (always active)
manager.add_persistent_alias('ll', 'ls -la')
manager.add_persistent_alias('grep', 'grep --color=auto')

# Add environment variables
manager.add_persistent_env('EDITOR', 'vim')
manager.add_persistent_env('BROWSER', 'firefox')

# Check status
status = manager.get_status()
print(f"Active groups: {status['active_groups']}")
print(f"Persistent items: {status['persistent_items']}")
```

### Working with groups
```
from shtick import ShtickManager

manager = ShtickManager()

# Create project-specific configuration
project_aliases = {
    'start': 'npm start',
    'test': 'npm test',
    'build': 'npm run build',
    'deploy': 'npm run deploy'
}

# Add all aliases to a group
for alias, command in project_aliases.items():
    manager.add_alias(alias, command, 'frontend')

# Add environment variables for the project
manager.add_env('NODE_ENV', 'development', 'frontend')
manager.add_env('API_URL', 'http://localhost:3000', 'frontend')

# Activate the group
manager.activate_group('frontend')

# Get information about what's configured
items = manager.list_items('frontend')
for item in items:
    print(f"{item['type']}: {item['key']} = {item['value']}")
```

### Automation and scripting

from shtick import ShtickManager
```
def setup_development_environment():
    """Set up a complete development environment"""
    manager = ShtickManager()
    
    # Docker aliases
    docker_aliases = {
        'dps': 'docker ps',
        'dimg': 'docker images',
        'dlog': 'docker logs -f',
        'dexec': 'docker exec -it',
        'dstop': 'docker stop $(docker ps -q)',
    }
    
    for alias, command in docker_aliases.items():
        manager.add_alias(alias, command, 'docker')
    
    # Git aliases
    git_aliases = {
        'gst': 'git status',
        'gco': 'git checkout',
        'gcb': 'git checkout -b',
        'gpl': 'git pull',
        'gps': 'git push',
    }
    
    for alias, command in git_aliases.items():
        manager.add_alias(alias, command, 'git')
    
    # Development environment variables
    dev_env = {
        'DOCKER_BUILDKIT': '1',
        'COMPOSE_DOCKER_CLI_BUILD': '1',
        'NODE_ENV': 'development',
    }
    
    for var, value in dev_env.items():
        manager.add_env(var, value, 'development')
    
    # Activate all development groups
    groups = ['docker', 'git', 'development']
    for group in groups:
        success = manager.activate_group(group)
        print(f"{'✓' if success else '✗'} Activated {group} group")
    
    # Generate shell files
    manager.generate_shell_files()
    
    # Show source command for immediate use
    source_cmd = manager.get_source_command()
    if source_cmd:
        print(f"\nTo use immediately, run: {source_cmd}")

def clean_inactive_groups():
    """Remove aliases from inactive groups"""
    manager = ShtickManager()
    
    active_groups = manager.get_active_groups()
    all_groups = manager.get_groups()
    
    inactive_groups = set(all_groups) - set(active_groups) - {'persistent'}
    
    for group in inactive_groups:
        items = manager.list_items(group)
        if items:
            print(f"Found {len(items)} items in inactive group '{group}'")
            # Could prompt user or automatically clean up
    
    return inactive_groups

# Example usage
if __name__ == '__main__':
    setup_development_environment()
```

### Error handling and validation
```
from shtick import ShtickManager
def safe_alias_management():
    """Example with proper error handling"""
    manager = ShtickManager(debug=True)  # Enable debug output
    
    # Try to add an alias
    success = manager.add_persistent_alias('test', 'echo "Hello World"')
    if success:
        print("✓ Alias added successfully")
    else:
        print("✗ Failed to add alias")
    
    # Check current status before making changes
    status = manager.get_status()
    if 'error' in status:
        print(f"Configuration error: {status['error']}")
        return False
    
    # Validate shell integration
    if not status['loader_exists']:
        print("Warning: Shell loader not found. Run 'shtick generate'")
    
    # List current items to avoid conflicts
    existing_items = manager.list_items()
    existing_aliases = [item['key'] for item in existing_items 
                       if item['type'] == 'alias']
    
    new_alias = 'myalias'
    if new_alias in existing_aliases:
        print(f"Alias '{new_alias}' already exists")
    else:
        manager.add_persistent_alias(new_alias, 'echo "New alias"')
    
    return True

# Run the example
safe_alias_management()
```