"""Self-contained Runtime 5.3 model artifact verification."""

from __future__ import annotations

from dataclasses import dataclass
import ast
import json
from pathlib import Path
from typing import Any

from moth_runtime_v5_3.legacy.canonical import canonical_bytes, digest, sha256_bytes
from moth_runtime_v5_3.legacy.model import IntegrityError

from .assets import RuntimeFoundation, load_foundation
from .compile.skills import load_field_object, load_skill_object
from .energy.loader import EnergyFoundation, load_energy_foundation
from .energy.schema import Runtime53Failure
from .persistence.objects import ObjectStore, TensorEnvelope


ARTIFACT_SCHEMA = "moth-model-artifact/5.3"
ARTIFACT_FILENAME = "model-artifact.json"


def _read_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntegrityError(
            f"invalid Runtime 5.3 artifact JSON: {path.name}"
        ) from exc
    if not isinstance(value, dict):
        raise IntegrityError(
            f"Runtime 5.3 artifact JSON is not an object: {path.name}"
        )
    return value, raw


def _member(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise IntegrityError(
            "Runtime 5.3 artifact member path escapes its root"
        ) from exc
    if not path.is_file():
        raise IntegrityError(
            f"Runtime 5.3 artifact member is missing: {relative}"
        )
    return path


@dataclass(frozen=True)
class ModelArtifact53:
    root: Path
    manifest: dict[str, Any]
    artifact_id: str
    artifact_hash: str
    kernel_foundation: RuntimeFoundation
    energy_envelope: TensorEnvelope
    energy_foundation: EnergyFoundation
    fields: dict[str, dict[str, Any]]
    skills: dict[str, dict[str, Any]]

    @classmethod
    def open(cls, artifact_path: str | Path) -> "ModelArtifact53":
        root = Path(artifact_path).resolve()
        manifest, _ = _read_json(_member(root, ARTIFACT_FILENAME))
        required = {
            "schema",
            "model_id",
            "runtime",
            "kernel_foundation",
            "energy_foundation",
            "fields",
            "skills",
            "members",
            "artifact_hash",
        }
        if set(manifest) != required or manifest.get("schema") != ARTIFACT_SCHEMA:
            raise IntegrityError(
                "Runtime 5.3 model artifact schema is invalid"
            )
        runtime = manifest["runtime"]
        if not isinstance(runtime, dict) or set(runtime) != {
            "compatibility",
            "kernel_compatibility",
            "entrypoint",
            "packages",
            "package_manifest",
        }:
            raise IntegrityError(
                "Runtime 5.3 package descriptor is invalid"
            )
        if (
            runtime["compatibility"] != "5.3"
            or runtime["kernel_compatibility"] != "5.3"
            or runtime["packages"] != ["moth_runtime_v5_3"]
        ):
            raise IntegrityError(
                "Runtime 5.3 package compatibility changed"
            )

        members = manifest["members"]
        if not isinstance(members, dict) or not members:
            raise IntegrityError(
                "Runtime 5.3 artifact member manifest is empty"
            )
        actual = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and path.name != ARTIFACT_FILENAME
        }
        if actual != set(members):
            raise IntegrityError(
                "Runtime 5.3 artifact has missing or undeclared members"
            )
        for relative, expected_hash in members.items():
            if sha256_bytes(_member(root, str(relative)).read_bytes()) != expected_hash:
                raise IntegrityError(
                    f"Runtime 5.3 artifact member hash mismatch: {relative}"
                )

        package_manifest, _ = _read_json(
            _member(root, str(runtime["package_manifest"]))
        )
        if (
            package_manifest.get("schema") != "moth-runtime-package/5.3"
            or package_manifest.get("runtime") != "5.3"
            or package_manifest.get("entrypoint") != runtime["entrypoint"]
            or package_manifest.get("packages") != runtime["packages"]
            or not isinstance(package_manifest.get("files"), dict)
        ):
            raise IntegrityError(
                "Runtime 5.3 embedded package manifest is invalid"
            )
        expected_files = {
            path.relative_to(root / "runtime").as_posix()
            for path in (root / "runtime").rglob("*.py")
            if path.is_file()
        }
        if set(package_manifest["files"]) != expected_files:
            raise IntegrityError(
                "Runtime 5.3 embedded package closure changed"
            )
        for relative, expected_hash in package_manifest["files"].items():
            source = _member(root / "runtime", str(relative))
            if sha256_bytes(source.read_bytes()) != expected_hash:
                raise IntegrityError(
                    "Runtime 5.3 embedded source hash changed"
                )
            try:
                tree = ast.parse(
                    source.read_text(encoding="utf-8"), filename=str(source)
                )
            except (OSError, UnicodeDecodeError, SyntaxError) as exc:
                raise IntegrityError(
                    "Runtime 5.3 embedded source is invalid"
                ) from exc
            for node in ast.walk(tree):
                modules: list[str] = []
                if isinstance(node, ast.ImportFrom) and node.module:
                    modules.append(node.module)
                elif isinstance(node, ast.Import):
                    modules.extend(alias.name for alias in node.names)
                if any(
                    (module.startswith("moth_runtime") and not (module == "moth_runtime_v5_3" or module.startswith("moth_runtime_v5_3.")))
                    or module.startswith("experiments")
                    for module in modules
                ):
                    raise IntegrityError(
                        "Runtime 5.3 package is not independent"
                    )

        kernel_descriptor = manifest["kernel_foundation"]
        if not isinstance(kernel_descriptor, dict) or set(
            kernel_descriptor
        ) != {
            "path",
            "manifest_hash",
            "foundation_id",
            "foundation_hash",
        }:
            raise IntegrityError(
                "Runtime 5.3 kernel foundation descriptor is invalid"
            )
        kernel_root = (root / str(kernel_descriptor["path"])).resolve()
        try:
            kernel_root.relative_to(root)
        except ValueError as exc:
            raise IntegrityError(
                "Runtime 5.3 kernel foundation escapes artifact"
            ) from exc
        kernel = load_foundation(kernel_root)
        if (
            kernel.manifest_hash != kernel_descriptor["manifest_hash"]
            or kernel.foundation_id != kernel_descriptor["foundation_id"]
            or kernel.foundation_hash != kernel_descriptor["foundation_hash"]
        ):
            raise IntegrityError(
                "Runtime 5.3 kernel foundation binding changed"
            )

        energy_descriptor = manifest["energy_foundation"]
        if not isinstance(energy_descriptor, dict) or set(
            energy_descriptor
        ) != {"path", "file_hash", "logical_hash"}:
            raise IntegrityError(
                "Runtime 5.3 energy foundation descriptor is invalid"
            )
        relative = str(energy_descriptor["path"])
        path = _member(root, relative)
        expected_object_path = (
            root
            / "objects"
            / "sha256"
            / str(energy_descriptor["file_hash"])[:2]
            / f"{energy_descriptor['file_hash']}.safetensors"
        ).resolve()
        if path != expected_object_path:
            raise IntegrityError(
                "Runtime 5.3 energy object is not content-addressed"
            )
        envelope = ObjectStore(root).open(
            str(energy_descriptor["file_hash"])
        )
        energy = load_energy_foundation(envelope)
        if energy.logical_hash != energy_descriptor["logical_hash"]:
            raise IntegrityError(
                "Runtime 5.3 energy foundation logical hash changed"
            )

        fields: dict[str, dict[str, Any]] = {}
        for descriptor in manifest["fields"]:
            if not isinstance(descriptor, dict) or set(descriptor) != {
                "field_id",
                "kind",
                "field_hash",
                "object_hash",
                "logical_hash",
            }:
                raise IntegrityError(
                    "Runtime 5.3 field descriptor is invalid"
                )
            if descriptor["field_id"] in fields:
                raise IntegrityError(
                    "Runtime 5.3 field identity is duplicated"
                )
            field_envelope = ObjectStore(root).open(descriptor["object_hash"])
            if field_envelope.logical_hash != descriptor["logical_hash"]:
                raise IntegrityError(
                    "Runtime 5.3 compiled field binding changed"
                )
            field_object = load_field_object(field_envelope)
            if (
                field_object.field_id != descriptor["field_id"]
                or field_object.kind != descriptor["kind"]
                or field_object.field_hash != descriptor["field_hash"]
            ):
                raise IntegrityError(
                    "Runtime 5.3 compiled field descriptor changed"
                )
            fields[str(descriptor["field_id"])] = dict(descriptor)

        skills: dict[str, dict[str, Any]] = {}
        for descriptor in manifest["skills"]:
            if not isinstance(descriptor, dict) or set(descriptor) != {
                "compilation_id",
                "field_id",
                "profile_id",
                "policy_hash",
                "object_hash",
                "logical_hash",
            }:
                raise IntegrityError(
                    "Runtime 5.3 skill descriptor is invalid"
                )
            if (
                descriptor["field_id"] not in fields
                or descriptor["compilation_id"] in skills
            ):
                raise IntegrityError(
                    "Runtime 5.3 compiled skill binding is invalid"
                )
            skill_envelope = ObjectStore(root).open(
                descriptor["object_hash"]
            )
            if skill_envelope.logical_hash != descriptor["logical_hash"]:
                raise IntegrityError(
                    "Runtime 5.3 compiled skill logical hash changed"
                )
            skill_object = load_skill_object(skill_envelope)
            if (
                skill_object.compilation_id != descriptor["compilation_id"]
                or skill_object.field_id != descriptor["field_id"]
                or skill_object.profile_id != descriptor["profile_id"]
                or skill_object.policy_hash != descriptor["policy_hash"]
            ):
                raise IntegrityError(
                    "Runtime 5.3 compiled skill descriptor changed"
                )
            skills[str(descriptor["compilation_id"])] = dict(descriptor)

        body = {
            key: value for key, value in manifest.items()
            if key != "artifact_hash"
        }
        artifact_hash = digest("moth-model-artifact/5.3", body)
        if artifact_hash != manifest["artifact_hash"]:
            raise IntegrityError(
                "Runtime 5.3 artifact aggregate hash changed"
            )
        return cls(
            root,
            manifest,
            str(manifest["model_id"]),
            artifact_hash,
            kernel,
            envelope,
            energy,
            fields,
            skills,
        )

    def verify(self) -> dict[str, Any]:
        rebuilt = type(self).open(self.root)
        if rebuilt.artifact_hash != self.artifact_hash:
            raise IntegrityError(
                "Runtime 5.3 artifact verification changed identity"
            )
        return {
            "schema": "moth-model-artifact-verification/5.3",
            "model_id": self.artifact_id,
            "artifact_hash": self.artifact_hash,
            "kernel_foundation_id": self.kernel_foundation.foundation_id,
            "kernel_foundation_hash": self.kernel_foundation.foundation_hash,
            "energy_foundation_logical_hash": self.energy_foundation.logical_hash,
            "energy_foundation_file_hash": self.energy_foundation.file_hash,
            "candidate_count": self.energy_foundation.candidate_count,
            "field_count": len(self.fields),
            "skill_count": len(self.skills),
            "verified": True,
        }

    def receipt(self) -> dict[str, Any]:
        return self.verify()
