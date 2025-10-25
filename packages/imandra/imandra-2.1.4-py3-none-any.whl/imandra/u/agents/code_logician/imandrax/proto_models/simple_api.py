from __future__ import annotations

from enum import Enum
from typing import Literal, Self

from devtools import pformat
from pydantic import BaseModel, Field, TypeAdapter, field_validator, model_validator

from ..decode_artifact import RegionStr, decode_artifact
from .artmsg import Art
from .error import Error
from .session import Session
from .task import Origin, Task
from .utils import Empty, StringMsg


class SessionCreateReq(BaseModel):
    api_version: str = Field(description="the API types version (mandatory)")


class LiftBool(Enum):
    Default = 0
    NestedEqualities = 1
    Equalities = 2
    All = 3


class DecomposeReq(BaseModel):
    session: Session | None = Field(default=None)
    name: str = Field(description="name of function to decompose")
    assuming: str | None = Field(
        default=None, description="name of side condition function"
    )
    basis: list[str]
    rule_specs: list[str]
    prune: bool
    ctx_simp: bool | None = Field(default=None)
    lift_bool: LiftBool | None = Field(default=None)
    str_: bool = Field(default=True, alias="str")
    timeout: int | None = Field(default=None)


class DecomposeResProto(BaseModel):
    artifact: Art | None = Field(default=None)
    err: Empty | None = Field(default=None)
    errors: list[Error] = Field(default_factory=list)
    task: Task | None = Field(default=None)

    @model_validator(mode="after")
    def one_of_res(self) -> Self:
        if (self.artifact is None) == (self.err is None):
            raise ValueError("One of artifact or err must be set")
        return self


class string_kv(BaseModel):
    k: str
    v: str


class DecomposeRes(DecomposeResProto):
    """Result of a decomposition"""

    regions_str: list[RegionStr] | None = Field(
        default=None, description="None if there's decomposition error"
    )

    @model_validator(mode="after")
    def unwrap_region_str(self) -> Self:
        if self.regions_str is not None:
            return self
        elif self.errors:
            return self
        else:
            regions_str = decode_artifact(self.artifact.data, self.artifact.kind)
            return self.model_copy(update={"regions_str": regions_str})

    def __repr__(self) -> str:
        return pformat(self)

    @property
    def iml_test_cases(self) -> list[dict[str, str]]:
        """
        [
            {"args": {"x": "1", "y": "2"}, "expected_output": "3"},
            {"args": {"x": "3", "y": "4"}, "expected_output": "7"},
        ]
        """
        if not self.regions_str:
            return []
        test_cases = []
        for region_str in self.regions_str:
            if (model_eval_str := region_str.model_eval_str) is None:
                continue
            test_cases.append(
                {"args": region_str.model_str, "expected_output": model_eval_str}
            )
        return test_cases

    @property
    def test_docstrs(self) -> list[str]:
        docstrs = []
        if not self.regions_str:
            return docstrs
        for region_str in self.regions_str:
            s = ""
            if region_str.constraints_str:
                s += "Constraints:\n"
                for c in region_str.constraints_str:
                    s += f"    - `{c}`\n"
            if region_str.invariant_str:
                s += "Invariant:\n"
                s += f"    - `{region_str.invariant_str}`\n"
            docstrs.append(s)
        return docstrs


class EvalSrcReq(BaseModel):
    session: Session | None = Field(default=None)
    src: str = Field(description="source code to evaluate")
    async_only: bool | None = Field(
        default=None,
        description="if true, do not wait for tasks results, only return the task list "
        "and not the task results. Use `get_artifact` to get the results.",
    )


class EvalOutput(BaseModel):
    """Output of an `eval` statement"""

    success: bool
    value_as_ocaml: str | None = Field(
        default=None, description="result as a OCaml value, if any"
    )
    errors: list[Error] = Field(default_factory=list)


class EvalRes(BaseModel):
    success: bool = Field()
    messages: list[str] = Field(default_factory=list, description='"normal" messages')
    errors: list[Error] = Field(default_factory=list, description="akin to stderr")

    tasks: list[Task] = Field(
        default_factory=list, description="all tasks started during eval"
    )
    po_results: list[PO_Res] = Field(default_factory=list)
    eval_results: list[EvalOutput] = Field(default_factory=list)
    decomp_results: list[DecomposeRes] = Field(default_factory=list)

    def __repr__(self) -> str:
        return pformat(self, indent=2)

    @property
    def po_errors(self) -> list[Error]:
        return [err for po_res in self.po_results for err in po_res.errors]

    @property
    def has_errors(self) -> bool:
        return (len(self.errors) > 0) or (len(self.po_errors) > 0)


class VerifySrcReq(BaseModel):
    session: Session | None = Field(default=None)
    src: str = Field(description="source code")
    hints: str | None = Field(default=None)


class VerifyNameReq(BaseModel):
    session: Session | None = Field(default=None)
    name: str = Field(description="name of the predicate to verify")
    hints: str | None = Field(default=None)


class InstanceSrcReq(BaseModel):
    session: Session | None = Field(default=None)
    src: str = Field(description="source code")
    hints: str | None = Field(default=None)


