"""Self-contained, weight-free Moth Model 5.1 artifact boundary."""

from __future__ import annotations

from dataclasses import dataclass
import ast
import json
from pathlib import Path
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes, digest, sha256_bytes
from moth_runtime_v5_0.model import IntegrityError

from .assets import RuntimeFoundation, load_foundation
from .compiled_fields import CompiledField, load_field_archive, verify_skill_compilation


ARTIFACT_SCHEMA = "moth-model-artifact/5.1"
CAPABILITY_SCHEMA = "moth-capability-index/5.1"
ARTIFACT_FILENAME = "model-artifact.json"


def _read_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntegrityError(f"invalid model artifact JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise IntegrityError(f"model artifact JSON is not an object: {path.name}")
    return value, raw


def _member(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise IntegrityError("model artifact member path escapes its root") from exc
    if not path.is_file():
        raise IntegrityError(f"model artifact member is missing: {relative}")
    return path


@dataclass(frozen=True)
class ModelArtifact51:
    root: Path
    manifest: dict[str, Any]
    artifact_id: str
    artifact_hash: str
    foundation: RuntimeFoundation
    fields: dict[str, CompiledField]
    skills: dict[str, dict[str, Any]]
    capability_index: dict[str, Any]

    @classmethod
    def open(cls, artifact_path: str | Path) -> "ModelArtifact51":
        root = Path(artifact_path).resolve()
        manifest, _ = _read_json(_member(root, ARTIFACT_FILENAME))
        required = {
            "schema", "model_id", "runtime", "foundation", "fields", "skills",
            "capability_index", "members", "artifact_hash",
        }
        if set(manifest) != required or manifest.get("schema") != ARTIFACT_SCHEMA:
            raise IntegrityError("model artifact manifest schema is invalid")
        runtime = manifest["runtime"]
        if not isinstance(runtime, dict) or set(runtime) != {
            "compatibility", "entrypoint", "packages", "package_manifest",
        } or runtime.get("compatibility") != "5.1":
            raise IntegrityError("model artifact Runtime compatibility is invalid")

        members = manifest["members"]
        if not isinstance(members, dict) or not members:
            raise IntegrityError("model artifact member manifest is empty")
        if any("weight" in str(relative).casefold() for relative in members):
            raise IntegrityError("model artifact must not declare weight members")
        actual = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and path.name != ARTIFACT_FILENAME
        }
        if actual != set(members):
            raise IntegrityError("model artifact contains missing or undeclared members")
        for relative, expected_hash in members.items():
            raw = _member(root, str(relative)).read_bytes()
            if sha256_bytes(raw) != expected_hash:
                raise IntegrityError(f"model artifact member hash mismatch: {relative}")

        package_manifest, _ = _read_json(_member(root, str(runtime["package_manifest"])))
        if set(package_manifest) != {"schema", "runtime", "entrypoint", "packages", "files"} or (
            package_manifest.get("schema") != "moth-runtime-package/5.1"
            or package_manifest.get("runtime") != "5.1"
            or package_manifest.get("entrypoint") != runtime["entrypoint"]
            or package_manifest.get("packages") != runtime["packages"]
            or not isinstance(package_manifest.get("files"), dict)
        ):
            raise IntegrityError("embedded Runtime package manifest is invalid")
        expected_package_files = {
            path.relative_to(root / "runtime").as_posix()
            for path in (root / "runtime").rglob("*.py") if path.is_file()
        }
        if set(package_manifest["files"]) != expected_package_files:
            raise IntegrityError("embedded Runtime package closure changed")
        for relative, expected_hash in package_manifest["files"].items():
            source_path = _member(root / "runtime", str(relative))
            if sha256_bytes(source_path.read_bytes()) != expected_hash:
                raise IntegrityError("embedded Runtime source hash changed")
            try:
                tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
            except (OSError, UnicodeDecodeError, SyntaxError) as exc:
                raise IntegrityError("embedded Runtime source is invalid") from exc
            for node in ast.walk(tree):
                module = node.module if isinstance(node, ast.ImportFrom) else None
                names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else []
                if (module and module.startswith("experiments")) or any(
                    name.startswith("experiments") for name in names
                ):
                    raise IntegrityError("embedded Runtime imports an experiment package")

        foundation_descriptor = manifest["foundation"]
        if not isinstance(foundation_descriptor, dict) or set(foundation_descriptor) != {
            "path", "manifest_hash", "foundation_id", "foundation_hash",
        }:
            raise IntegrityError("model artifact foundation descriptor is invalid")
        foundation_root = (root / str(foundation_descriptor["path"])).resolve()
        try:
            foundation_root.relative_to(root)
        except ValueError as exc:
            raise IntegrityError("model artifact foundation path escapes its root") from exc
        foundation = load_foundation(foundation_root)
        if (
            foundation.manifest_hash != foundation_descriptor["manifest_hash"]
            or foundation.foundation_id != foundation_descriptor["foundation_id"]
            or foundation.foundation_hash != foundation_descriptor["foundation_hash"]
        ):
            raise IntegrityError("model artifact foundation binding changed")

        fields: dict[str, CompiledField] = {}
        descriptors = manifest["fields"]
        if not isinstance(descriptors, list) or not descriptors:
            raise IntegrityError("model artifact has no compiled fields")
        for descriptor in descriptors:
            if not isinstance(descriptor, dict) or set(descriptor) != {
                "field_id", "kind", "path", "sha256", "field_hash",
            }:
                raise IntegrityError("model artifact field descriptor is invalid")
            path = _member(root, str(descriptor["path"]))
            value, raw = _read_json(path)
            field = load_field_archive(value)
            if (
                sha256_bytes(raw) != descriptor["sha256"]
                or field.field_id != descriptor["field_id"]
                or field.kind.value != descriptor["kind"]
                or field.field_hash != descriptor["field_hash"]
                or field.field_id in fields
            ):
                raise IntegrityError("model artifact field binding is invalid")
            fields[field.field_id] = field

        skills: dict[str, dict[str, Any]] = {}
        skill_descriptors = manifest["skills"]
        if not isinstance(skill_descriptors, list) or not skill_descriptors:
            raise IntegrityError("model artifact has no compiled skills")
        for descriptor in skill_descriptors:
            if not isinstance(descriptor, dict) or set(descriptor) != {
                "compilation_id", "field_id", "profile_id", "policy_hash", "path", "sha256",
            }:
                raise IntegrityError("model artifact skill descriptor is invalid")
            value, raw = _read_json(_member(root, str(descriptor["path"])))
            field = fields.get(str(descriptor["field_id"]))
            if field is None:
                raise IntegrityError("model artifact skill references an unknown field")
            verify_skill_compilation(value, field)
            compilation_id = str(value["compilation_id"])
            if (
                sha256_bytes(raw) != descriptor["sha256"]
                or compilation_id != descriptor["compilation_id"]
                or value["profile_id"] != descriptor["profile_id"]
                or value["policy_hash"] != descriptor["policy_hash"]
                or compilation_id in skills
            ):
                raise IntegrityError("model artifact skill binding is invalid")
            skills[compilation_id] = value

        capability_descriptor = manifest["capability_index"]
        if not isinstance(capability_descriptor, dict) or set(capability_descriptor) != {
            "path", "sha256",
        }:
            raise IntegrityError("model artifact capability descriptor is invalid")
        capability_index, raw = _read_json(_member(root, str(capability_descriptor["path"])))
        if sha256_bytes(raw) != capability_descriptor["sha256"]:
            raise IntegrityError("model artifact capability index hash changed")
        if set(capability_index) != {"schema", "surface_modes"} or capability_index.get("schema") != CAPABILITY_SCHEMA:
            raise IntegrityError("model artifact capability index schema is invalid")
        modes = capability_index["surface_modes"]
        if not isinstance(modes, list) or not modes:
            raise IntegrityError("model artifact Surface capability index is empty")
        mode_ids: set[str] = set()
        for mode in modes:
            if not isinstance(mode, dict) or set(mode) != {
                "mode", "field_id", "compilation_id", "requests", "semantic_kinds",
                "grounding_cost_units",
            }:
                raise IntegrityError("model artifact Surface capability is invalid")
            if (
                not isinstance(mode["mode"], str) or mode["mode"] in mode_ids
                or mode["field_id"] not in fields or mode["compilation_id"] not in skills
                or skills[mode["compilation_id"]]["field_id"] != mode["field_id"]
                or not isinstance(mode["requests"], list) or not mode["requests"]
                or not isinstance(mode["semantic_kinds"], list) or not mode["semantic_kinds"]
                or not isinstance(mode["grounding_cost_units"], int)
                or mode["grounding_cost_units"] < 0
            ):
                raise IntegrityError("model artifact Surface capability binding is invalid")
            mode_ids.add(mode["mode"])

        body = {key: value for key, value in manifest.items() if key != "artifact_hash"}
        artifact_hash = digest("moth-model-artifact/5.1", body)
        if manifest["artifact_hash"] != artifact_hash:
            raise IntegrityError("model artifact aggregate hash changed")
        artifact_id = str(manifest["model_id"])
        return cls(
            root, manifest, artifact_id, artifact_hash, foundation,
            fields, skills, capability_index,
        )

    def verify(self) -> dict[str, Any]:
        # Re-open independently so every receipt is reconstructed from disk.
        rebuilt = type(self).open(self.root)
        if rebuilt.artifact_hash != self.artifact_hash:
            raise IntegrityError("model artifact verification changed its identity")
        return {
            "schema": "moth-model-artifact-verification/5.1",
            "model_id": self.artifact_id,
            "artifact_hash": self.artifact_hash,
            "foundation_id": self.foundation.foundation_id,
            "foundation_hash": self.foundation.foundation_hash,
            "field_count": len(self.fields), "skill_count": len(self.skills),
            "surface_mode_count": len(self.capability_index["surface_modes"]),
            "weights_present": False, "verified": True,
        }

    def receipt(self) -> dict[str, Any]:
        return self.verify()
