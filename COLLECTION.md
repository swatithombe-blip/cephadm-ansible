# Ansible Collection Documentation

## Overview

This document describes the Ansible Collection implementation for `cephadm-ansible`. The project is structured as a proper Ansible Collection (`ceph.cephadm`) while maintaining **100% backward compatibility** for existing users who clone the repository directly.

## Goals

- ✅ Convert repository to proper Ansible Collection format
- ✅ Maintain complete backward compatibility
- ✅ Enable Galaxy publishing (`ceph.cephadm`)
- ✅ Support both traditional and collection-based workflows
- ✅ Zero breaking changes for existing users

## Current Repository Analysis

### Structure
```
cephadm-ansible/
├── library/                    # 6 custom modules
├── module_utils/               # Shared utilities (ceph_common.py)
├── ceph_defaults/              # Single role
├── *.yml                       # 8 playbooks at root
├── validate/                   # Validation playbooks
├── templates/                  # Jinja2 templates
├── tests/                      # Test suite
└── ansible.cfg                 # Points to ./library and ./module_utils
```

### Dependencies
- **ansible.cfg** explicitly references `./library` and `./module_utils`
- **Modules** use conditional imports for compatibility
- **Playbooks** use `import_role: ceph_defaults`
- **Tests** use relative imports

## Target Collection Structure

```
cephadm-ansible/
├── galaxy.yml                           # NEW: Collection metadata
├── README.md
├── COLLECTION.md                        # This document
│
# Collection structure (NEW)
├── plugins/
│   ├── modules/                         # Modules moved here
│   │   ├── cephadm_bootstrap.py
│   │   ├── cephadm_registry_login.py
│   │   ├── ceph_config.py
│   │   ├── ceph_orch_apply.py
│   │   ├── ceph_orch_daemon.py
│   │   └── ceph_orch_host.py
│   └── module_utils/                    # Module utilities moved here
│       └── ceph_common.py
│
├── roles/
│   └── ceph_defaults/                   # Role moved here
│       ├── defaults/
│       ├── meta/
│       └── README.md
│
├── playbooks/                           # NEW: Collection playbooks
│   ├── cephadm-preflight.yml           # Symlink to ../cephadm-preflight.yml
│   ├── cephadm-clients.yml             # Symlink to ../cephadm-clients.yml
│   ├── cephadm-purge-cluster.yml       # Symlink to ../cephadm-purge-cluster.yml
│   └── ...                              # All other playbooks
│
# Backward compatibility (SYMLINKS)
├── library/                             # → plugins/modules/
├── module_utils/                        # → plugins/module_utils/
├── ceph_defaults/                       # → roles/ceph_defaults/
│
# Preserved at root for backward compatibility
├── cephadm-preflight.yml
├── cephadm-clients.yml
├── cephadm-purge-cluster.yml
├── cephadm-distribute-ssh-key.yml
├── cephadm-set-container-insecure-registries.yml
├── rocksdb-resharding.yml
├── checks.yml
├── rhel-checks.yml
│
# Other directories (unchanged)
├── validate/
├── templates/
├── tests/
├── doc/
└── ansible.cfg                          # Updated to include plugins path
```

## Migration Steps

### Phase 1: Preparation (Non-Breaking)

#### Step 1.1: Create Collection Metadata

Create `galaxy.yml`:

```yaml
---
namespace: ceph
name: cephadm
version: 1.0.0
readme: README.md
authors:
  - Guillaume Abrioux <gabrioux@redhat.com>
  - Red Hat Ceph Team
description: Ansible collection for Ceph cluster management with cephadm
license:
  - Apache-2.0
tags:
  - ceph
  - cephadm
  - storage
  - infrastructure
  - cluster
repository: https://github.com/ceph/cephadm-ansible
documentation: https://cephadm-ansible.readthedocs.io/
homepage: https://github.com/ceph/cephadm-ansible
issues: https://github.com/ceph/cephadm-ansible/issues

build_ignore:
  - .git
  - .github
  - .gitignore
  - tests
  - tox.ini
  - mypy.ini
  - .readthedocs.yaml
  - cephadm-ansible.spec.in
  - COLLECTION.md
```

#### Step 1.2: Create Directory Structure

```bash
# Create new collection directories
mkdir -p plugins/modules
mkdir -p plugins/module_utils
mkdir -p roles
mkdir -p playbooks
```

### Phase 2: Migration (Breaking Changes Mitigated)

#### Step 2.1: Move Modules

```bash
# Move all modules to plugins/modules/
mv library/*.py plugins/modules/

# Keep __init__.py if needed for namespace
touch plugins/modules/__init__.py
touch plugins/__init__.py
```

**No code changes needed** - Modules already have conditional imports:
```python
try:
    from ansible.module_utils.ceph_common import exit_module, build_base_cmd
except ImportError:
    from module_utils.ceph_common import exit_module, build_base_cmd
```

#### Step 2.2: Move Module Utils