class InstanceNameReq(BaseModel):
    session: Session | None = Field(default=None)
    name: str = Field(description="name of the predicate to verify")
    hints: str | None = Field(default=None)


class Proved(BaseModel):
    proof_pp: str | None = Field(default=None)


class Verified_upto(BaseModel):
    msg: str | None = Field(default=None)


class Unsat(BaseModel):
    proof_pp: str | None = Field(default=None)


class ModelType(Enum):
    Counter_example = "Counter_example"
    Instance = "Instance"


class Model(BaseModel):
    m_type: ModelType
    src: str = Field(description="iml source code for the model")
    artifact: Art | None = Field(default=None, description="the model as an artifact")


class Refuted(BaseModel):
    model: Model | None = Field(default=None)


class Sat(BaseModel):
    model: Model | None = Field(default=None)


class CounterSat(BaseModel):
    model: Model | None = Field(default=None)


class PO_Res(BaseModel):
    unknown: StringMsg | None = Field(default=None)
    err: Empty | None = Field(default=None)
    proof: Proved | None = Field(default=None)
    instance: CounterSat | None = Field(default=None)
    verified_upto: Verified_upto | None = Field(default=None)

    errors: list[Error] = Field(default_factory=list)
    task: Task | None = Field(default=None, description="the ID of the task")
    origin: Origin | None = Field(
        default=None, description="where did the task originate?"
    )

    @model_validator(mode="after")
    def one_of_res(self) -> Self:
        sum_of_res = sum(
            1
            for r in [
                self.unknown,
                self.err,
                self.proof,
                self.instance,
                self.verified_upto,
            ]
            if r is not None
        )
        if sum_of_res != 1:
            raise ValueError(
                "Exactly one of unknown, err, proof, instance, verified_upto must be "
                "set"
            )
        return self


class VerifyRes(BaseModel):
    unknown: StringMsg | None = Field(default=None)
    err: Empty | None = Field(default=None)
    proved: Proved | None = Field(default=None)
    refuted: Refuted | None = Field(default=None)
    verified_upto: Verified_upto | None = Field(default=None)

    errors: list[Error] = Field(default_factory=list)
    task: Task | None = Field(default=None, description="the ID of the task")

    @property
    def res_type(
        self,
    ) -> Literal["unknown", "err", "proved", "refuted", "verified_upto"]:
        if self.unknown is not None:
            return "unknown"
        elif self.err is not None:
            return "err"
        elif self.proved is not None:
            return "proved"
        elif self.refuted is not None:
            return "refuted"
        elif self.verified_upto is not None:
            return "verified_upto"
        else:
            raise AssertionError("Never")

    @property
    def res(self) -> StringMsg | Empty | Proved | Refuted | Verified_upto:
        if self.unknown is not None:
            return self.unknown
        elif self.err is not None:
            return self.err
        elif self.proved is not None:
            return self.proved
        elif self.refuted is not None:
            return self.refuted
        elif self.verified_upto is not None:
            return self.verified_upto
        else:
            raise AssertionError("Never")

    @model_validator(mode="after")
    def one_of_res(self) -> Self:
        sum_of_res = sum(
            1
            for r in [
                self.unknown,
                self.err,
                self.proved,
                self.refuted,
                self.verified_upto,
            ]
            if r is not None
        )
        if sum_of_res != 1:
            raise ValueError(
                "Exactly one of unknown, err, proved, refuted, verified_upto must be "
                "set"
            )
        return self


class InstanceRes(BaseModel):
    unknown: StringMsg | None = Field(default=None)
    err: Empty | None = Field(default=None)
    unsat: Unsat | None = Field(default=None)
    sat: Sat | None = Field(default=None)

    errors: list[Error] = Field(default_factory=list)
    task: Task | None = Field(default=None, description="the ID of the task")

    @model_validator(mode="after")
    def one_of_res(self) -> Self:
        sum_of_res = sum(
            1 for r in [self.unknown, self.err, self.unsat, self.sat] if r is not None
        )
        if sum_of_res != 1:
            raise ValueError("Exactly one of unknown, err, unsat, sat must be set")
        return self


class TypecheckReq(BaseModel):
    session: Session | None = Field(default=None)
    src: str = Field(description="source code to evaluate")


class TypecheckResProto(BaseModel):
    success: bool
    types: str = Field(description="JSON string of inferred types")
    errors: list[Error] = Field(default_factory=list)


class InferredType(BaseModel):
    name: str
    ty: str = Field(description="inferred type")
    line: int = Field(description="line number")
    column: int = Field(description="column number")


InferredTypes = TypeAdapter(list[InferredType])


class TypecheckRes(TypecheckResProto):
    types: list[InferredType] = Field(description="Parsed inferred types")

    @field_validator("types", mode="before")
    @classmethod
    def validate_types(cls, v: str | list[InferredType]) -> list[InferredType]:
        if isinstance(v, str):
            types_list = InferredTypes.validate_json(v)
            return types_list
        return v


class OneshotReq(BaseModel):
    input: str = Field(description="some iml code")
    timeout: float | None = Field(default=None)


class OneshotRes(BaseModel):
    class Stats(BaseModel):
        time: float

    results: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    stats: Stats | None = Field(default=None)
    detailed_results: list[str] = Field(default_factory=list)
