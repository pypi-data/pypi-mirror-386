from .. import messages as msg
from ..resources import sym
from .run import run_command


def get_version_str(return_project_name: bool = False):
    result, _ = run_command(['uv', 'version', '--color', 'never'])
    project_name, version = result.stdout.strip().split(' ')

    if return_project_name:
        return project_name, version

    return version


def collect_info(version: str = None):
    result, _ = run_command(['uv', 'version', version, '--dry-run', '--color', 'never'], print_stderr=False)
    if not _:
        msg.failure(result.stderr.strip())

    package_name, old_version, _, new_version = result.stdout.strip().split(' ')
    return package_name, old_version, new_version


def calculate_version(bump_type: str, pre_release: str = None):
    possible_bumps = ['major', 'minor', 'patch', 'stable', 'alpha', 'beta', 'rc', 'post', 'dev']
    if bump_type not in possible_bumps:
        msg.failure(f'invalid release type: "{bump_type}"\n  possible values: {", ".join(possible_bumps)}')

    command = ['uv', 'version', '--dry-run', '--color', 'never', '--bump', bump_type]
    command = command if not pre_release else command + ['--bump', pre_release]
    res, _ = run_command(command, print_stderr=False)

    return res.stdout.strip().split(' ')[-1]


def tag(config: dict, new_ver: str):
    tag_prefix = config['tag_prefix']
    return f'{tag_prefix}{new_ver}'


def commit_message(config: dict, old_ver: str, new_ver: str):
    return config['commit_message'].format(old_ver=old_ver, new_ver=new_ver)


def update_files(config, package_name, version):
    msg.imsg(f'updating {package_name} version', icon=sym.item)

    if not config['dry_run']:
        _, success = run_command(['uv', 'version', version])
        exit(1) if not success else None


# region unused
def pre_commit_checks():
    msg.imsg('running pre-commit checks', icon=sym.item)
    _, success = run_command(['pre-commit', 'run', '--all-files'], print_stdout=False)
    msg.failure('failed to run pre-commit checks') if not success else None