```bash
# Move module_utils to plugins/module_utils/
mv module_utils/*.py plugins/module_utils/
```

#### Step 2.3: Move Role

```bash
# Move ceph_defaults role to roles/
mv ceph_defaults roles/
```

#### Step 2.4: Create Backward Compatibility Symlinks

**Critical for backward compatibility:**

```bash
# Create symlinks pointing to new locations
ln -s plugins/modules library
ln -s plugins/module_utils module_utils
ln -s roles/ceph_defaults ceph_defaults
```

**Verification:**
```bash
# Test that symlinks work
ls -la library/          # Should show modules
ls -la module_utils/     # Should show ceph_common.py
ls -la ceph_defaults/    # Should show role structure
```

#### Step 2.5: Create Playbook Symlinks in Collection

```bash
# Create symlinks in playbooks/ directory for collection users
cd playbooks/
ln -s ../cephadm-preflight.yml
ln -s ../cephadm-clients.yml
ln -s ../cephadm-purge-cluster.yml
ln -s ../cephadm-distribute-ssh-key.yml
ln -s ../cephadm-set-container-insecure-registries.yml
ln -s ../rocksdb-resharding.yml
ln -s ../checks.yml
ln -s ../rhel-checks.yml
cd ..
```

#### Step 2.6: Update ansible.cfg

Update `ansible.cfg` to recognize both paths:

```ini
[defaults]
log_path = $HOME/ansible/ansible.log
library = ./library:./plugins/modules
module_utils = ./module_utils:./plugins/module_utils
roles_path = ./:./roles

# ... rest of config unchanged
```

### Phase 3: Testing & Validation

#### Step 3.1: Test Traditional Workflow

**Must work without changes:**

```bash
# Test 1: Direct playbook execution (traditional)
ansible-playbook -i hosts cephadm-preflight.yml --check

# Test 2: Module availability
ansible localhost -m cephadm_bootstrap --version

# Test 3: Role import
ansible-playbook -i hosts cephadm-preflight.yml --check

# Test 4: Validate ansible.cfg paths
ansible-config dump | grep -E "(DEFAULT_MODULE_PATH|DEFAULT_MODULE_UTILS_PATH)"
```

#### Step 3.2: Test Collection Workflow

**New functionality for collection users:**

```bash
# Build the collection
ansible-galaxy collection build

# Install locally for testing
ansible-galaxy collection install ceph-cephadm-*.tar.gz -p ./collections

# Test collection module usage
ansible localhost -m ceph.cephadm.cephadm_bootstrap --version

# Test collection playbook usage
ansible-playbook ceph.cephadm.cephadm_preflight -i hosts --check

# Test FQCN in playbooks
cat > test-collection.yml <<EOF
---
- hosts: localhost
  tasks:
    - name: Test FQCN module
      ceph.cephadm.cephadm_bootstrap:
        mon_ip: 192.168.1.10
      check_mode: true
EOF

ansible-playbook test-collection.yml
```

#### Step 3.3: Run Existing Tests

```bash
# Run tox tests to ensure nothing breaks
tox -e py3

# Run functional tests
cd tests/functional
ansible-playbook deploy-cluster.yml -i hosts --check
```

### Phase 4: Documentation Updates

#### Step 4.1: Update README.md

Add collection usage section:

```markdown
# Installation

## Traditional Usage (Existing)

Clone the repository and use playbooks directly:

\`\`\`bash
git clone https://github.com/ceph/cephadm-ansible
cd cephadm-ansible
ansible-playbook -i hosts cephadm-preflight.yml
\`\`\`

## Collection Usage (New)

Install from Ansible Galaxy:

\`\`\`bash
ansible-galaxy collection install ceph.cephadm
\`\`\`

Use with FQCN:

\`\`\`yaml
---
- hosts: all
  tasks:
    - name: Bootstrap Ceph cluster
      ceph.cephadm.cephadm_bootstrap:
        mon_ip: 192.168.1.10
\`\`\`

Or run collection playbooks:

\`\`\`bash
ansible-playbook ceph.cephadm.cephadm_preflight -i hosts
\`\`\`
```

#### Step 4.2: Create MIGRATION.md

Document the migration for users:

```markdown
# Migration to Ansible Collection

This project is now available as an Ansible Collection (`ceph.cephadm`).

## For Existing Users

**Nothing changes!** All existing workflows continue to work:
- Clone the repository and run playbooks directly
- Use modules from the `library/` directory
- Use the `ceph_defaults` role

## For New Users

We recommend using the collection:

\`\`\`bash
ansible-galaxy collection install ceph.cephadm
\`\`\`

See README.md for collection usage examples.
```

#### Step 4.3: Update module documentation

Add FQCN to module documentation:

```python
DOCUMENTATION = r'''
---
module: cephadm_bootstrap
short_description: Bootstrap a Ceph cluster
description:
  - Bootstrap a new Ceph cluster using cephadm
  - Can be called as 'cephadm_bootstrap' or 'ceph.cephadm.cephadm_bootstrap'
'''
```

