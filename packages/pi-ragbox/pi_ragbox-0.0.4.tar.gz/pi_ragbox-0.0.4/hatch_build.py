"""Custom Hatchling build hook to resolve workspace dependencies.

This hook replaces workspace member dependencies (clients, data-model, indexer,
search-service) with their transitive dependencies in the wheel metadata.
"""

import tomli
from pathlib import Path
from typing import Any, Dict, List, Set
from hatchling.metadata.plugin.interface import MetadataHookInterface


class CustomMetadataHook(MetadataHookInterface):
    """Metadata hook that resolves workspace dependencies to their transitive deps."""

    PLUGIN_NAME = "custom"

    # Workspace members to bundle
    WORKSPACE_MEMBERS = {"clients", "data-model", "indexer", "search-service"}

    def update(self, metadata: Dict[str, Any]) -> None:
        """Update metadata by replacing workspace deps with transitive deps."""
        if "dependencies" not in metadata:
            return

        original_deps = metadata["dependencies"]
        resolved_deps = self._resolve_dependencies(original_deps)
        metadata["dependencies"] = sorted(resolved_deps)

    def _resolve_dependencies(self, dependencies: List[str]) -> Set[str]:
        """Resolve workspace dependencies to their transitive dependencies.

        Args:
            dependencies: List of dependency specifications (e.g., ["clients", "httpx>=0.27.0"])

        Returns:
            Set of resolved dependency specifications with workspace deps replaced
        """
        # Collect all dependencies in a dict keyed by package name
        # This allows us to merge version constraints for duplicate packages
        dep_dict: Dict[str, List[str]] = {}

        for dep in dependencies:
            # Extract package name (everything before <, >, =, [, etc.)
            pkg_name = dep.split("[")[0].split("<")[0].split(">")[0].split("=")[0].split("!")[0].strip()

            if pkg_name in self.WORKSPACE_MEMBERS:
                # Resolve workspace member to its transitive dependencies
                transitive_deps = self._get_transitive_deps(pkg_name)
                for tdep in transitive_deps:
                    tpkg_name = tdep.split("[")[0].split("<")[0].split(">")[0].split("=")[0].split("!")[0].strip()
                    if tpkg_name not in dep_dict:
                        dep_dict[tpkg_name] = []
                    dep_dict[tpkg_name].append(tdep)
            else:
                # Keep non-workspace dependencies
                if pkg_name not in dep_dict:
                    dep_dict[pkg_name] = []
                dep_dict[pkg_name].append(dep)

        # Merge duplicate dependencies by taking the most specific version constraint
        resolved = set()
        for pkg_name, specs in dep_dict.items():
            if len(specs) == 1:
                resolved.add(specs[0])
            else:
                # Multiple specs for same package - take the most restrictive
                resolved.add(self._merge_specs(specs))

        return resolved

    def _merge_specs(self, specs: List[str]) -> str:
        """Merge multiple dependency specifications for the same package.

        For now, we just take the first specification with a version constraint,
        or the last one if none have constraints. A more sophisticated approach
        would parse and merge the version constraints properly.

        Args:
            specs: List of dependency specs for the same package

        Returns:
            Merged dependency specification
        """
        # Prefer specs with extras or version constraints
        for spec in specs:
            if "[" in spec or any(op in spec for op in ["<", ">", "=", "!", "~"]):
                return spec
        return specs[-1]

    def _get_transitive_deps(self, workspace_member: str) -> Set[str]:
        """Get all transitive dependencies for a workspace member.

        Args:
            workspace_member: Name of the workspace member package

        Returns:
            Set of all transitive dependency specifications
        """
        visited = set()
        all_deps = set()

        def collect_deps(member_name: str) -> None:
            """Recursively collect dependencies."""
            if member_name in visited:
                return
            visited.add(member_name)

            # Read the workspace member's pyproject.toml
            member_dir = self._get_member_directory(member_name)
            if not member_dir:
                return

            pyproject_path = member_dir / "pyproject.toml"
            if not pyproject_path.exists():
                return

            with open(pyproject_path, "rb") as f:
                pyproject = tomli.load(f)

            # Get direct dependencies
            deps = pyproject.get("project", {}).get("dependencies", [])

            for dep in deps:
                # Extract package name
                pkg_name = dep.split("[")[0].split("<")[0].split(">")[0].split("=")[0].split("!")[0].strip()

                if pkg_name in self.WORKSPACE_MEMBERS:
                    # Recursively resolve workspace dependencies
                    collect_deps(pkg_name)
                else:
                    # Add external dependency
                    all_deps.add(dep)

        collect_deps(workspace_member)
        return all_deps

    def _get_member_directory(self, member_name: str) -> Path | None:
        """Get the directory path for a workspace member.

        Args:
            member_name: Name of the workspace member package

        Returns:
            Path to the member directory, or None if not found
        """
        # Map package names to directory names
        name_map = {
            "clients": "clients",
            "data-model": "data-model",
            "indexer": "indexer",
            "search-service": "search-service",
        }

        dir_name = name_map.get(member_name)
        if not dir_name:
            return None

        # Get the backend directory (parent of pi-ragbox)
        backend_dir = Path(self.root).parent
        member_dir = backend_dir / dir_name

        return member_dir if member_dir.exists() else None
