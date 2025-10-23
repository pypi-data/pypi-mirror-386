"""Git-native handler for ignore functionality using hybrid stash approach."""

from pathlib import Path
from typing import List, Optional

from git_autosquash.hunk_target_resolver import HunkTargetMapping
from git_autosquash.git_ops import GitOps
from git_autosquash.strategy_base import CliStrategy


class GitNativeIgnoreHandler(CliStrategy):
    """Enhanced ignore handler using git native operations for backup/restore.

    This implementation combines the reliability of git's native stash operations
    for backup and restore with precise patch application for hunk-level control.
    """

    def __init__(self, git_ops: GitOps) -> None:
        """Initialize the git-native handler.

        Args:
            git_ops: GitOps instance for git command execution
        """
        super().__init__(git_ops)

    @property
    def strategy_name(self) -> str:
        """Get the name of this strategy for logging and identification."""
        return "index"

    @property
    def requires_worktree_support(self) -> bool:
        """Whether this strategy requires git worktree support."""
        return False

    def is_available(self) -> bool:
        """Check if this strategy is available in the current environment.

        Returns:
            True if strategy can be used
        """
        try:
            # Check if git stash is available (should be in all git versions)
            result = self.git_ops.run_git_command(["stash", "--help"])
            return result.returncode == 0
        except Exception:
            return False

    def apply_ignored_hunks(self, ignored_mappings: List[HunkTargetMapping]) -> bool:
        """Apply ignored hunks with native git backup/restore.

        Uses a hybrid approach:
        1. Native git stash for comprehensive backup
        2. Proven patch application for precise hunk control
        3. Atomic native restore on any failure

        Args:
            ignored_mappings: List of ignored hunk to commit mappings

        Returns:
            True if successful, False if any hunks could not be applied
        """
        if not ignored_mappings:
            self.logger.info("No ignored hunks to apply")
            return True

        self.logger.info(
            f"Applying {len(ignored_mappings)} ignored hunks with git-native backup"
        )

        # Phase 1: Create comprehensive native backup
        backup_stash = self._create_comprehensive_backup()
        if not backup_stash:
            self.logger.error("Failed to create backup stash")
            return False

        try:
            # Phase 2: Validate file paths for security
            if not self._validate_file_paths(ignored_mappings):
                self.logger.error("Path validation failed")
                return False

            # Phase 3: Apply patches with existing proven logic
            success = self._apply_patches_with_validation(ignored_mappings)

            if success:
                self.logger.info(
                    "✓ Ignored hunks successfully restored to working tree"
                )
                return True
            else:
                self.logger.warning("Patch application failed, initiating restore")
                self._restore_from_stash(backup_stash)
                return False

        except Exception as e:
            # Phase 4: Atomic native restore on any failure
            self.logger.error(f"Exception during patch application: {e}")
            self._restore_from_stash(backup_stash)
            return False

        finally:
            # Phase 5: Clean up backup stash
            self._cleanup_stash(backup_stash)

    def _create_comprehensive_backup(self) -> Optional[str]:
        """Create comprehensive stash backup including untracked files.

        Returns:
            Stash reference if successful, None if failed
        """
        self.logger.debug("Creating comprehensive backup stash")

        result = self.git_ops.run_git_command(
            [
                "stash",
                "push",
                "--include-untracked",
                "--message",
                "git-autosquash-comprehensive-backup",
            ]
        )

        if result.returncode == 0:
            # Extract stash reference - typically "stash@{0}" after creation
            stash_ref = "stash@{0}"
            self.logger.debug(f"Created backup stash: {stash_ref}")
            return stash_ref
        else:
            self.logger.error(f"Failed to create backup stash: {result.stderr}")
            return None

    def _validate_file_paths(self, ignored_mappings: List[HunkTargetMapping]) -> bool:
        """Enhanced path validation to prevent security issues.

        Args:
            ignored_mappings: List of mappings to validate

        Returns:
            True if all paths are safe, False otherwise
        """
        try:
            repo_root = Path(self.git_ops.repo_path).resolve()

            for mapping in ignored_mappings:
                file_path = Path(mapping.hunk.file_path)

                # Reject absolute paths
                if file_path.is_absolute():
                    self.logger.error(
                        f"Absolute file path not allowed: {mapping.hunk.file_path}"
                    )
                    return False

                # Check for symlinks in path components (security)
                current_path = repo_root
                for part in file_path.parts:
                    current_path = current_path / part
                    if current_path.is_symlink():
                        self.logger.error(
                            f"Symlinks not allowed in file paths: {mapping.hunk.file_path}"
                        )
                        return False

                # Check for path traversal by resolving against repo root
                resolved_path = (repo_root / file_path).resolve()
                try:
                    resolved_path.relative_to(repo_root)
                except ValueError:
                    self.logger.error(
                        f"Path traversal detected: {mapping.hunk.file_path}"
                    )
                    return False

            self.logger.debug("All file paths validated successfully")
            return True

        except Exception as e:
            self.logger.error(f"Path validation failed: {e}")
            return False

    def _apply_patches_with_validation(
        self, ignored_mappings: List[HunkTargetMapping]
    ) -> bool:
        """Apply patches using git index manipulation for precise control.

        This enhanced approach uses git's native index operations:
        1. Stage specific hunks to the index
        2. Generate patch using git diff --cached
        3. Reset index and apply patch to working tree
        4. Provides better validation and error handling

        Args:
            ignored_mappings: List of mappings to apply

        Returns:
            True if all patches applied successfully, False otherwise
        """
        return self._apply_patches_via_index(ignored_mappings)

    def _apply_patches_via_index(
        self, ignored_mappings: List[HunkTargetMapping]
    ) -> bool:
        """Apply patches using git index manipulation for precise control.

        This method leverages git's native index operations:
        1. Create temporary patches for each hunk
        2. Stage hunks individually to the index
        3. Generate final patch using git diff --cached
        4. Reset index and apply to working tree

        Args:
            ignored_mappings: List of mappings to apply

        Returns:
            True if all patches applied successfully, False otherwise
        """
        try:
            # Store original index state
            success, original_index = self._capture_index_state()
            if not success:
                self.logger.error("Failed to capture original index state")
                return False

            try:
                # Apply each hunk to index individually for validation
                for mapping in ignored_mappings:
                    if not self._stage_hunk_to_index(mapping.hunk):
                        self.logger.error(
                            f"Failed to stage hunk for {mapping.hunk.file_path}"
                        )
                        return False

                # Generate patch from staged changes
                patch_content = self._generate_patch_from_index()
                if not patch_content:
                    self.logger.error("Failed to generate patch from staged changes")
                    return False

                # Reset index to original state
                self._restore_index_state(original_index)

                # Apply patch to working tree using git apply
                result = self.git_ops.run_git_command_with_input(
                    ["apply", "--check"], patch_content
                )

                if result.returncode != 0:
                    self.logger.error(f"Patch validation failed: {result.stderr}")
                    return False

                result = self.git_ops.run_git_command_with_input(
                    ["apply"], patch_content
                )

                if result.returncode == 0:
                    self.logger.debug("Git-native patch application successful")
                    return True
                else:
                    self.logger.error(
                        f"Git-native patch application failed: {result.stderr}"
                    )
                    return False

            except Exception as e:
                self.logger.error(f"Error during index-based patch application: {e}")
                # Ensure index is restored on any error
                self._restore_index_state(original_index)
                return False

        except Exception as e:
            self.logger.error(f"Failed to apply patches via index: {e}")
            return False

    def _capture_index_state(self) -> tuple[bool, str]:
        """Capture the current git index state for restoration.

        Returns:
            Tuple of (success, index_hash) where index_hash can be used to restore
        """
        try:
            # Get current index tree hash
            result = self.git_ops.run_git_command(["write-tree"])
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                self.logger.error("Failed to capture index tree state")
                return False, ""
        except Exception as e:
            self.logger.error(f"Error capturing index state: {e}")
            return False, ""

    def _restore_index_state(self, tree_hash: str) -> bool:
        """Restore git index to a previous state.

        Args:
            tree_hash: Tree hash to restore index to

        Returns:
            True if restoration successful
        """
        try:
            if not tree_hash:
                return False

            result = self.git_ops.run_git_command(["read-tree", tree_hash])
            if result.returncode == 0:
                self.logger.debug(f"Index restored to tree {tree_hash[:8]}")
                return True
            else:
                self.logger.error(f"Failed to restore index to tree {tree_hash}")
                return False
        except Exception as e:
            self.logger.error(f"Error restoring index state: {e}")
            return False

    def _stage_hunk_to_index(self, hunk) -> bool:
        """Stage a specific hunk to the git index using patch application.

        Args:
            hunk: DiffHunk object to stage

        Returns:
            True if hunk was staged successfully
        """
        try:
            # Create a minimal patch for this single hunk
            hunk_patch = self._create_minimal_patch_for_hunk(hunk)
            if not hunk_patch:
                return False

            # Apply patch to index only (--cached)
            result = self.git_ops.run_git_command_with_input(
                ["apply", "--cached"], hunk_patch
            )

            if result.returncode == 0:
                self.logger.debug(f"Staged hunk for {hunk.file_path} to index")
                return True
            else:
                self.logger.warning(
                    f"Failed to stage hunk for {hunk.file_path}: {result.stderr}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Error staging hunk to index: {e}")
            return False

    def _create_minimal_patch_for_hunk(self, hunk) -> Optional[str]:
        """Create a minimal git patch for a single hunk.

        Args:
            hunk: DiffHunk object to create patch for

        Returns:
            Patch content string, or None if creation failed
        """
        try:
            # Get blob info for proper headers
            blob_info = self._get_file_blob_info(hunk.file_path)

            # Build minimal patch
            patch_lines = [
                f"diff --git a/{hunk.file_path} b/{hunk.file_path}",
                f"index {blob_info['old_hash']}..{blob_info['new_hash']} {blob_info['mode']}",
                f"--- a/{hunk.file_path}",
                f"+++ b/{hunk.file_path}",
            ]

            # Add hunk content
            patch_lines.extend(hunk.lines)

            return "\n".join(patch_lines) + "\n"

        except Exception as e:
            self.logger.error(f"Failed to create minimal patch for hunk: {e}")
            return None

    def _generate_patch_from_index(self) -> Optional[str]:
        """Generate a patch from currently staged changes using git diff --cached.

        Returns:
            Patch content, or None if generation failed
        """
        try:
            result = self.git_ops.run_git_command(["diff", "--cached"])

            if result.returncode == 0 and result.stdout.strip():
                self.logger.debug(
                    f"Generated patch from index ({len(result.stdout)} bytes)"
                )
                return result.stdout
            else:
                self.logger.warning("No staged changes found to generate patch")
                return None

        except Exception as e:
            self.logger.error(f"Failed to generate patch from index: {e}")
            return None

    def _get_file_blob_info(self, file_path: str) -> dict:
        """Get git blob information for proper patch headers.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with old_hash, new_hash, and mode
        """
        try:
            # Get current file hash
            current_result = self.git_ops.run_git_command(["hash-object", file_path])

            # Get HEAD version hash
            head_result = self.git_ops.run_git_command(
                ["rev-parse", f"HEAD:{file_path}"]
            )

            # Get file mode
            mode_result = self.git_ops.run_git_command(
                ["ls-files", "--stage", file_path]
            )

            if current_result.returncode == 0 and mode_result.returncode == 0:
                # Extract mode from ls-files output (format: mode hash stage filename)
                mode = mode_result.stdout.split()[0] if mode_result.stdout else "100644"
                return {
                    "old_hash": head_result.stdout.strip()
                    if head_result.returncode == 0
                    else "0" * 40,
                    "new_hash": current_result.stdout.strip(),
                    "mode": mode,
                }
            else:
                # Fallback to placeholder values
                return {"old_hash": "0" * 40, "new_hash": "1" * 40, "mode": "100644"}

        except Exception as e:
            self.logger.warning(f"Could not get blob info for {file_path}: {e}")
            return {"old_hash": "0" * 40, "new_hash": "1" * 40, "mode": "100644"}

    def _restore_from_stash(self, stash_ref: str) -> bool:
        """Atomically restore working tree from stash.

        Args:
            stash_ref: Stash reference to restore from

        Returns:
            True if restore succeeded, False otherwise
        """
        self.logger.info(f"Restoring working tree from stash: {stash_ref}")

        result = self.git_ops.run_git_command(["stash", "pop", stash_ref])

        if result.returncode == 0:
            self.logger.info("✓ Working tree restored from backup")
            return True
        else:
            self.logger.error(f"Failed to restore from stash: {result.stderr}")
            # Try alternative restore method
            return self._force_restore_from_stash(stash_ref)

    def _force_restore_from_stash(self, stash_ref: str) -> bool:
        """Force restore using checkout method as fallback.

        Args:
            stash_ref: Stash reference to restore from

        Returns:
            True if force restore succeeded, False otherwise
        """
        self.logger.warning("Attempting force restore using checkout method")

        # Reset working tree to clean state first
        result = self.git_ops.run_git_command(["reset", "--hard", "HEAD"])
        if result.returncode != 0:
            self.logger.error("Failed to reset working tree")
            return False

        # Apply stash changes using checkout
        result = self.git_ops.run_git_command(["checkout", stash_ref, "--", "."])

        if result.returncode == 0:
            self.logger.info("✓ Force restore completed")
            return True
        else:
            self.logger.error(f"Force restore failed: {result.stderr}")
            return False

    def _find_stash_ref_by_sha(self, stash_sha: str) -> Optional[str]:
        """Find stash reference (stash@{n}) for a given SHA.

        Args:
            stash_sha: The SHA to find in stash list

        Returns:
            Stash reference like "stash@{0}" if found, None otherwise
        """
        # List all stashes with their SHAs
        result = self.git_ops.run_git_command(["stash", "list", "--format=%H %gd"])

        if result.returncode != 0:
            self.logger.error(f"Failed to list stashes: {result.stderr}")
            return None

        # Parse output to find matching SHA
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2:
                sha, ref = parts
                if sha == stash_sha or sha.startswith(stash_sha[:12]):
                    # Extract stash@{n} from format like "(stash@{0})"
                    if ref.startswith("(") and ref.endswith(")"):
                        ref = ref[1:-1]
                    self.logger.debug(
                        f"Found stash reference {ref} for SHA {stash_sha[:12]}"
                    )
                    return ref

        self.logger.warning(f"No stash reference found for SHA {stash_sha[:12]}")
        return None

    def _cleanup_stash(self, stash_ref: str) -> None:
        """Clean up backup stash.

        Args:
            stash_ref: Stash reference (SHA or stash@{n}) to clean up
        """
        self.logger.debug(f"Cleaning up backup stash: {stash_ref}")

        # If it looks like a SHA, find the proper stash reference
        actual_ref = stash_ref
        if len(stash_ref) >= 7 and not stash_ref.startswith("stash@"):
            found_ref = self._find_stash_ref_by_sha(stash_ref)
            if found_ref:
                actual_ref = found_ref
                self.logger.debug(f"Resolved SHA {stash_ref[:12]} to {actual_ref}")
            else:
                self.logger.warning(
                    f"Could not find stash reference for SHA {stash_ref[:12]}. "
                    "Stash may have been dropped already."
                )
                return

        result = self.git_ops.run_git_command(["stash", "drop", actual_ref])

        if result.returncode == 0:
            self.logger.debug("✓ Backup stash cleaned up")
        else:
            self.logger.warning(
                f"Failed to clean up stash {actual_ref}: {result.stderr}"
            )
            self.logger.warning(
                f"Stash may need manual cleanup with: git stash drop {actual_ref}"
            )

    def get_stash_info(self) -> List[dict]:
        """Get information about current stashes for debugging.

        Returns:
            List of dictionaries with stash information
        """
        result = self.git_ops.run_git_command(["stash", "list"])

        if result.returncode != 0:
            return []

        stashes = []
        for line in result.stdout.split("\n"):
            if line.strip():
                # Parse stash line format: stash@{0}: WIP on branch: message
                parts = line.split(": ", 2)
                if len(parts) >= 3:
                    stashes.append(
                        {"ref": parts[0], "type": parts[1], "message": parts[2]}
                    )

        return stashes