### Phase 5: GitHub & CI Updates

#### Step 5.1: Update .github/workflows/

Ensure CI tests both workflows:

```yaml
# .github/workflows/test-collection.yml
name: Test Collection Build

on: [push, pull_request]

jobs:
  test-traditional:
    name: Test Traditional Usage
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test playbook execution
        run: ansible-playbook cephadm-preflight.yml --syntax-check

  test-collection:
    name: Test Collection Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build collection
        run: ansible-galaxy collection build
      - name: Install collection
        run: ansible-galaxy collection install ceph-cephadm-*.tar.gz
      - name: Test FQCN
        run: ansible localhost -m ceph.cephadm.cephadm_bootstrap --version
```

#### Step 5.2: Update .gitignore

Add collection artifacts:

```
# Collection build artifacts
*.tar.gz
collections/
```

### Phase 6: Galaxy Publishing

#### Step 6.1: Build Release

```bash
# Update version in galaxy.yml
vim galaxy.yml  # Set version: 1.0.0

# Build collection tarball
ansible-galaxy collection build

# Verify tarball contents
tar -tzf ceph-cephadm-1.0.0.tar.gz | head -20
```

#### Step 6.2: Publish to Galaxy

```bash
# Publish to Ansible Galaxy
ansible-galaxy collection publish ceph-cephadm-1.0.0.tar.gz --api-key=YOUR_API_KEY
```

#### Step 6.3: Create Git Tag

```bash
git tag -a v1.0.0 -m "Release v1.0.0 - Initial collection release"
git push origin v1.0.0
```

## Rollback Plan

If issues arise, rollback is simple:

```bash
# Remove symlinks
rm library module_utils ceph_defaults

# Restore original directories
git checkout library/ module_utils/ ceph_defaults/

# Remove collection structure
rm -rf plugins/ roles/ playbooks/

# Remove galaxy.yml
rm galaxy.yml

# Restore ansible.cfg
git checkout ansible.cfg
```

## Usage Comparison

### Traditional Usage (Still Supported)

```bash
# Clone and use
git clone https://github.com/ceph/cephadm-ansible
cd cephadm-ansible
ansible-playbook -i hosts cephadm-preflight.yml

# Playbook references
- import_role:
    name: ceph_defaults

# Module usage (implicit from library/)
- cephadm_bootstrap:
    mon_ip: 192.168.1.10
```

### Collection Usage (New)

```bash
# Install from Galaxy
ansible-galaxy collection install ceph.cephadm

# Run collection playbooks
ansible-playbook ceph.cephadm.cephadm_preflight -i hosts

# Use FQCN in playbooks
- ceph.cephadm.cephadm_bootstrap:
    mon_ip: 192.168.1.10

# Use collection roles
- import_role:
    name: ceph.cephadm.ceph_defaults
```

## Benefits

### For Existing Users
- ✅ No changes required
- ✅ Same commands work
- ✅ No migration effort
- ✅ Can upgrade when ready

### For New Users
- ✅ Install via Galaxy
- ✅ Semantic versioning
- ✅ Proper namespace isolation
- ✅ Better dependency management
- ✅ Follows Ansible best practices

### For Maintainers
- ✅ Easier distribution
- ✅ Version control via Galaxy
- ✅ Better namespace management
- ✅ Compatibility with automation hub
- ✅ Professional project structure

## Timeline

1. **Week 1**: Create collection structure (Phase 1-2)
2. **Week 2**: Testing and validation (Phase 3)
3. **Week 3**: Documentation updates (Phase 4)
4. **Week 4**: CI/CD updates and Galaxy publishing (Phase 5-6)

## Success Criteria

- [ ] All existing playbooks work without modification
- [ ] All existing tests pass
- [ ] Collection builds successfully
- [ ] Collection installs from tarball
- [ ] FQCN module calls work
- [ ] Collection playbooks execute
- [ ] Documentation complete
- [ ] Published to Galaxy
- [ ] CI/CD validates both workflows

## FAQ

**Q: Do I need to change my existing playbooks?**
A: No! All existing playbooks continue to work unchanged.

**Q: Can I still clone the repo and use it directly?**
A: Yes! Traditional git clone usage is fully supported.

**Q: When should I migrate to collection usage?**
A: Migrate when it suits you. Both methods are supported indefinitely.

**Q: Will the symlinks work on Windows?**
A: Symlinks work on Windows 10+ with Developer Mode enabled. Collection usage is recommended on Windows.

**Q: What if a symlink breaks?**
A: The collection structure is self-contained, so collection users are unaffected. Traditional users can restore from git.

## Conclusion

This migration plan achieves the goal of creating a proper Ansible Collection while maintaining 100% backward compatibility. Existing users experience zero disruption, while new users benefit from modern collection features.

The use of symlinks is the key strategy that enables both workflows simultaneously.
