# Gen RBAC

Generate K8s role from a set of manifests.

# How to run?

```bash
pipenv run ./main.py --dir $DIRECTORY_WITH_MANIFESTS
```

The script will generate a role file that grants
all the permissions for any Group and Kind it finds
in the manifests.

The result role file can be then used for granting
permissions to a a service a account.

The manifests directory contains some helper
manifests for creating a namespace, service account and role binding.
