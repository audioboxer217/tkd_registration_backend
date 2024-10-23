python_ver := '3.10.13'
python_win_ver := '3.10.11'
python_subdir := if os_family() == "windows" { "/Scripts" } else { "/bin" }
python_exec := if os_family() == "windows" { "/python.exe" } else { "/python3" }
system_python := if os_family() == "windows" { "${HOME}/.pyenv/pyenv-win/versions/" + python_win_ver + "/python.exe" } else { "${HOME}/.pyenv/versions/" + python_ver + "/bin/python3" }
zappa := './.venv/' + python_subdir + '/zappa'

default:
  @just --list

# Bootstrap Python Env. Valid Types: 'deploy' & 'dev'
bootstrap venv_dir='.venv' type="deploy":
  if test ! -e {{ venv_dir }}; then {{ system_python }} -m venv {{ venv_dir }}; fi
  ./{{ venv_dir }}{{ python_subdir }}{{ python_exec }} -m pip install --upgrade pip
  ./{{ venv_dir }}{{ python_subdir }}{{ python_exec }} -m pip install --upgrade -r requirements.txt {{ if type == 'dev' { '-r dev_requirements.txt' } else { '' } }}

_aws_login AWS_PROFILE:
  @aws --profile {{ AWS_PROFILE }} sts get-caller-identity || aws sso login

_zappa CMD ACCT ENV:
  @just _aws_login "$(yq '.{{ ENV }}.profile_name' envs/{{ ACCT }}.yml)"
  {{ zappa }} {{ CMD }} -s envs/{{ ACCT }}.yml {{ ENV }}

# Deploy new environment
deploy ACCT='test' ENV='dev': (_zappa "deploy" ACCT ENV)

# Certify new environment
certify ACCT='test' ENV='dev': (_zappa "certify" ACCT ENV)

# Update existing environment
update ACCT='test' ENV='dev': (_zappa "update" ACCT ENV)

# Check status of existing environment
status ACCT='test' ENV='dev': (_zappa "status" ACCT ENV)

# Check logs of running environment
logs ACCT='test' ENV='dev': (_zappa "tail" ACCT ENV)

# Undeploy a running environment
undeploy ACCT='test' ENV='dev': (_zappa "undeploy" ACCT ENV)

archive_db TABLE OUTPUT_FILE='output/full_lookup.json' profile='personal' venv_dir='.venv':
  @just _aws_login {{ profile }}
  if [ ! -d $(dirname "{{ OUTPUT_FILE }}") ];then mkdir -p $(dirname "{{ OUTPUT_FILE }}");fi
  ./{{ venv_dir }}{{ python_subdir }}{{ python_exec }} \
    ./scripts/archive_reg_db.py \
    -p {{ profile }} \
    -o {{ OUTPUT_FILE }} \
    {{ TABLE }}

load_lookup_db INPUT_FILE='output/full_lookup.json' TABLE='' profile='personal' venv_dir='.venv':
  @just _aws_login {{ profile }}
  ./{{ venv_dir }}{{ python_subdir }}{{ python_exec }} \
    ./scripts/load_lookup_db.py \
    -p {{ profile }} \
    {{ if TABLE != '' { "-t " + TABLE } else { "" } }} \
    {{ INPUT_FILE }}
